<!-- File: docs/repository-structure.md -->
# Repository Structure

이 문서는 SmartFarm 프로젝트의 폴더 역할을 정의합니다. 현재 목표 UI는 `SFES Lab`이며 Raspberry Pi에서 브라우저 전체 화면으로 실행합니다.

## 1. 현재 주요 구조

```text
smartfarm/
├─ docs/
│  ├─ ui-spec.md
│  ├─ db-schema.md
│  ├─ mqtt-topics.md
│  ├─ arduino-firmware-spec.md
│  ├─ json-schemas.md
│  └─ naming-conventions.md
├─ rpi/
│  ├─ logger/
│  ├─ ui/
│  ├─ tests/
│  ├─ sensor_hub/          # planned
│  ├─ weather_service/     # planned
│  └─ supervisor/          # planned
└─ arduino/
   ├─ control_node/        # planned
   └─ tests/
```

## 2. Raspberry Pi 영역

### `rpi/ui/`

`SFES Lab` UI 코드 위치입니다.

역할:

- 1024x600 기준 탭 UI 제공
- 브라우저 전체 화면/kiosk 모드에서 사용
- sensor, actuator, heartbeat, weather, graph 화면 제공
- 화면 표시와 사용자 입력 처리 담당
- Python 서비스 실행은 UI가 직접 하지 않고 supervisor/systemd가 담당

### `rpi/logger/`

MQTT 메시지를 받아 월별 SQLite DB에 저장하는 서비스 위치입니다.

역할:

- `sf/gh1/sensors/snapshot` 저장
- `sf/gh1/sensors/weather` 저장
- `sf/gh1/actuators/cmd` 저장
- `sf/gh1/actuators/state` 저장
- `sf/gh1/actuators/heartbeat` 저장
- 월별 DB 파일 생성 및 전환

### `rpi/sensor_hub/`

ADS1115 센서값을 읽고 완성형 `sensor_snapshot` MQTT payload를 publish하는 코드 위치입니다.

상태:

- planned
- 기존 테스트 코드에서 sensor read/publish 실험 코드가 있음

### `rpi/weather_service/`

외부 날씨 API를 조회하고 MQTT로 publish하는 코드 위치입니다.

규칙:

- 인터넷 접속 실패 시 서비스 전체를 죽이지 않음
- 실패 시 weather publish를 생략하거나 빈 값을 publish

### `rpi/supervisor/`

여러 Python 프로그램을 함께 실행하고 감시하는 launcher/service 코드 위치입니다.

상태:

- planned
- 향후 Raspberry Pi boot 자동 실행과 연결

## 3. Arduino 영역

### `arduino/control_node/`

Arduino actuator 제어 firmware 위치입니다.

역할:

- `sf/gh1/actuators/cmd` subscribe
- PWM/ON-OFF/window/LED 제어
- `sf/gh1/actuators/state` publish
- `sf/gh1/actuators/heartbeat` publish
- 필요 시 fan RPM publish

### `arduino/tests/`

actuator, MQTT, fan RPM 단위 테스트 스케치 위치입니다.

## 4. 운영 실행 구조

최종 목표:

```text
Raspberry Pi boot
-> systemd starts SFES Lab supervisor
-> supervisor starts MQTT broker check, logger, sensor_hub, weather_service, UI server
-> browser opens SFES Lab in fullscreen/kiosk mode
```

초기 구현 단계:

```text
python -m rpi.ui.app
python -m rpi.logger.mqtt_logger
sensor_hub script
weather_service script
```

## 5. 확인 필요

- systemd service 파일을 repo에 포함할지 결정 필요
- supervisor와 systemd service 구성 방식 확정 필요
- 월별 DB 파일 저장 디렉터리 기본값 확정 필요
