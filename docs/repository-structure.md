<!-- File: docs/repository-structure.md -->
# Repository Structure

이 문서는 현재 레포 구조와 향후 코드가 들어갈 위치를 설명합니다.
목표는 "복잡하지 않게 시작하고, 필요한 만큼만 늘리는 것"입니다.

## 1. 현재 구조
```text
smartfarm/
├─ AGENT.md
├─ OWNER.md
├─ README.md
├─ .github/
│  └─ pull_request_template.md
├─ docs/
│  ├─ repository-structure.md
│  ├─ mqtt-topics.md
│  ├─ ui-spec.md
│  ├─ db-schema.md
│  ├─ arduino-firmware-spec.md
│  ├─ naming-conventions.md
│  ├─ json-schemas.md
│  └─ pin-map.md
├─ rpi/
│  ├─ README.md
│  ├─ requirements.txt
│  ├─ sensor_hub/
│  ├─ logger/
│  ├─ ui/
│  ├─ weather_service/
│  └─ tests/
│     ├─ README.md
│     ├─ sensors/
│     │  ├─ test_ads1115_basic.py
│     │  ├─ test_temp_humidity_inputs.py
│     │  ├─ test_co2_input.py
│     │  ├─ test_par_input.py
│     │  └─ test_soil_moisture_inputs.py
│     ├─ actuators/
│     │  ├─ test_rpi_gpio_relay_reset.py
│     │  └─ test_mqtt_command_publish.py
│     ├─ services/
│     │  ├─ test_logger_write_sqlite.py
│     │  ├─ test_weather_kma_fetch.py
│     │  └─ test_ui_db_read_latest.py
│     └─ integration/
│        ├─ test_sensor_to_mqtt.py
│        ├─ test_mqtt_to_sqlite.py
│        └─ test_end_to_end_local.py
└─ arduino/
   ├─ README.md
   ├─ control_node/
   └─ tests/
      ├─ README.md
      ├─ actuators/
      │  ├─ test_vent_fan_pwm.ino
      │  ├─ test_circ_fan_pwm.ino
      │  ├─ test_heater_slow_pwm.ino
      │  ├─ test_pump_pwm.ino
      │  ├─ test_valves_onoff.ino
      │  ├─ test_mist_onoff.ino
      │  ├─ test_window_l298n.ino
      │  └─ test_led_addressable.ino
      ├─ sensors/
      │  └─ test_fan_rpm_read.ino
      ├─ mqtt/
      │  ├─ test_mqtt_subscribe_cmd.ino
      │  ├─ test_mqtt_publish_state.ino
      │  └─ test_mqtt_publish_heartbeat.ino
      └─ integration/
         └─ test_full_control_node.ino
```

## 2. 각 위치의 역할
- `AGENT.md`
  - 에이전트가 가장 먼저 읽는 짧은 안내서
- `OWNER.md`
  - 오너/운영자 관점의 메모
- `README.md`
  - GitHub 공개용 개요 문서
- `.github/pull_request_template.md`
  - PR 작성 템플릿과 안전 체크리스트
- `docs/`
  - 상세 스펙과 계약 문서
- `docs/db-schema.md`
  - SQLite DB 스키마 초안
- `rpi/`
  - Raspberry Pi 관련 코드 위치
- `arduino/`
  - Arduino 관련 코드 위치

## 3. 코드가 들어갈 때 권장 구조
현재는 테스트와 기본 폴더 구조를 먼저 확보한 상태이며, 운영 코드는 단계적으로 채워 넣습니다.
아래와 같은 방향을 권장합니다.

### 3.1 Raspberry Pi 코드
```text
rpi/
├─ README.md
├─ requirements.txt
├─ sensor_hub/
├─ logger/
├─ ui/
├─ weather_service/
└─ tests/
```

- `sensor_hub/`
  - ADS1115 센서 수집
  - MQTT publish
- `logger/`
  - MQTT subscribe
  - SQLite 저장
  - heartbeat 모니터링
- `ui/`
  - 웹 UI
- `weather_service/`
  - KMA API 수집
  - MQTT publish
- `tests/`
  - 센서, GPIO, MQTT, 서비스 흐름 점검용 스크립트

### 3.2 Arduino 코드
```text
arduino/
├─ README.md
├─ control_node/
└─ tests/
```

- `control_node/`
  - 제어 노드 펌웨어
  - MQTT subscribe/publish
  - RPM/heartbeat/state 처리
- `tests/`
  - 액추에이터 단위 테스트와 MQTT/RPM/integration bring-up 스케치

## 4. 구조 설계 원칙
- 코드 디렉터리는 "기능 단위"로 나눕니다.
- `gh1`, `gh2`용 코드를 따로 복제하지 않습니다.
- 온실 구분은 설정값 또는 topic namespace로 처리합니다.
- 문서 수는 최소로 유지하되, 계약(MQTT/UI/DB/펌웨어/네이밍)은 분리 문서로 유지합니다.

## 5. 현재/추후 추가될 수 있는 파일
구현이 진행되면 아래 파일이 추가되거나 정리될 수 있습니다.

- `.env.example`
- `pyproject.toml`
- `platformio.ini`
- `systemd/` 서비스 파일
- `scripts/` 배포/실행 스크립트

필요할 때 추가하면 됩니다.
