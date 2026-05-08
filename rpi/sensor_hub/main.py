"""
test_sensor_snapshot_publish.py

ADS1115 센서 4개에서 채널을 읽고,
핀맵(docs/pin-map.md) 기준으로 필드에 매핑하여
sf/gh1/sensors/snapshot MQTT 토픽에 발행합니다.

실행:
    ./rpi/.venv/bin/python rpi/sensor_hub/main.py --gh gh1
    ./rpi/.venv/bin/python rpi/sensor_hub/main.py --rate 0.5
"""

import argparse
import json
import sys
import time
import statistics
import collections
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import paho.mqtt.client as mqtt

# Allow both `python -m rpi.sensor_hub.main` and direct script execution.
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rpi.logger.db import DEFAULT_DB_DIR, monthly_db_path, connect_db, init_db

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_HARDWARE = True
except (ImportError, Exception):
    HAS_HARDWARE = False

# ==========================================
# 전압 → 물리량 변환 및 캘리브레이션
# ==========================================

# 센서별 보정값 (실제 값과 차이가 날 경우 여기서 가감하세요)
TEMP_OFFSET = 0.0
HUM_OFFSET  = 0.0
CO2_OFFSET  = 0.0

# Keep global humidity scaling neutral. A one-point scale can make already
# correct readings drift high; use HUMIDITY_CAL_POINTS for real calibration.
HUM_SCALE = 1.0

HUM_V_MIN = 0.655
HUM_V_SPAN = 2.634
HUM_PCT_MIN = 0.0
HUM_PCT_MAX = 99.9

# Optional two-point humidity calibration, per channel.
# Leave empty to use the default datasheet-style voltage mapping above.
# Example:
# HUMIDITY_CAL_POINTS = {
#     "hum_pot": ((1.42, 45.0), (1.80, 60.0)),
#     "hum_top": ((1.40, 45.0), (1.78, 60.0)),
# }
HUMIDITY_CAL_POINTS = {}

def clamp_pct(value):
    return max(0, min(100, value))

def interpolate_two_point(voltage, low_point, high_point):
    v1, y1 = low_point
    v2, y2 = high_point
    if v1 == v2:
        return y1
    slope = (y2 - y1) / (v2 - v1)
    return y1 + (voltage - v1) * slope

def voltage_to_temp_c(voltage):
    """0.686V=-19.9C, 3.3V=60C 변환 (0.6도 하향 보정을 위해 기준 전압을 0.666V에서 0.686V로 상향 조정)"""
    v_adj = max(0, voltage - 0.686)
    val = (v_adj * (79.9 / 2.634)) - 19.9
    return round(val + TEMP_OFFSET, 2)

def voltage_to_hum_pct(voltage, key=None):
    """0.655V=0%, 3.3V=100% 변환 (0.665V에서 0.4% 낮게 측정되어 0.655V로 미세 조정)"""
    cal_points = HUMIDITY_CAL_POINTS.get(key)
    if cal_points:
        val = interpolate_two_point(voltage, cal_points[0], cal_points[1])
    else:
        val = interpolate_two_point(
            voltage,
            (HUM_V_MIN, HUM_PCT_MIN),
            (HUM_V_MIN + HUM_V_SPAN, HUM_PCT_MAX),
        )

    return round(clamp_pct((val * HUM_SCALE) + HUM_OFFSET), 2)

def voltage_to_co2_ppm(voltage):
    """0.666V=0ppm, 3.3V=5000ppm 변환"""
    v_adj = max(0, voltage - 0.666)
    val = v_adj * (5000 / 2.634)
    return round(max(0, val + CO2_OFFSET), 1)

def voltage_to_par_w_m2(voltage):
    """PAR 센서 전압 → W/m2 변환 (임시: voltage 그대로)"""
    return round(voltage, 4)

def voltage_to_soil_moisture_pct(voltage):
    """토양수분 센서 전압 → 퍼센트 변환 (임시: voltage 그대로)"""
    return round(voltage, 4)


def now_kst():
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def init_i2c():
    if not HAS_HARDWARE:
        return None
    try:
        return busio.I2C(board.SCL, board.SDA)
    except Exception:
        return None




def try_init_ads(i2c, address):
    if not i2c:
        return None, []
    try:
        ads = ADS.ADS1115(i2c, address=address)
        ads.data_rate = 860  # 읽기 속도 증가 (기본 128 -> 860 SPS)
        channels = [AnalogIn(ads, i) for i in range(4)]
        print(f"  ADS1115 0x{address:02x} 초기화 성공 (860 SPS)")
        return ads, channels
    except Exception as e:
        print(f"  ADS1115 0x{address:02x} 초기화 실패: {e}")
        return None, []


# Fast but stable filtering:
# - read fewer ADS samples per channel for lower latency
# - reject one-cycle spikes against the recent channel median
# - accept repeated large moves quickly so real changes are not over-smoothed
SAMPLE_COUNT = 7
SAMPLE_DELAY_SEC = 0.002
SETTLE_DELAY_SEC = 0.003
HISTORY_SIZE = 5
OUTLIER_ACCEPT_COUNT = 2
SLOW_ALPHA = 0.55
FAST_ALPHA = 0.85

FILTER_STATE = {}
LAST_STABLE_SNAPSHOT = None

SNAPSHOT_SPIKE_THRESHOLDS = {
    "temp_pot_c": 1.0,
    "hum_pot_pct": 2.0,
    "temp_top_c": 1.0,
    "hum_top_pct": 2.0,
    "co2_ppm": 200.0,
    "par_w_m2": 0.5,
}

SNAPSHOT_SPIKE_COUNT = 3

SNAPSHOT_KEY_TO_FILTER_KEY = {
    "temp_pot_c": "temp_pot",
    "hum_pot_pct": "hum_pot",
    "temp_top_c": "temp_top",
    "hum_top_pct": "hum_top",
    "co2_ppm": "co2",
    "par_w_m2": "par",
    "soil_moisture_1_pct": "sm1",
    "soil_moisture_2_pct": "sm2",
    "soil_moisture_3_pct": "sm3",
    "soil_moisture_4_pct": "sm4",
    "soil_moisture_5_pct": "sm5",
    "soil_moisture_6_pct": "sm6",
}

def reset_filter_to_value(filter_key, value):
    state = FILTER_STATE.get(filter_key)
    if not state or value is None:
        return
    state["history"].clear()
    state["history"].append(value)
    state["ema"] = value
    state["pending_direction"] = 0
    state["pending_count"] = 0

def reject_snapshot_spike(snapshot):
    global LAST_STABLE_SNAPSHOT

    if LAST_STABLE_SNAPSHOT is None:
        LAST_STABLE_SNAPSHOT = dict(snapshot)
        return snapshot

    spike_keys = []
    for key, threshold in SNAPSHOT_SPIKE_THRESHOLDS.items():
        current = snapshot.get(key)
        stable = LAST_STABLE_SNAPSHOT.get(key)
        if current is None or stable is None:
            continue
        if abs(current - stable) > threshold:
            spike_keys.append(key)

    if len(spike_keys) >= SNAPSHOT_SPIKE_COUNT:
        print(f"Rejected correlated sensor spike: {', '.join(spike_keys)}")
        clean_snapshot = dict(snapshot)
        for key, stable in LAST_STABLE_SNAPSHOT.items():
            if stable is not None:
                clean_snapshot[key] = stable
                filter_key = SNAPSHOT_KEY_TO_FILTER_KEY.get(key)
                if filter_key:
                    reset_filter_to_value(filter_key, stable)
        return clean_snapshot

    LAST_STABLE_SNAPSHOT = dict(snapshot)
    return snapshot

def read_measurement_period_seconds(default_period):
    db_path = monthly_db_path(DEFAULT_DB_DIR)
    if not db_path.exists():
        return default_period

    try:
        with connect_db(db_path) as conn:
            init_db(conn)
            row = conn.execute(
                "SELECT value FROM app_setting WHERE key = ?",
                ("measurement_interval_sec",),
            ).fetchone()
    except Exception:
        return default_period

    if not row:
        return default_period

    try:
        return max(0.1, float(row["value"]))
    except (TypeError, ValueError):
        return default_period

def read_snapshot(ch_4b, ch_49, ch_48):
    """
    핀맵 기준:
      0x4b A0: 온도 하부 → temp_pot_c
      0x4b A1: 습도 하부 → hum_pot_pct
      0x4b A2: 온도 상부 → temp_top_c
      0x4b A3: 습도 상부 → hum_top_pct
      0x49 A0: CO2       → co2_ppm
      0x49 A1: 조도(PAR) → par_w_m2
      0x49 A2: 토양수분1 → soil_moisture_1_pct
      0x49 A3: 토양수분2 → soil_moisture_2_pct
      0x48 A0: 토양수분3 → soil_moisture_3_pct
      0x48 A1: 토양수분4 → soil_moisture_4_pct
      0x48 A2: 토양수분5 → soil_moisture_5_pct
      0x48 A3: 토양수분6 → soil_moisture_6_pct
    """
    def safe_read(channels, idx, convert_fn, key, threshold):
        try:
            # 채널 전환 후 짧게 안정화
            _ = channels[idx].voltage
            time.sleep(SETTLE_DELAY_SEC)

            samples = []
            for _ in range(SAMPLE_COUNT):
                v = channels[idx].voltage
                if v > 0.005:
                    samples.append(v)
                time.sleep(SAMPLE_DELAY_SEC)

            if not samples:
                return None
                
            # 전압 강하 노이즈가 잦아 하위 절반은 버리고, 최상위 1개도 버립니다.
            samples.sort()
            n = len(samples)
            if n >= 5:
                valid_samples = samples[n // 2 : n - 1]
                filtered_v = statistics.mean(valid_samples) if valid_samples else statistics.median(samples)
            else:
                filtered_v = statistics.median(samples)
                
            current_val = convert_fn(filtered_v, key) if convert_fn is voltage_to_hum_pct else convert_fn(filtered_v)

            state = FILTER_STATE.setdefault(key, {
                "history": collections.deque(maxlen=HISTORY_SIZE),
                "ema": None,
                "pending_direction": 0,
                "pending_count": 0,
            })
            history = state["history"]

            input_val = current_val
            alpha = FAST_ALPHA
            if history:
                baseline = statistics.median(history)
                delta = current_val - baseline
                direction = 1 if delta > 0 else -1

                if threshold and abs(delta) > threshold:
                    if direction == state["pending_direction"]:
                        state["pending_count"] += 1
                    else:
                        state["pending_direction"] = direction
                        state["pending_count"] = 1

                    if state["pending_count"] < OUTLIER_ACCEPT_COUNT:
                        input_val = baseline
                        alpha = SLOW_ALPHA
                    else:
                        state["pending_count"] = 0
                        state["pending_direction"] = 0
                        alpha = FAST_ALPHA
                else:
                    state["pending_count"] = 0
                    state["pending_direction"] = 0
                    alpha = FAST_ALPHA if abs(delta) > (threshold * 0.35) else SLOW_ALPHA

            last_ema = state["ema"]
            smoothed_val = input_val if last_ema is None else (alpha * input_val) + ((1 - alpha) * last_ema)
            state["ema"] = smoothed_val
            history.append(smoothed_val)
            return round(smoothed_val, 2)
        except Exception:
            return None

    snapshot = {
        "temp_pot_c":          safe_read(ch_4b, 0, voltage_to_temp_c, "temp_pot", 5.0)       if ch_4b else None,
        "hum_pot_pct":         safe_read(ch_4b, 1, voltage_to_hum_pct, "hum_pot", 10.0)      if ch_4b else None,
        "temp_top_c":          safe_read(ch_4b, 2, voltage_to_temp_c, "temp_top", 5.0)       if ch_4b else None,
        "hum_top_pct":         safe_read(ch_4b, 3, voltage_to_hum_pct, "hum_top", 10.0)      if ch_4b else None,
        "co2_ppm":             safe_read(ch_49, 0, voltage_to_co2_ppm, "co2", 500.0)         if ch_49 else None,
        "par_w_m2":            safe_read(ch_49, 1, voltage_to_par_w_m2, "par", 2.0)          if ch_49 else None,
        "soil_moisture_1_pct": safe_read(ch_49, 2, voltage_to_soil_moisture_pct, "sm1", 10.0) if ch_49 else None,
        "soil_moisture_2_pct": safe_read(ch_49, 3, voltage_to_soil_moisture_pct, "sm2", 10.0) if ch_49 else None,
        "soil_moisture_3_pct": safe_read(ch_48, 0, voltage_to_soil_moisture_pct, "sm3", 10.0) if ch_48 else None,
        "soil_moisture_4_pct": safe_read(ch_48, 1, voltage_to_soil_moisture_pct, "sm4", 10.0) if ch_48 else None,
        "soil_moisture_5_pct": safe_read(ch_48, 2, voltage_to_soil_moisture_pct, "sm5", 10.0) if ch_48 else None,
        "soil_moisture_6_pct": safe_read(ch_48, 3, voltage_to_soil_moisture_pct, "sm6", 10.0) if ch_48 else None,
    }
    return reject_snapshot_spike(snapshot)


def main():
    parser = argparse.ArgumentParser(description="ADS1115 센서 snapshot을 MQTT로 발행합니다.")
    parser.add_argument("--gh", default="gh1", choices=["gh1"], help="온실 ID (현재 구현: gh1)")
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

    # MQTT 연결
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.host, args.port, 60)
        client.loop_start()
        print(f"MQTT 연결 성공: {args.host}:{args.port}")
    except Exception as e:
        print(f"MQTT 연결 실패: {e}")
        return

    # I2C 및 ADS1115 초기화
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

            payload = {
                "ts": ts,
                "source": "rpi5_main",
                **sensor_values,
            }

            client.publish(topic, json.dumps(payload))
            print(f"[{ts}] 발행 → {topic}")

            # 루프 실행 시간을 고려하여 남은 시간만큼만 대기
            elapsed = time.time() - loop_start
            period = read_measurement_period_seconds(default_period)
            time.sleep(max(0, period - elapsed))

    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
