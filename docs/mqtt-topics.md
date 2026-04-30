<!-- File: docs/mqtt-topics.md -->
# MQTT Topics

현재 운영 대상은 `GH1`만 사용합니다. topic namespace는 확장 가능성을 위해 `gh1` segment를 유지합니다.

## 1. 기본 규칙

- topic prefix: `sf/gh1`
- topic segment: lower-kebab-case
- JSON key: lower_snake_case
- UI 제어 명령은 `sf/gh1/actuators/cmd`로 publish
- Arduino 상태와 heartbeat는 logger가 subscribe해서 DB에 저장

## 2. Topic 목록

| Topic | Publisher | Consumer | 목적 |
| --- | --- | --- | --- |
| `sf/gh1/sensors/snapshot` | sensor_hub | logger, UI | 완성형 센서 스냅샷 |
| `sf/gh1/sensors/weather` | weather_service | logger, UI | 외부 날씨 정보 |
| `sf/gh1/actuators/cmd` | SFES Lab UI | Arduino control node, logger | 제어 명령 |
| `sf/gh1/actuators/state` | Arduino control node | logger, UI | 실제 적용 상태 |
| `sf/gh1/actuators/heartbeat` | Arduino control node | logger, UI | 생존 신호 |
| `sf/gh1/actuators/fan-rpm` | Arduino control node | logger, UI | 팬 RPM |

## 3. Sensor Snapshot

Topic:

```text
sf/gh1/sensors/snapshot
```

Payload:

```json
{
  "ts": "2026-04-30T12:00:00+09:00",
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

Sensor hub input note:

- Physical ADS input count is 16 channels from four ADS1115 boards.
- `0x4a/A0..A3` are reserved as spare channels.
- Production `sensor_snapshot` publishes only converted sensor fields used by the UI.

## 4. Weather

Topic:

```text
sf/gh1/sensors/weather
```

Payload:

```json
{
  "ts": "2026-04-30T12:05:00+09:00",
  "source": "weather_service",
  "region": "Seoul",
  "outdoor_temp_c": 18.2,
  "outdoor_hum_pct": 43.0
}
```

인터넷 접속 실패 시 weather publish를 생략해도 됩니다. UI는 값을 비워서 표시합니다.

## 5. Actuator Command

Topic:

```text
sf/gh1/actuators/cmd
```

Payload는 부분 업데이트를 허용합니다.

```json
{
  "ts": "2026-04-30T12:01:00+09:00",
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

## 6. Actuator State

Topic:

```text
sf/gh1/actuators/state
```

Payload:

```json
{
  "ts": "2026-04-30T12:01:01+09:00",
  "source": "arduino_node_1",
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
    "mist_on": false,
    "window_1_cmd": "stop",
    "window_2_cmd": "close"
  }
}
```

## 7. Heartbeat

Topic:

```text
sf/gh1/actuators/heartbeat
```

Payload:

```json
{
  "ts": "2026-04-30T12:01:05+09:00",
  "source": "arduino_node_1",
  "uptime_ms": 1234567
}
```

UI는 마지막 heartbeat 시간이 기준 시간보다 오래되면 LED를 OFF로 표시합니다.

## 8. Fan RPM

Topic:

```text
sf/gh1/actuators/fan-rpm
```

Payload:

```json
{
  "ts": "2026-04-30T12:01:05+09:00",
  "source": "arduino_node_1",
  "vent_fan_rpm": 1250,
  "circ_fan_1_rpm": 1100,
  "circ_fan_2_rpm": 1120
}
```

## 9. 확인 필요

- `ads_reading` raw topic은 디버깅용으로 유지할지 결정 필요
- command publish QoS/retain 정책 확정 필요
- Arduino reset 명령을 MQTT topic으로 처리할지, Raspberry Pi GPIO helper API로 처리할지 결정 필요
