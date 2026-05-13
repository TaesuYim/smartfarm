"""GPIO Bridge — MQTT ↔ GPIO 브릿지 데몬.

MQTT 토픽 `sf/gh1/system/arduino-power`를 구독하여
라즈베리파이 GPIO 핀으로 아두이노 전원을 제어합니다.

이 데몬이 GPIO를 독점 소유하므로, UI 서버나 외부 제어 시스템은
MQTT publish만으로 아두이노 전원을 제어할 수 있습니다.

실행:
    cd /home/pi/smartfarm/smartfarm
    python -m rpi.services.gpio_bridge
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

# Path setup
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

KST = timezone(timedelta(hours=9))

# ── Configuration ──
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_CMD = "sf/gh1/system/arduino-power"
TOPIC_STATE = "sf/gh1/system/arduino-power/state"
GPIO_PIN = 17  # BCM 모드, 릴레이 연결 핀

relay = None


def now_kst_iso():
    return datetime.now(KST).isoformat(timespec="seconds")


def init_gpio():
    """GPIO 핀 초기화. 라즈베리파이가 아닌 환경에서는 None 반환."""
    global relay
    if os.name == "nt":
        print("[gpio_bridge] Windows 환경 — GPIO 비활성화 (dry-run 모드)")
        return None
    try:
        from gpiozero import OutputDevice

        # active_high=True, initial_value=None: 현재 핀 상태 유지
        relay = OutputDevice(GPIO_PIN, active_high=True, initial_value=None)
        print(f"[gpio_bridge] GPIO {GPIO_PIN} 초기화 완료")
        return relay
    except Exception as e:
        print(f"[gpio_bridge] GPIO 초기화 실패: {e}")
        return None


def publish_state(client, state, result="ok", error=None):
    """현재 전원 상태를 state 토픽으로 publish."""
    payload = {
        "ts": now_kst_iso(),
        "state": state,
        "result": result,
    }
    if error:
        payload["error"] = str(error)
    client.publish(TOPIC_STATE, json.dumps(payload))


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[gpio_bridge] MQTT 연결 성공, 구독: {TOPIC_CMD}")
        client.subscribe(TOPIC_CMD)
    else:
        print(f"[gpio_bridge] MQTT 연결 실패: rc={rc}")


def on_message(client, userdata, msg):
    global relay
    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[gpio_bridge] 잘못된 payload: {e}")
        return

    state = payload.get("state", "").lower()
    source = payload.get("source", "unknown")

    if state not in ("on", "off"):
        print(f"[gpio_bridge] 무시: 알 수 없는 state '{state}' (from {source})")
        return

    print(f"[gpio_bridge] 명령 수신: state={state}, source={source}")

    if relay is None:
        # dry-run 모드 (Windows 등)
        print(f"[gpio_bridge] dry-run: GPIO 미사용, state={state}")
        publish_state(client, state, result="ok_dry_run")
        return

    try:
        if state == "on":
            relay.on()
        else:
            relay.off()
        print(f"[gpio_bridge] GPIO {GPIO_PIN} → {state.upper()}")
        publish_state(client, state)
    except Exception as e:
        print(f"[gpio_bridge] GPIO 제어 실패: {e}")
        publish_state(client, state, result="error", error=e)


def main():
    print("[gpio_bridge] 시작...")
    init_gpio()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            print("\n[gpio_bridge] 종료 요청")
            break
        except Exception as e:
            print(f"[gpio_bridge] MQTT 연결 오류: {e}, 5초 후 재시도...")
            time.sleep(5)

    client.disconnect()
    if relay:
        relay.close()
        print("[gpio_bridge] GPIO 리소스 해제")


if __name__ == "__main__":
    main()
