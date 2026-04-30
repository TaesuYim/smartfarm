<!-- File: docs/arduino-firmware-spec.md -->
# Arduino Firmware Specification

Arduino UNO R4 WiFi 기반 actuator control node의 요구사항입니다. 현재 운영 대상은 `GH1`입니다.

## 1. MQTT 연결

Subscribe:

```text
sf/gh1/actuators/cmd
```

Publish:

```text
sf/gh1/actuators/state
sf/gh1/actuators/heartbeat
sf/gh1/actuators/fan-rpm
```

권장 source:

```text
arduino_node_1
```

## 2. PWM 제어

| 장치 | 입력 key | 범위 | 비고 |
| --- | --- | --- | --- |
| 환기팬 | `vent_fan_pwm_pct` | `0..100` | 고주파 PWM |
| 순환팬 1 | `circ_fan_1_pwm_pct` | `0..100` | 고주파 PWM |
| 순환팬 2 | `circ_fan_2_pwm_pct` | `0..100` | 고주파 PWM |
| 히터 1 | `heater_1_pwm_pct` | `0..100` | `millis()` 기반 slow PWM |
| 히터 2 | `heater_2_pwm_pct` | `0..100` | `millis()` 기반 slow PWM |
| 펌프 | `pump_pwm_pct` | `0..100` | PWM |

## 3. ON/OFF 제어

| 장치 | 입력 key | 동작 |
| --- | --- | --- |
| 포트 밸브 1 | `valve_pot_1_on` | `true` = ON |
| 포트 밸브 2 | `valve_pot_2_on` | `true` = ON |
| 포트 밸브 3 | `valve_pot_3_on` | `true` = ON |
| 포트 밸브 4 | `valve_pot_4_on` | `true` = ON |
| 포트 밸브 5 | `valve_pot_5_on` | `true` = ON |
| 포트 밸브 6 | `valve_pot_6_on` | `true` = ON |
| 포그 밸브 | `valve_fog_on` | `true` = ON |
| 미스트 | `mist_on` | `true` = ON |

## 4. Window 제어

입력:

```text
window_1_cmd
window_2_cmd
```

허용값:

```text
open
close
stop
```

L298N 기준 동작:

| 명령 | IN1 | IN2 |
| --- | --- | --- |
| `open` | HIGH | LOW |
| `close` | LOW | HIGH |
| `stop` | LOW | LOW |

## 5. LED 제어

입력:

```text
led_r
led_g
led_b
led_brightness_pct
```

값 범위:

- `led_r`, `led_g`, `led_b`: `0..255`
- `led_brightness_pct`: `0..100`

## 6. Heartbeat

Arduino는 주기적으로 heartbeat를 publish합니다.

Topic:

```text
sf/gh1/actuators/heartbeat
```

Payload:

```json
{
  "ts": "",
  "source": "arduino_node_1",
  "uptime_ms": 1234567
}
```

UI는 이 신호를 LED 형태로 표시합니다.

## 7. State Publish

명령 적용 후 Arduino는 실제 적용 상태를 publish합니다.

Topic:

```text
sf/gh1/actuators/state
```

필수 필드:

```text
ts
source
seq
result
errors
applied
```

## 8. 안전 기본값

부팅 직후 또는 통신 불안정 시 기본 상태:

- 모든 PWM = 0
- 모든 밸브 OFF
- 미스트 OFF
- 창문 = `stop`
- LED OFF

## 9. 확인 필요

- Arduino reset을 MQTT command로 처리할지 Raspberry Pi GPIO helper로 처리할지 결정 필요
- MQTT disconnect 시 actuator를 안전 상태로 내릴지, 마지막 상태를 유지할지 결정 필요
- fan RPM의 PPR과 pull-up 회로 확정 필요
