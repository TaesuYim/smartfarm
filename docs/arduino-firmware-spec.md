<!-- File: docs/arduino-firmware-spec.md -->
# Arduino Firmware Specification

이 문서는 SmartFarm Arduino control node firmware의 역할과 MQTT 계약을 정의합니다.

## 1. 기본 방향

- 현재 운영 대상은 `GH1`입니다.
- Arduino control node는 2개 운용합니다.
  - **Node 1** (`control_node_1`): 환기팬, 히터, 순환팬, 펌프, 미스트, 창문 제어
  - **Node 2** (`control_node_2`): 솔레노이드 밸브, LED, 차광스크린(스텝모터) 제어
- Raspberry Pi는 UI, logger, sensor hub, weather service, supervisor/systemd를 담당합니다.
- Arduino 재부팅은 MQTT topic이 아니라 Raspberry Pi GPIO + 릴레이 helper로 수행합니다.

## 2. MQTT 연결

Arduino control node는 아래 topic을 사용합니다.

| Topic | 방향 | 목적 |
| --- | --- | --- |
| `sf/gh1/actuators/cmd` | subscribe | UI 제어 명령 수신 |
| `sf/gh1/actuators/state` | publish | 실제 적용 상태 보고 |
| `sf/gh1/actuators/heartbeat` | publish | online/offline 판단 |
| `sf/gh1/actuators/fan-rpm` | publish | 팬 RPM 보고 |

## 3. Command 처리

`sf/gh1/actuators/cmd` payload는 JSON입니다. command에는 전체 actuator 값 또는 변경된 일부 값만 포함될 수 있습니다.

Firmware는 다음 규칙을 따릅니다.

- 수신한 key만 상태에 반영합니다.
- PWM 값은 `0..100` 범위로 제한합니다.
- ON/OFF 값은 boolean 또는 `0/1`로 처리합니다.
- window command는 `open`, `close`, `stop`만 허용합니다.
- 허용되지 않는 window command는 `stop`으로 처리합니다.
- 명령 적용 후 `state` topic으로 결과를 publish합니다.

## 4. Actuator 대상

### Node 1 담당

PWM 제어:

- 환기팬
- 순환팬 1
- 순환팬 2
- 히터 1
- 히터 2
- 펌프

ON/OFF 제어:

- 미스트

창문 제어:

- 창문 1
- 창문 2
- 명령: `open`, `close`, `stop`

### Node 2 담당

ON/OFF 제어:

- 화분 밸브 1..6
- 포깅 밸브

LED 제어:

- RGB
- brightness

차광스크린 제어:

- 스텝모터 (DM542 드라이버)
- 명령: `open`, `close`, `stop`

## 5. State publish

명령을 적용한 뒤 Arduino는 `sf/gh1/actuators/state`에 실제 적용 상태를 publish합니다.

필수 필드:

- `ts`
- `source`
- `seq`
- `result`
- `errors`
- `applied`

`seq`는 UI command와 Arduino state를 연결하는 값입니다.

## 6. Heartbeat

Arduino는 주기적으로 `sf/gh1/actuators/heartbeat`를 publish합니다.

권장 주기:

- 5초

UI는 마지막 heartbeat 수신 시각을 기준으로 LED 상태를 표시합니다.

## 7. Fan RPM

팬 RPM 측정이 가능한 경우 Arduino는 `sf/gh1/actuators/fan-rpm`을 publish합니다.

대상:

- `vent_fan_rpm`
- `circ_fan_1_rpm`
- `circ_fan_2_rpm`

## 8. Reset

운영 UI에는 Arduino reset 버튼이 있습니다.

단, reset은 Arduino firmware가 자기 자신에게 MQTT 명령을 받아 수행하는 방식이 아니라 Raspberry Pi GPIO + 릴레이 helper가 수행합니다.

권장 동작:

- UI reset 버튼 클릭
- UI/backend helper가 reset 요청 처리
- Raspberry Pi GPIO가 릴레이를 짧게 제어
- Arduino 전원 또는 reset line이 재시작됨
- Arduino가 다시 WiFi/MQTT 연결 후 heartbeat publish

## 9. 안전 규칙

- 부팅 직후 actuator는 안전한 기본값으로 설정합니다.
- MQTT 연결 전에도 actuator가 임의로 켜지지 않아야 합니다.
- MQTT 연결이 끊겨도 마지막 상태 유지 또는 안전 상태 전환 정책을 명확히 해야 합니다.
- heater/window/pump처럼 위험도가 있는 actuator는 테스트 단계에서 낮은 출력부터 확인합니다.

## 10. 확인 필요

- MQTT 연결 끊김 시 actuator 상태 유지 정책
- window 개도율 계산 방식
- fan RPM publish 주기
- relay reset helper의 실제 회로와 GPIO 핀
