# Arduino Tests

이 디렉터리는 Arduino UNO R4 WiFi 기반 하드웨어 bring-up과 액추에이터 개별 점검을 위한 테스트 스케치 모음입니다.
최종 운영 펌웨어가 아니라 부품별 동작 확인·안전 점검용입니다.
운영 계약은 `docs/` 문서를 우선합니다.

## 1. 테스트 현황

| 파일 | 상태 | 설명 |
|------|------|------|
| `actuators/test_vent_fan_pwm.ino` | ✅ 구현 | 환기팬 PWM 제어 (20kHz, PwmOut API) |
| `actuators/test_circ_fan_pwm.ino` | ✅ 구현 | 순환팬 PWM 제어 (환기팬과 동일 코드 — 실제 배선 시 핀 분리 필요) |
| `actuators/test_heater_slow_pwm.ino` | ✅ 구현 | 히터 time-proportional PWM (5초 윈도우, millis 기반) |
| `actuators/test_valves_onoff.ino` | ✅ 구현 | 솔레노이드 밸브 ON/OFF (MOSFET) |
| `actuators/test_mist_onoff.ino` | ✅ 구현 | 초음파 미스트 ON/OFF (MOSFET) |
| `actuators/test_window_l298n.ino` | ✅ 구현 | L298N 창문 액추에이터 (open/close/stop) |
| `actuators/test_led_addressable.ino` | ✅ 구현 | WS2811 addressable LED 색상 제어 (NeoPixel) |
| `actuators/test_pump_pwm.ino` | ❌ placeholder | |
| `sensors/test_fan_rpm_read.ino` | ❌ placeholder | |
| `mqtt/test_mqtt_subscribe_cmd.ino` | ❌ placeholder | |
| `mqtt/test_mqtt_publish_state.ino` | ❌ placeholder | |
| `mqtt/test_mqtt_publish_heartbeat.ino` | ❌ placeholder | |
| `integration/test_full_control_node.ino` | ❌ placeholder | |

> 핀 번호 등 하드웨어 세부사항은 [docs/pin-map.md](../../docs/pin-map.md) 확정 후 반영 예정

## 2. 실행 메모
- Arduino IDE에서 스케치를 하나씩 열어 업로드
- 시리얼 모니터: `115200` baud
- 고위험 부하(히터, 펌프, 창문 모터)는 마지막에 연결
- 테스트 결과는 운영 펌웨어(`control_node/`)에 정리하여 반영
