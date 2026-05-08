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
import time
import statistics
import collections
import random
from datetime import datetime, timezone, timedelta

import paho.mqtt.client as mqtt

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

def voltage_to_temp_c(voltage):
    """0.686V=-19.9C, 3.3V=60C 변환 (0.6도 하향 보정을 위해 기준 전압을 0.666V에서 0.686V로 상향 조정)"""
    v_adj = max(0, voltage - 0.686)
    val = (v_adj * (79.9 / 2.634)) - 19.9
    return round(val + TEMP_OFFSET, 2)

def voltage_to_hum_pct(voltage):
    """0.655V=0%, 3.3V=100% 변환 (0.665V에서 0.4% 낮게 측정되어 0.655V로 미세 조정)"""
    v_adj = max(0, voltage - 0.655)
    val = v_adj * (99.9 / 2.634)
    # 습도는 0~100% 사이로 제한
    return round(max(0, min(100, val + HUM_OFFSET)), 2)

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


# 각 채널별 마지막 정상 값과 슬라이딩 윈도우 버퍼
HISTORY_BUFFERS = {}
EMA_VALUES = {}

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
            # 채널 전환 후 전압 안정화
            _ = channels[idx].voltage
            time.sleep(0.01)

            # 15번 읽어서 하드웨어 중간값 취함 (노이즈 상쇄를 위한 충분한 샘플 수)
            samples = []
            for _ in range(15):
                v = channels[idx].voltage
                if v > 0.005:
                    samples.append(v)
                time.sleep(0.005)

            if not samples:
                return None
                
            # --- 상위 절사 평균 (Upper-Trimmed Mean) 필터 ---
            # 전압 강하(뚝 떨어지는) 노이즈가 많으므로 하위 50%를 버리고, 
            # 위로 튀는 최상위 값 1~2개도 버린 후 '상위권 안정값'들의 평균을 구함
            samples.sort()
            n = len(samples)
            if n >= 5:
                # 예: 15개 샘플이면 하위 7개 버림, 최상위 2개 버림 -> 8번째 ~ 13번째 값의 평균
                valid_samples = samples[n//2 : n - (n//8 + 1)]
                filtered_v = statistics.mean(valid_samples) if valid_samples else statistics.median(samples)
            else:
                filtered_v = statistics.median(samples)
                
            current_val = convert_fn(filtered_v)
            
            # --- 강력한 슬라이딩 윈도우 최댓값 필터 (값 갇힘 현상 원천 차단) ---
            if key not in HISTORY_BUFFERS:
                # 2Hz 기준 10개 = 5초 분량의 데이터 유지
                HISTORY_BUFFERS[key] = collections.deque(maxlen=10)
                
            HISTORY_BUFFERS[key].append(current_val)
            
            # 최근 5초간의 데이터 중 중간값을 선택 (자연스러운 노이즈의 중심값)
            window_median = statistics.median(HISTORY_BUFFERS[key])
            
            # --- 부드러운 UI 표시를 위한 가벼운 EMA ---
            alpha = 0.5
            last_ema = EMA_VALUES.get(key)
            if last_ema is not None:
                smoothed_val = (alpha * window_median) + ((1 - alpha) * last_ema)
            else:
                smoothed_val = window_median
                
            EMA_VALUES[key] = smoothed_val
            return round(smoothed_val, 2)
        except Exception:
            return None

    return {
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


def main():
    parser = argparse.ArgumentParser(description="ADS1115 센서 snapshot을 MQTT로 발행합니다.")
    parser.add_argument("--gh", default="gh1", choices=["gh1"], help="온실 ID (현재 구현: gh1)")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT 브로커 호스트")
    parser.add_argument("--port", default=1883, type=int, help="MQTT 브로커 포트")
    parser.add_argument("--rate", default=2.0, type=float, help="초당 발행 횟수 (기본: 2)")
    args = parser.parse_args()

    topic = f"sf/{args.gh}/sensors/snapshot"
    period = 1.0 / args.rate

    print("=== SmartFarm Sensor Snapshot Publisher ===")
    print(f"  온실: {args.gh}")
    print(f"  MQTT 토픽: {topic}")
    print(f"  발행 주기: {period:.1f}s")
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
            time.sleep(max(0, period - elapsed))

    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
