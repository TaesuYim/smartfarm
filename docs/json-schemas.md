<!-- File: docs/json-schemas.md -->
# JSON Schemas

MQTT payload JSON 구조 초안입니다. 현재 운영 대상은 `GH1`입니다.

## 1. 공통 필드

권장 공통 필드:

- `ts`: ISO 8601 timestamp string
- `source`: publisher name
- `seq`: command/state 연결용 integer, 선택

## 2. Sensor Snapshot

Topic:

```text
sf/gh1/sensors/snapshot
```

물리 입력은 ADS1115 4개, 총 16채널입니다. `0x4a/A0..A3`는 spare 채널이며, 운영 `sensor_snapshot` payload에는 UI에서 쓰는 완성형 센서값만 포함합니다.

권장 필드:

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

값 타입:

- 온도/습도/CO2/PAR/토양수분: number 또는 `null`
- 아직 연결되지 않았거나 유효하지 않은 센서값은 `null` 허용

## 3. Weather

Topic:

```text
sf/gh1/sensors/weather
```

권장 필드:

- `ts`
- `source`
- `region`
- `outdoor_temp_c`
- `outdoor_hum_pct`

인터넷/API 실패 시 publish를 생략하거나 값을 `null`로 보낼 수 있습니다.

## 4. Actuator Command

Topic:

```text
sf/gh1/actuators/cmd
```

필드:

- `ts`: string
- `source`: string
- `seq`: integer
- `vent_fan_pwm_pct`: integer `0..100`
- `circ_fan_1_pwm_pct`: integer `0..100`
- `circ_fan_2_pwm_pct`: integer `0..100`
- `heater_1_pwm_pct`: integer `0..100`
- `heater_2_pwm_pct`: integer `0..100`
- `pump_pwm_pct`: integer `0..100`
- `valve_pot_1_on`: boolean
- `valve_pot_2_on`: boolean
- `valve_pot_3_on`: boolean
- `valve_pot_4_on`: boolean
- `valve_pot_5_on`: boolean
- `valve_pot_6_on`: boolean
- `valve_fog_on`: boolean
- `mist_on`: boolean
- `window_1_cmd`: enum `open`, `close`, `stop`
- `window_2_cmd`: enum `open`, `close`, `stop`
- `shading_screen_cmd`: enum `open`, `close`, `stop`
- `led_r`: integer `0..255`
- `led_g`: integer `0..255`
- `led_b`: integer `0..255`
- `led_brightness_pct`: integer `0..100`

부분 업데이트를 허용합니다. payload에 포함된 필드만 변경합니다.

## 5. Actuator State

Topic:

```text
sf/gh1/actuators/state
```

권장 필드:

- `ts`
- `source`
- `seq`
- `result`
- `errors`
- `applied`

`applied` 내부에는 실제 적용된 actuator command key를 넣습니다.

## 6. Heartbeat

Topic:

```text
sf/gh1/actuators/heartbeat
```

필드:

- `ts`
- `source`
- `uptime_ms`

## 7. Fan RPM

Topic:

```text
sf/gh1/actuators/fan-rpm
```

필드:

- `ts`
- `source`
- `vent_fan_rpm`
- `circ_fan_1_rpm`
- `circ_fan_2_rpm`

## 8. 설정 관련

설정 탭의 `measurement_interval_sec`는 DB 저장 주기가 아니라 sensor hub의 측정/publish 주기입니다.

logger는 MQTT 메시지를 수신하는 즉시 월별 DB에 저장합니다.
