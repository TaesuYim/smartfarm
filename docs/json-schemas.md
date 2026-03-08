<!-- File: docs/json-schemas.md -->
# JSON Schemas

이 문서는 MQTT payload JSON 스키마 초안입니다.
아직 구현 초반이므로 완전한 JSON Schema 파일 대신, 각 payload가 가져야 할 필드와 타입 수준의 뼈대를 먼저 정의합니다.

나중에 실제 schema 파일을 만들고 싶다면 아래 문서를 기준으로 `schemas/` 디렉터리에 분리하면 됩니다.

## 1. 공통 규칙
공통 권장 필드:
- `ts`: string, ISO 8601 timestamp
- `source`: string
- `seq`: integer, 선택

## 2. sensor snapshot schema 초안
대상 topic:
- `sf/<gh>/sensors/snapshot`

필수 권장 필드:
- `ts`
- `source`
- `temp_pot_c`
- `hum_pot_pct`
- `temp_top_c`
- `hum_top_pct`
- `co2_ppm`
- `par_w_m2`
- `soil_moisture_1_pct`
- `soil_moisture_2_pct`
- `soil_moisture_3_pct`
- `soil_moisture_4_pct`
- `soil_moisture_5_pct`
- `soil_moisture_6_pct`

타입 초안:
- 온도/습도/CO2/PAR/토양수분: number

## 3. weather schema 초안
대상 topic:
- `sf/<gh>/sensors/weather`

필수 권장 필드:
- `ts`
- `source`
- `region`
- `outdoor_temp_c`
- `outdoor_hum_pct`

타입 초안:
- `region`: string
- 나머지: number

## 4. actuator cmd schema 초안
대상 topic:
- `sf/<gh>/actuators/cmd`

필드:
- `ts`: string
- `source`: string
- `seq`: integer
- `vent_fan_pwm_pct`: integer 0..100
- `circ_fan_1_pwm_pct`: integer 0..100
- `circ_fan_2_pwm_pct`: integer 0..100
- `heater_1_pwm_pct`: integer 0..100
- `heater_2_pwm_pct`: integer 0..100
- `pump_pwm_pct`: integer 0..100
- `valve_pot_1_on`: boolean
- `valve_pot_2_on`: boolean
- `valve_pot_3_on`: boolean
- `valve_pot_4_on`: boolean
- `valve_pot_5_on`: boolean
- `valve_pot_6_on`: boolean
- `valve_fog_on`: boolean
- `mist_on`: boolean
- `window_1_cmd`: enum(`open`, `close`, `stop`)
- `window_2_cmd`: enum(`open`, `close`, `stop`)
- `led_r`: integer 0..255
- `led_g`: integer 0..255
- `led_b`: integer 0..255
- `led_brightness_pct`: integer 0..100

주의:
- 부분 업데이트 허용 여부는 구현에서 지원 가능
- 다만 schema 검증에서는 전체 명령 구조를 우선 기준으로 삼아도 됨

## 5. actuator state schema 초안
대상 topic:
- `sf/<gh>/actuators/state`

필수 권장 필드:
- `ts`
- `source`
- `result`
- `errors`
- `applied`

`applied` 내부는 actuator cmd와 동일한 key 구조를 권장합니다.

## 6. heartbeat schema 초안
대상 topic:
- `sf/<gh>/actuators/heartbeat`

필수 권장 필드:
- `ts`
- `source`
- `uptime_ms`

## 7. fan-rpm schema 초안
대상 topic:
- `sf/<gh>/actuators/fan-rpm`

필수 권장 필드:
- `ts`
- `source`
- `vent_fan_rpm`
- `circ_fan_1_rpm`
- `circ_fan_2_rpm`

타입 초안:
- RPM 필드: integer

## 8. 나중에 실제 파일로 분리할 때 권장 이름
- `sensor-snapshot.schema.json`
- `weather.schema.json`
- `actuator-cmd.schema.json`
- `actuator-state.schema.json`
- `heartbeat.schema.json`
- `fan-rpm.schema.json`

## 9. TODO
- 실제 JSON Schema 문법으로 변환
- CI에서 payload validation 수행 여부 결정
- optional/required field 최종 확정