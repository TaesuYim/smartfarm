"""
sensor_to_publish.py

ADS1115 센서 4개(0x4b, 0x49, 0x48, 0x4a), 총 16채널에서 읽고,
핀맵(docs/pin-map.md) 기준으로 필드에 매핑하여
sf/gh1/sensors/snapshot MQTT 토픽에 발행합니다.
(0x4a는 spare으로 현재 사용하지 않습니다.)

전압 → 물리량 변환, MQTT 발행 상세는
docs/sensor-hub-spec.md 를 참조하세요.

실행:
    ./rpi/.venv/bin/python rpi/sensor_hub/sensor_to_publish.py --gh gh1
    ./rpi/.venv/bin/python rpi/sensor_hub/sensor_to_publish.py --rate 0.5
    python -m rpi.sensor_hub.sensor_to_publish
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import paho.mqtt.client as mqtt

# Allow both `python -m rpi.sensor_hub.sensor_to_publish` and direct script execution.
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rpi.logger.db import DEFAULT_DB_DIR, monthly_db_path, connect_db, init_db

# 하드웨어 옵셔널 구조 (spec 섹션 3):
# 임포트 실패 시 HAS_HARDWARE = False, 모든 센서값은 None
try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_HARDWARE = True
except (ImportError, Exception):
    HAS_HARDWARE = False

# ==========================================
# 전압 → 물리량 변환 (spec 섹션 6)
# ==========================================

# 보정 상수 (offset) — 실측 보정 시 조정 (spec 섹션 6.6)
TEMP_OFFSET = 0.0
HUM_OFFSET  = 0.0
CO2_OFFSET  = 0.0


def voltage_to_temp_c(voltage):
    """spec 6.1: 0.66666667V = -20.0°C, 3.33333333V = 60°C"""
    v_adj = max(0, voltage - 0.66666667)
    temp_c = (v_adj * (80 / 2.66666667)) - 20
    return round(temp_c + TEMP_OFFSET, 2)


def voltage_to_hum_pct(voltage):
    """spec 6.2: 0.66666667V = 0%, 3.33333333V = 100% (clamp 적용)"""
    v_adj = max(0, voltage - 0.66666667)
    hum_pct = v_adj * (100 / 2.66666667)
    hum_pct = max(0, min(100, hum_pct + HUM_OFFSET))
    return round(hum_pct, 2)


def voltage_to_co2_ppm(voltage):
    """spec 6.3: 0.6V = 0ppm, 3.0V = 2000ppm"""
    v_adj = max(0, voltage - 0.6)
    co2_ppm = v_adj * (2000 / 2.4)
    return round(max(0, co2_ppm + CO2_OFFSET), 1)


def voltage_to_par_w_m2(voltage):
    """spec 6.4: 임시 구현 — 전압값 그대로 반환 (소수점 4자리)"""
    return round(voltage, 4)


def voltage_to_soil_moisture_pct(voltage):
    """spec 6.5: 임시 구현 — 전압값 그대로 반환 (소수점 4자리)"""
    return round(voltage, 4)


# ==========================================
# 타임스탬프 (spec 섹션 10)
# ==========================================

def now_kst():
    """KST(UTC+9) 기준, YYYY-MM-DDTHH:MM:SS 형식, 타임존 접미사 없음"""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S")


# ==========================================
# I2C / ADS1115 초기화 (spec 섹션 4, 5)
# ==========================================

def init_i2c():
    if not HAS_HARDWARE:
        return None
    try:
        return busio.I2C(board.SCL, board.SDA)
    except Exception:
        return None


def try_init_ads(i2c, address):
    """ADS1115 객체 생성 및 4채널 AnalogIn 생성, data_rate = 860 SPS (spec 섹션 4, 12)"""
    if not i2c:
        return None, []
    try:
        ads = ADS.ADS1115(i2c, address=address)
        ads.data_rate = 860
        channels = [AnalogIn(ads, i) for i in range(4)]
        print(f"  ADS1115 0x{address:02x} 초기화 성공 (860 SPS)")
        return ads, channels
    except Exception as e:
        print(f"  ADS1115 0x{address:02x} 초기화 실패: {e}")
        return None, []


# ==========================================
# 센서 읽기 (spec 섹션 5, 6)
# ==========================================

def safe_read(channels, idx, convert_fn):
    """채널에서 전압을 읽고 변환 함수로 물리량 변환"""
    try:
        voltage = channels[idx].voltage
        return convert_fn(voltage)
    except Exception:
        return None


def read_snapshot(ch_4b, ch_49, ch_48):
    """핀맵 기준 12채널 읽기 및 물리량 변환 (spec 섹션 5)

    0x4b A0: 온도 하부 → temp_pot_c       0x49 A0: CO2       → co2_ppm
    0x4b A1: 습도 하부 → hum_pot_pct      0x49 A1: 조도(PAR) → par_w_m2
    0x4b A2: 온도 상부 → temp_top_c       0x49 A2: 토양수분1 → soil_moisture_1_pct
    0x4b A3: 습도 상부 → hum_top_pct      0x49 A3: 토양수분2 → soil_moisture_2_pct
    0x48 A0: 토양수분3   0x48 A1: 토양수분4   0x48 A2: 토양수분5   0x48 A3: 토양수분6
    """
    return {
        "temp_pot_c":          safe_read(ch_4b, 0, voltage_to_temp_c)            if ch_4b else None,
        "hum_pot_pct":         safe_read(ch_4b, 1, voltage_to_hum_pct)           if ch_4b else None,
        "temp_top_c":          safe_read(ch_4b, 2, voltage_to_temp_c)            if ch_4b else None,
        "hum_top_pct":         safe_read(ch_4b, 3, voltage_to_hum_pct)           if ch_4b else None,
        "co2_ppm":             safe_read(ch_49, 0, voltage_to_co2_ppm)           if ch_49 else None,
        "par_w_m2":            safe_read(ch_49, 1, voltage_to_par_w_m2)          if ch_49 else None,
        "soil_moisture_1_pct": safe_read(ch_49, 2, voltage_to_soil_moisture_pct) if ch_49 else None,
        "soil_moisture_2_pct": safe_read(ch_49, 3, voltage_to_soil_moisture_pct) if ch_49 else None,
        "soil_moisture_3_pct": safe_read(ch_48, 0, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_4_pct": safe_read(ch_48, 1, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_5_pct": safe_read(ch_48, 2, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_6_pct": safe_read(ch_48, 3, voltage_to_soil_moisture_pct) if ch_48 else None,
    }


# ==========================================
# 측정 주기 관리 (spec 섹션 8)
# ==========================================

# DB 설정값 캐싱 — 5초 이내 재호출 시 캐시 반환 (spec 섹션 8.2, 12)
_cached_period = None
_last_db_check = 0


def read_measurement_period_seconds(default_period):
    """app_setting 테이블에서 measurement_interval_sec 읽기 (spec 섹션 8.2)

    - DB에 값이 있으면 해당 값 사용 (최소 0.1초)
    - DB에 값이 없거나 오류 시 default_period 사용
    - 5초 이내 재호출 시 캐시된 값 반환
    """
    global _cached_period, _last_db_check
    now = time.time()

    if _cached_period is not None and (now - _last_db_check) < 5.0:
        return _cached_period

    _last_db_check = now
    db_path = monthly_db_path(DEFAULT_DB_DIR)
    if not db_path.exists():
        _cached_period = default_period
        return default_period

    try:
        with connect_db(db_path) as conn:
            row = conn.execute(
                "SELECT value FROM app_setting WHERE key = ?",
                ("measurement_interval_sec",),
            ).fetchone()

            if row:
                _cached_period = max(0.1, float(row["value"]))
            else:
                _cached_period = default_period
    except Exception:
        _cached_period = default_period

    return _cached_period


# ==========================================
# 메인 (spec 섹션 4, 9, 11)
# ==========================================

def main():
    # 1. CLI 인자 파싱 (spec 섹션 2)
    parser = argparse.ArgumentParser(description="ADS1115 센서 snapshot을 MQTT로 발행합니다.")
    parser.add_argument("--gh", default="gh1", choices=["gh1"], help="온실 ID (현재 gh1만 지원)")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT 브로커 호스트")
    parser.add_argument("--port", default=1883, type=int, help="MQTT 브로커 포트")
    parser.add_argument("--rate", default=2.0, type=float, help="초당 발행 횟수 (기본: 2)")
    args = parser.parse_args()

    topic = f"sf/{args.gh}/sensors/snapshot"
    default_period = 1.0 / args.rate

    print("=== SmartFarm Sensor Snapshot Publisher ===")
    print(f"  온실: {args.gh}")
    print(f"  MQTT 토픽: {topic}")
    print(f"  발행 주기: {default_period:.1f}s")
    print()

    # 2. MQTT 연결 (spec 섹션 4)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.host, args.port, 60)
        client.loop_start()
        print(f"MQTT 연결 성공: {args.host}:{args.port}")
    except Exception as e:
        print(f"MQTT 연결 실패: {e}")
        return

    # 3. 데이터베이스 초기화 — 프로그램 시작 시 한 번만 (spec 섹션 4)
    try:
        db_path = monthly_db_path(DEFAULT_DB_DIR)
        with connect_db(db_path) as conn:
            init_db(conn)
        print(f"데이터베이스 초기화 완료: {db_path.name}")
    except Exception as e:
        print(f"데이터베이스 초기화 실패: {e}")

    # 4. I2C 버스 초기화 (spec 섹션 4)
    # 5. ADS1115 초기화 — 3개 주소(0x4b, 0x49, 0x48) (spec 섹션 4, 5)
    ads_4b, ch_4b = None, []
    ads_49, ch_49 = None, []
    ads_48, ch_48 = None, []

    if HAS_HARDWARE:
        print("ADS1115 초기화 중...")
        i2c = init_i2c()
        if i2c:
            ads_4b, ch_4b = try_init_ads(i2c, 0x4b)
            ads_49, ch_49 = try_init_ads(i2c, 0x49)
            ads_48, ch_48 = try_init_ads(i2c, 0x48)
    else:
        print("하드웨어를 찾을 수 없습니다. (ADS1115 라이브러리 미설치 또는 환경 차이)")
    print()

    # MQTT 발행 루프 (spec 섹션 9)
    print("발행 시작... (Ctrl+C로 종료)")
    try:
        while True:
            loop_start = time.time()
            ts = now_kst()

            sensor_values = read_snapshot(
                ch_4b if ads_4b else None,
                ch_49 if ads_49 else None,
                ch_48 if ads_48 else None,
            )

            # payload 구조 (spec 섹션 9.2)
            payload = {
                "ts": ts,
                "source": "rpi5_main",
                **sensor_values,
            }

            client.publish(topic, json.dumps(payload))
            print(f"[{ts}] 발행 → {topic}")

            # 루프 타이밍 (spec 섹션 8.3)
            elapsed = time.time() - loop_start
            period = read_measurement_period_seconds(default_period)
            time.sleep(max(0, period - elapsed))

    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        # 종료 처리 (spec 섹션 11)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
