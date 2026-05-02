<!-- File: docs/naming-conventions.md -->
# Naming Conventions

UI, logger, Raspberry Pi, Arduino가 같은 이름을 쓰도록 하는 규칙입니다.

## 1. Product/UI Name

- UI 표시 이름: `SFES Lab`
- 코드 패키지 이름은 기존 Python 관례에 맞춰 `rpi.ui` 사용

## 2. Greenhouse

현재 운영 대상은 `GH1`만 사용합니다.

표기 규칙:

- UI 표시: `GH1`
- MQTT topic: `gh1`
- DB 값: `gh1`

`gh2`는 현재 구현 대상에서 제외합니다. 다만 topic 구조는 향후 확장을 위해 `sf/<greenhouse>/...` 패턴을 유지합니다. 현재 실제 운영 topic은 `sf/gh1/...`만 사용합니다.

## 3. MQTT Topic

형식:

```text
sf/gh1/<domain>/<name>
```

예시:

```text
sf/gh1/sensors/snapshot
sf/gh1/actuators/cmd
sf/gh1/actuators/heartbeat
```

규칙:

- topic segment는 lower-kebab-case 사용
- JSON key는 lower_snake_case 사용

## 4. Sensor Fields

```text
temp_pot_c
hum_pot_pct
temp_top_c
hum_top_pct
co2_ppm
par_w_m2
soil_moisture_1_pct
soil_moisture_2_pct
soil_moisture_3_pct
soil_moisture_4_pct
soil_moisture_5_pct
soil_moisture_6_pct
```

## 5. Actuator Fields

PWM:

```text
vent_fan_pwm_pct
circ_fan_1_pwm_pct
circ_fan_2_pwm_pct
heater_1_pwm_pct
heater_2_pwm_pct
pump_pwm_pct
```

ON/OFF:

```text
valve_pot_1_on
valve_pot_2_on
valve_pot_3_on
valve_pot_4_on
valve_pot_5_on
valve_pot_6_on
valve_fog_on
mist_on
```

Window:

```text
window_1_cmd
window_2_cmd
shading_screen_cmd
```

허용값:

```text
open
close
stop
```

LED:

```text
led_r
led_g
led_b
led_brightness_pct
```

## 6. DB File Name

월별 DB 파일명:

```text
smartfarm_YYYY_MM.sqlite3
```

예시:

```text
smartfarm_2026_04.sqlite3
```

## 7. Source Names

권장 source 값:

```text
rpi5_main
sensor_hub
weather_service
logger
ui
arduino_node_1
arduino_node_2
```

## 8. Settings Keys

```text
ui_refresh_sec
measurement_interval_sec
heartbeat_timeout_sec
monitoring_graph_minutes
```

## 9. 확인 필요

- PAR 단위가 최종적으로 `W/m2`가 맞는지 확인 필요
- 토양수분 값이 실제 `%` 변환 후 저장되는지 확인 필요

## 10. ADS Channel Map

물리 입력은 ADS1115 4개, 총 16채널입니다.

| ADS address | Channel | 이름 |
| --- | --- | --- |
| `0x48` | `a0`..`a3` | active sensor channels |
| `0x49` | `a0`..`a3` | active sensor channels |
| `0x4a` | `a0`..`a3` | spare channels |
| `0x4b` | `a0`..`a3` | active sensor channels |

`0x4a`의 spare 채널은 향후 센서 확장용으로 예약합니다.
