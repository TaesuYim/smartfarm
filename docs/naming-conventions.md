<!-- File: docs/naming-conventions.md -->
# Naming Conventions

이 문서는 토픽, JSON key, 디바이스 이름 등의 규칙을 정리합니다.
목표는 UI, logger, Raspberry Pi, Arduino가 같은 이름을 쓰도록 하는 것입니다.

## 1. 기본 규칙

### 1.1 MQTT topic
- 형식: `sf/<gh>/<domain>/<name>`
- `<gh>`: `gh1`, `gh2`
- `<domain>`: `sensors`, `actuators`
- topic segment 표기: lower-kebab-case

예:
- `sf/gh1/sensors/snapshot`
- `sf/gh2/actuators/fan-rpm`

### 1.2 JSON key
- 표기: lower_snake_case
- 단위가 명확하면 suffix를 붙임
  - `_c`: 섭씨
  - `_pct`: 퍼센트
  - `_ppm`: ppm
  - `_rpm`: rpm
  - `_ms`: milliseconds
  - `_cmd`: command field

예:
- `temp_pot_c`
- `hum_top_pct`
- `co2_ppm`
- `vent_fan_rpm`
- `window_1_cmd`

## 2. source 이름
권장 값:
- `rpi5_main`
- `sensor_hub`
- `weather_service`
- `logger`
- `ui`
- `arduino_ctrl`

## 3. 센서 키
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

## 4. 외기 키
- `region`
- `outdoor_temp_c`
- `outdoor_hum_pct`

## 5. 액추에이터 명령/상태 키

### 5.1 PWM 계열
- `vent_fan_pwm_pct`
- `circ_fan_1_pwm_pct`
- `circ_fan_2_pwm_pct`
- `heater_1_pwm_pct`
- `heater_2_pwm_pct`
- `pump_pwm_pct`

### 5.2 ON/OFF 계열
- `valve_pot_1_on`
- `valve_pot_2_on`
- `valve_pot_3_on`
- `valve_pot_4_on`
- `valve_pot_5_on`
- `valve_pot_6_on`
- `valve_fog_on`
- `mist_on`

### 5.3 창문 계열
- `window_1_cmd`
- `window_2_cmd`

허용 값:
- `open`
- `close`
- `stop`

### 5.4 LED 계열
- `led_r`
- `led_g`
- `led_b`
- `led_brightness_pct`

권장 범위:
- `led_r`, `led_g`, `led_b`: `0..255`
- `led_brightness_pct`: `0..100`

## 6. fan RPM 키
- `vent_fan_rpm`
- `circ_fan_1_rpm`
- `circ_fan_2_rpm`

## 7. 일반 규칙
- payload에 한국어 key를 사용하지 않음
- 숫자 인덱스가 필요한 경우 1부터 시작
  - 예: `soil_moisture_1_pct`
- 배열보다 명시적 key를 우선 사용
  - 예: `soil_moisture_1_pct` ... `soil_moisture_6_pct`

## 8. TODO
- PAR 최종 단위가 바뀌면 `par_*` 네이밍 재검토
- actuator state에 에러 코드 체계를 둘지 결정