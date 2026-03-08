<!-- File: docs/mqtt-topics.md -->
# MQTT Topics

이 문서는 MQTT 토픽과 JSON payload의 기준 문서입니다.
온실 2동(`gh1`, `gh2`) 모두 동일한 구조를 사용합니다.

## 1. 기본 규칙

### 1.1 온실 구분
- 허용 값: `gh1`, `gh2`

### 1.2 토픽 프리픽스
- `sf/gh1/sensors/...`
- `sf/gh1/actuators/...`
- `sf/gh2/sensors/...`
- `sf/gh2/actuators/...`

### 1.3 네이밍 규칙
- 토픽 segment: lower-kebab-case
- JSON key: lower_snake_case

자세한 규칙은 [docs/naming-conventions.md](naming-conventions.md)를 참고합니다.

## 2. 토픽 목록

| Topic | Publisher | Consumer | 설명 |
| --- | --- | --- | --- |
| `sf/<gh>/sensors/snapshot` | Raspberry Pi sensor_hub | logger, UI, 분석 로직 | 센서 12채널 스냅샷 |
| `sf/<gh>/sensors/weather` | Raspberry Pi weather_service | logger, UI | KMA 외기 정보 |
| `sf/<gh>/actuators/cmd` | UI 또는 상위 제어 로직 | Arduino control node | 액추에이터 제어 명령 |
| `sf/<gh>/actuators/state` | Arduino control node | logger, UI | 실제 적용된 제어 상태 |
| `sf/<gh>/actuators/heartbeat` | Arduino control node | logger, UI | 생존 신호 |
| `sf/<gh>/actuators/fan-rpm` | Arduino control node | logger, UI | 팬 RPM 3채널 |

## 3. 센서 스냅샷

### 3.1 Topic
- `sf/gh1/sensors/snapshot`
- `sf/gh2/sensors/snapshot`

### 3.2 Payload 필드
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

### 3.3 Payload 예시
```json
{
  "ts": "2026-03-03T12:00:00+09:00",
  "source": "rpi5_main",
  "temp_pot_c": 23.4,
  "hum_pot_pct": 55.1,
  "temp_top_c": 24.0,
  "hum_top_pct": 52.0,
  "co2_ppm": 830,
  "par_w_m2": 120.5,
  "soil_moisture_1_pct": 31.2,
  "soil_moisture_2_pct": 30.8,
  "soil_moisture_3_pct": 29.9,
  "soil_moisture_4_pct": 33.1,
  "soil_moisture_5_pct": 28.7,
  "soil_moisture_6_pct": 32.0
}
```

## 4. 외기 정보

### 4.1 Topic
- `sf/gh1/sensors/weather`
- `sf/gh2/sensors/weather`

### 4.2 Payload 필드
- `ts`
- `source`
- `region`
- `outdoor_temp_c`
- `outdoor_hum_pct`

### 4.3 Payload 예시
```json
{
  "ts": "2026-03-03T12:05:00+09:00",
  "source": "weather_service",
  "region": "Seoul",
  "outdoor_temp_c": 3.2,
  "outdoor_hum_pct": 40.0
}
```

## 5. 액추에이터 명령

### 5.1 Topic
- `sf/gh1/actuators/cmd`
- `sf/gh2/actuators/cmd`

### 5.2 Payload 규칙
- 부분 업데이트 허용
  - payload에 들어온 키만 변경하고 나머지는 유지 가능
- 기본 범위
  - PWM: `0..100`
  - ON/OFF: `true/false`
  - 창문 명령: `"open" | "close" | "stop"`
  - LED
    - `led_r`: `0..255`
    - `led_g`: `0..255`
    - `led_b`: `0..255`
    - `led_brightness_pct`: `0..100`

### 5.3 Payload 필드
- `ts`
- `source`
- `seq`
- `vent_fan_pwm_pct`
- `circ_fan_1_pwm_pct`
- `circ_fan_2_pwm_pct`
- `heater_1_pwm_pct`
- `heater_2_pwm_pct`
- `pump_pwm_pct`
- `valve_pot_1_on`
- `valve_pot_2_on`
- `valve_pot_3_on`
- `valve_pot_4_on`
- `valve_pot_5_on`
- `valve_pot_6_on`
- `valve_fog_on`
- `mist_on`
- `window_1_cmd`
- `window_2_cmd`
- `led_r`
- `led_g`
- `led_b`
- `led_brightness_pct`

### 5.4 Payload 예시
```json
{
  "ts": "2026-03-03T12:01:00+09:00",
  "source": "ui",
  "seq": 101,
  "vent_fan_pwm_pct": 60,
  "circ_fan_1_pwm_pct": 40,
  "circ_fan_2_pwm_pct": 40,
  "heater_1_pwm_pct": 50,
  "heater_2_pwm_pct": 0,
  "pump_pwm_pct": 30,
  "valve_pot_1_on": true,
  "valve_pot_2_on": false,
  "valve_pot_3_on": false,
  "valve_pot_4_on": false,
  "valve_pot_5_on": false,
  "valve_pot_6_on": false,
  "valve_fog_on": false,
  "mist_on": false,
  "window_1_cmd": "stop",
  "window_2_cmd": "close",
  "led_r": 80,
  "led_g": 30,
  "led_b": 0,
  "led_brightness_pct": 60
}
```

## 6. 액추에이터 상태

### 6.1 Topic
- `sf/gh1/actuators/state`
- `sf/gh2/actuators/state`

### 6.2 목적
- UI와 logger가 "실제로 적용된 값"을 확인하기 위한 상태 publish
- 가능한 경우 `seq`를 포함해 마지막 명령과 연결

### 6.3 Payload 예시
```json
{
  "ts": "2026-03-03T12:01:01+09:00",
  "source": "arduino_ctrl",
  "seq": 101,
  "result": "ok",
  "errors": [],
  "applied": {
    "vent_fan_pwm_pct": 60,
    "circ_fan_1_pwm_pct": 40,
    "circ_fan_2_pwm_pct": 40,
    "heater_1_pwm_pct": 50,
    "heater_2_pwm_pct": 0,
    "pump_pwm_pct": 30,
    "valve_pot_1_on": true,
    "valve_pot_2_on": false,
    "valve_pot_3_on": false,
    "valve_pot_4_on": false,
    "valve_pot_5_on": false,
    "valve_pot_6_on": false,
    "valve_fog_on": false,
    "mist_on": false,
    "window_1_cmd": "stop",
    "window_2_cmd": "close",
    "led_r": 80,
    "led_g": 30,
    "led_b": 0,
    "led_brightness_pct": 60
  }
}
```

## 7. Arduino Heartbeat

### 7.1 Topic
- `sf/gh1/actuators/heartbeat`
- `sf/gh2/actuators/heartbeat`

### 7.2 Payload 필드
- `ts`
- `source`
- `uptime_ms`

### 7.3 Payload 예시
```json
{
  "ts": "2026-03-03T12:01:05+09:00",
  "source": "arduino_ctrl",
  "uptime_ms": 1234567
}
```

### 7.4 운영 메모
- logger는 heartbeat를 받아 `online/offline` 상태를 판단하는 구조를 권장합니다.
- 권장 heartbeat 주기는 5초 전후이며, 최종값은 설정으로 둡니다.

## 8. Fan RPM

### 8.1 Topic
- `sf/gh1/actuators/fan-rpm`
- `sf/gh2/actuators/fan-rpm`

### 8.2 Payload 필드
- `ts`
- `source`
- `vent_fan_rpm`
- `circ_fan_1_rpm`
- `circ_fan_2_rpm`

### 8.3 Payload 예시
```json
{
  "ts": "2026-03-03T12:01:05+09:00",
  "source": "arduino_ctrl",
  "vent_fan_rpm": 1250,
  "circ_fan_1_rpm": 1100,
  "circ_fan_2_rpm": 1120
}
```

## 9. 현재 범위 밖 항목
- Arduino 재부팅은 현재 MQTT 토픽이 아니라 Raspberry Pi GPIO + 릴레이로 수행합니다.
- 차광 블라인드 제어 토픽은 현재 문서 범위 밖입니다.
  - 필요 시 추후 `actuators/*` 하위에 별도 추가

## 10. TODO
- retain/QoS 정책 확정
- 오류/경고 전용 토픽 필요 여부 검토
- JSON schema 파일 실제 분리 여부 검토