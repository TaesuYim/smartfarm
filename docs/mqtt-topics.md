<!-- File: docs/mqtt-topics.md -->
# MQTT Topics

이 문서는 SmartFarm MQTT topic과 payload 계약을 정의합니다. 현재 구현/운영 대상은 `GH1` 1개이며, `GH2`는 향후 확장 대상으로만 둡니다.

## 1. 기본 규칙

- MQTT broker는 Raspberry Pi에서 실행하는 것을 기본으로 합니다.
- topic은 모두 lower-case를 사용합니다.
- payload는 JSON을 기본으로 합니다.
- timestamp는 ISO 8601 문자열을 사용합니다.
- logger는 MQTT 수신 즉시 월별 SQLite DB에 저장합니다.
- 설정 탭의 측정 주기는 DB 저장 주기가 아니라 sensor hub publish 주기를 의미합니다.

## 2. Topic 목록

| Topic | 방향 | 저장 테이블 | 목적 |
| --- | --- | --- | --- |
| `sf/gh1/sensors/snapshot` | sensor hub -> broker | `sensor_snapshot` | 완성형 센서 스냅샷 |
| `sf/gh1/sensors/weather` | weather service -> broker | `weather` | 기상청/내부 온습도 정보 |
| `sf/gh1/actuators/cmd` | UI -> Arduino | `actuator_cmd` | actuator 제어 명령 |
| `sf/gh1/actuators/state` | Arduino -> broker | `actuator_history` | 실제 적용 상태 |
| `sf/gh1/actuators/heartbeat` | Arduino -> broker | `heartbeat` | Arduino 생존 신호 |
| `sf/gh1/actuators/fan-rpm` | Arduino -> broker | `fan_rpm` | 팬 RPM |
| `sensor/ads1115_*/+/raw` | sensor test -> broker | `ads_reading` | ADS raw 디버깅 |
| `sensor/ads1115_*/+/voltage` | sensor test -> broker | `ads_reading` | ADS voltage 디버깅 |

`ads_reading` raw topic은 운영 UI의 기본 화면에는 표시하지 않고 디버깅/보정용으로 유지할 수 있습니다.

## 3. `sf/gh1/sensors/snapshot`

ADS1115 값을 변환한 완성형 센서 payload입니다.

```json
{
  "ts": "2026-04-30T10:00:00+09:00",
  "source": "rpi5_main",
  "temp_pot_c": 27.3,
  "hum_pot_pct": 55.2,
  "temp_top_c": 26.8,
  "hum_top_pct": 57.1,
  "co2_ppm": 820,
  "par_w_m2": 120.5,
  "soil_moisture_1_pct": 43.1,
  "soil_moisture_2_pct": 44.0,
  "soil_moisture_3_pct": 42.7,
  "soil_moisture_4_pct": 45.2,
  "soil_moisture_5_pct": 43.9,
  "soil_moisture_6_pct": 41.8
}
```

## 4. `sf/gh1/sensors/weather`

기상청 및 내부 온습도 정보입니다. weather service는 1시간에 한 번, 정시의 1분에 요청합니다. 예를 들어 `01:00` 데이터는 `01:01`에 요청합니다. `ts`는 관측 데이터 시각이고, `fetched_at`은 실제로 기상청 정보를 받아온 시각입니다.

```json
{
  "ts": "2026-05-03T01:00:00+09:00",
  "fetched_at": "2026-05-03T01:01:00+09:00",
  "source": "kma",
  "station_id": "146",
  "internal_temp_c": 24.7,
  "internal_hum_pct": 62.5,
  "ta": 18.2,
  "hm": 72.0,
  "rn": 0.0,
  "ws": 1.8,
  "icsr": 0.0,
  "ss": 0.0,
  "qc_flags": {
    "ta": 0,
    "hm": 0,
    "rn": 0,
    "ws": 0,
    "icsr": 0,
    "ss": 0
  }
}
```

인터넷/API 실패 시 publish를 생략하거나 값 일부를 `null`로 보낼 수 있습니다.

## 5. `sf/gh1/actuators/cmd`

UI가 Arduino control node로 보내는 제어 명령입니다. 모든 key가 항상 포함될 필요는 없고, 변경된 항목만 포함할 수 있습니다.

```json
{
  "ts": "2026-04-30T10:00:00+09:00",
  "source": "sfes_lab_ui",
  "seq": 1001,
  "vent_fan_pwm_pct": 50,
  "circ_fan_1_pwm_pct": 40,
  "circ_fan_2_pwm_pct": 40,
  "heater_1_pwm_pct": 0,
  "heater_2_pwm_pct": 0,
  "pump_pwm_pct": 30,
  "valve_pot_1_on": false,
  "valve_pot_2_on": false,
  "valve_pot_3_on": false,
  "valve_pot_4_on": false,
  "valve_pot_5_on": false,
  "valve_pot_6_on": false,
  "valve_fog_on": false,
  "mist_on": true,
  "window_1_cmd": "stop",
  "window_2_cmd": "stop",
  "shading_screen_cmd": "stop",
  "led_r": 255,
  "led_g": 255,
  "led_b": 255,
  "led_brightness_pct": 80
}
```

## 6. `sf/gh1/actuators/state`

Arduino가 실제 적용 결과를 publish합니다.

```json
{
  "ts": "2026-04-30T10:00:01+09:00",
  "source": "arduino_node_1",
  "seq": 1001,
  "result": "ok",
  "errors": [],
  "applied": {
    "vent_fan_pwm_pct": 50,
    "circ_fan_1_pwm_pct": 40,
    "circ_fan_2_pwm_pct": 40,
    "heater_1_pwm_pct": 0,
    "heater_2_pwm_pct": 0,
    "pump_pwm_pct": 30,
    "valve_pot_1_on": false,
    "valve_pot_2_on": false,
    "valve_pot_3_on": false,
    "valve_pot_4_on": false,
    "valve_pot_5_on": false,
    "valve_pot_6_on": false,
    "valve_fog_on": false,
    "mist_on": true,
    "window_1_cmd": "stop",
    "window_2_cmd": "stop",
    "shading_screen_cmd": "stop",
    "led_r": 255,
    "led_g": 255,
    "led_b": 255,
    "led_brightness_pct": 80
  }
}
```

## 7. `sf/gh1/actuators/heartbeat`

Arduino online/offline 판단용 신호입니다.

```json
{
  "ts": "2026-04-30T10:00:00+09:00",
  "source": "arduino_node_1",
  "uptime_ms": 123456
}
```

## 8. `sf/gh1/actuators/fan-rpm`

팬 RPM 측정값입니다.

```json
{
  "ts": "2026-04-30T10:00:00+09:00",
  "source": "arduino_node_1",
  "vent_fan_rpm": 1800,
  "circ_fan_1_rpm": 1500,
  "circ_fan_2_rpm": 1490
}
```

## 9. Arduino reset

Arduino 재부팅은 현재 MQTT topic이 아니라 Raspberry Pi GPIO + 릴레이 helper로 수행합니다.

운영 UI에서는 reset 버튼을 제공하지만, 실제 GPIO 제어는 UI 프로세스가 직접 하지 않고 별도 helper 또는 system service가 담당합니다.

## 10. QoS/retain 정책

초기값:

- actuators/heartbeat: QoS 0, retain false
- actuator cmd: QoS 0 또는 1 후보, retain false 권장
- weather: QoS 0, retain false

최종 정책은 운영 테스트 후 확정합니다.

## 11. 확인 필요

- `ads_reading` raw topic을 운영 배포 후에도 유지할지 결정 필요
- command publish QoS/retain 정책 확정 필요
- GPIO reset helper를 로컬 서비스로 둘지, 별도 HTTP API 형태로 둘지 구현 방식 확정 필요
