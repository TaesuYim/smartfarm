# Arduino Tests

이 디렉터리는 Arduino UNO R4 WiFi 기반 하드웨어 bring-up과 액추에이터 개별 점검을 위한 테스트 스케치 모음입니다.
현재 스케치들은 최종 운영 펌웨어 전체가 아니라, 부품별 동작 확인과 안전 점검을 위한 독립 테스트에 가깝습니다.

## 1. 현재 상태 요약
- 액추에이터 개별 테스트 스케치는 여러 개 작성되어 있음
- 펌프, RPM, MQTT, 전체 integration 일부는 아직 placeholder 상태임
- 최종 운영 계약은 `docs/` 문서를 우선하고, 테스트 스케치는 하드웨어 검증 참고용으로 봅니다.

## 2. 액추에이터 테스트
- `actuators/test_vent_fan_pwm.ino`
  - 팬 PWM 제어 동작 점검
- `actuators/test_circ_fan_pwm.ino`
  - 팬 PWM 제어 동작 점검
- `actuators/test_heater_slow_pwm.ino`
  - 히터 time-proportional PWM 점검
- `actuators/test_valves_onoff.ino`
  - 솔레노이드 밸브 ON/OFF 점검
- `actuators/test_mist_onoff.ino`
  - 초음파 미스트 ON/OFF 점검
- `actuators/test_window_l298n.ino`
  - L298N 기반 창문 액추에이터 점검
- `actuators/test_led_addressable.ino`
  - addressable LED 색상 제어 점검
- `actuators/test_pump_pwm.ino`
  - 아직 placeholder

## 3. 센서/MQTT/통합 테스트
- `sensors/test_fan_rpm_read.ino`
  - 아직 placeholder
- `mqtt/test_mqtt_subscribe_cmd.ino`
  - 아직 placeholder
- `mqtt/test_mqtt_publish_state.ino`
  - 아직 placeholder
- `mqtt/test_mqtt_publish_heartbeat.ino`
  - 아직 placeholder
- `integration/test_full_control_node.ino`
  - 아직 placeholder

## 4. 실행 메모
- 일반적으로 Arduino IDE에서 스케치를 하나씩 열어 업로드합니다.
- 시리얼 모니터는 보통 `115200` baud를 사용합니다.
- 고위험 부하(히터, 펌프, 창문 모터)는 마지막에 연결하는 것을 권장합니다.
- 테스트 스케치에서 확인된 설정은 운영 펌웨어에 반영하기 전에 다시 정리합니다.

## 5. 주의
- 실제 핀맵/배선도는 별도 문서에서 최종 확정합니다.
- 이 디렉터리의 스케치는 하드웨어 검증용이므로, production 코드와 1:1로 동일하다고 가정하면 안 됩니다.
