"""
test_sensor_snapshot_publish.py

ADS1115 센서 4개에서 채널을 읽고,
핀맵(docs/pin-map.md) 기준으로 필드에 매핑하여
sf/gh1/sensors/snapshot MQTT 토픽에 발행합니다.

실행:
    ./rpi/.venv/bin/python rpi/tests/integration/test_sensor_snapshot_publish.py
    ./rpi/.venv/bin/python rpi/tests/integration/test_sensor_snapshot_publish.py --gh gh2
    ./rpi/.venv/bin/python rpi/tests/integration/test_sensor_snapshot_publish.py --rate 0.5
"""

import argparse
import json
import time
from datetime import datetime, timezone, timedelta

import board
import busio
import paho.mqtt.client as mqtt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ==========================================
# 전압 → 물리량 변환 함수
# TODO: 실제 센서 데이터시트/캘리브레이션 값으로 수정 필요
# 현재는 voltage 값을 그대로 사용합니다.
# ==========================================

def voltage_to_temp_c(voltage):
    """SHT 계열 온도 센서 전압 → 섭씨 변환 (임시: voltage 그대로)"""
    return round(voltage, 4)

def voltage_to_hum_pct(voltage):
    """SHT 계열 습도 센서 전압 → 퍼센트 변환 (임시: voltage 그대로)"""
    return round(voltage, 4)

def voltage_to_co2_ppm(voltage):
    """CO2 센서 전압 → ppm 변환 (임시: voltage 그대로)"""
    return round(voltage, 4)

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
    return busio.I2C(board.SCL, board.SDA)


def try_init_ads(i2c, address):
    try:
        ads = ADS.ADS1115(i2c, address=address)
        channels = [AnalogIn(ads, i) for i in range(4)]
        print(f"  ADS1115 0x{address:02x} 초기화 성공")
        return ads, channels
    except Exception as e:
        print(f"  ADS1115 0x{address:02x} 초기화 실패: {e}")
        return None, []


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
    def safe_read(channels, idx, convert_fn):
        try:
            return convert_fn(channels[idx].voltage)
        except Exception as e:
            print(f"    채널 읽기 오류 (idx={idx}): {e}")
            return None

    return {
        "temp_pot_c":          safe_read(ch_4b, 0, voltage_to_temp_c)      if ch_4b else None,
        "hum_pot_pct":         safe_read(ch_4b, 1, voltage_to_hum_pct)     if ch_4b else None,
        "temp_top_c":          safe_read(ch_4b, 2, voltage_to_temp_c)      if ch_4b else None,
        "hum_top_pct":         safe_read(ch_4b, 3, voltage_to_hum_pct)     if ch_4b else None,
        "co2_ppm":             safe_read(ch_49, 0, voltage_to_co2_ppm)     if ch_49 else None,
        "par_w_m2":            safe_read(ch_49, 1, voltage_to_par_w_m2)    if ch_49 else None,
        "soil_moisture_1_pct": safe_read(ch_49, 2, voltage_to_soil_moisture_pct) if ch_49 else None,
        "soil_moisture_2_pct": safe_read(ch_49, 3, voltage_to_soil_moisture_pct) if ch_49 else None,
        "soil_moisture_3_pct": safe_read(ch_48, 0, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_4_pct": safe_read(ch_48, 1, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_5_pct": safe_read(ch_48, 2, voltage_to_soil_moisture_pct) if ch_48 else None,
        "soil_moisture_6_pct": safe_read(ch_48, 3, voltage_to_soil_moisture_pct) if ch_48 else None,
    }


def main():
    parser = argparse.ArgumentParser(description="ADS1115 센서 snapshot을 MQTT로 발행합니다.")
    parser.add_argument("--gh", default="gh1", choices=["gh1", "gh2"], help="온실 ID (기본: gh1)")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT 브로커 호스트")
    parser.add_argument("--port", default=1883, type=int, help="MQTT 브로커 포트")
    parser.add_argument("--rate", default=1.0, type=float, help="초당 발행 횟수 (기본: 1)")
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
    client.connect(args.host, args.port, 60)
    client.loop_start()
    print(f"MQTT 연결: {args.host}:{args.port}")

    # I2C 및 ADS1115 초기화
    print("ADS1115 초기화 중...")
    i2c = init_i2c()
    ads_4b, ch_4b = try_init_ads(i2c, 0x4b)
    ads_49, ch_49 = try_init_ads(i2c, 0x49)
    ads_48, ch_48 = try_init_ads(i2c, 0x48)
    print()

    print("발행 시작... (Ctrl+C로 종료)")
    try:
        while True:
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
            for k, v in sensor_values.items():
                print(f"  {k}: {v}")
            print()

            time.sleep(period)

    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
