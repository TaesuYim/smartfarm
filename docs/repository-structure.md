<!-- File: docs/repository-structure.md -->
# Repository Structure

이 문서는 SmartFarm 프로젝트의 폴더 역할을 정의합니다. 현재 목표 UI는 `SFES Lab`이며 Raspberry Pi에서 브라우저 전체 화면으로 실행합니다.

## 1. 현재 주요 구조

```text
smartfarm/
├─ OWNER.md
├─ README.md
├─ .env.example
├─ .agents/
│  └─ rules/
│     ├─ 01-project-overview.md
│     ├─ 02-docs-first.md
│     └─ 03-safety.md
├─ .github/
│  └─ pull_request_template.md
├─ docs/
│  ├─ ui-spec.md
│  ├─ db-schema.md
│  ├─ mqtt-topics.md
│  ├─ arduino-firmware-spec.md
│  ├─ json-schemas.md
│  ├─ naming-conventions.md
│  ├─ pin-map.md
│  ├─ repository-structure.md
│  └─ environment-config.md
├─ rpi/
│  ├─ README.md
│  ├─ logger/
│  ├─ ui/
│  ├─ tests/
│  ├─ sensor_hub/          # planned
│  ├─ weather_service/     # planned
│  └─ supervisor/          # planned
└─ arduino/
   ├─ README.md
   ├─ control_node_1/
   ├─ control_node_2/
   └─ tests/
```

## 2. 각 위치의 역할

- `.agents/rules/`: AI 에이전트 규칙
- `OWNER.md`: 오너/운영자 관점의 메모
- `README.md`: GitHub 공개용 개요 문서
- `.github/pull_request_template.md`: PR 작성 템플릿과 안전 체크리스트
- `docs/`: 상세 스펙과 계약 문서
- `rpi/`: Raspberry Pi 관련 코드 위치
- `arduino/`: Arduino 관련 코드 위치

## 3. Raspberry Pi 영역

### `rpi/ui/`

`SFES Lab` UI 코드 위치입니다.

역할:

- 1024x600 기준 탭 UI 제공
- 브라우저 전체 화면/kiosk 모드에서 사용
- 현재 구현: 최신 센서값과 actuator 제어/상태 화면
- 목표: heartbeat, weather, graph, settings 화면까지 확장
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
- `sf/gh1/actuators/fan-rpm` 저장
- 월별 DB 파일 생성 및 전환

### `rpi/sensor_hub/`

ADS1115 센서값을 읽고 완성형 `sensor_snapshot` MQTT payload를 publish하는 코드 위치입니다.

상태:

- planned
- 기존 테스트 코드에서 sensor read/publish 실험 코드가 있음

### `rpi/weather_service/`

기상청 API를 조회하고 MQTT로 publish하는 코드 위치입니다.

규칙:

- 인터넷 접속 실패 시 서비스 전체를 죽이지 않음
- 실패 시 weather publish를 생략하거나 빈 값을 publish
- 매시 정시 데이터는 정시의 1분에 요청
- 내부온도/내부습도와 KMA `ta`, `hm`, `rn`, `ws`, `icsr`, `ss`, QC 플래그를 함께 publish

### `rpi/supervisor/`

여러 Python 프로그램을 함께 실행하고 감시하는 launcher/service 코드 위치입니다.

상태:

- planned
- 향후 Raspberry Pi boot 자동 실행과 연결

### `rpi/tests/`

센서, GPIO, MQTT, 서비스 흐름 점검용 테스트 코드 위치입니다.

## 4. Arduino 영역

### `arduino/control_node_1/`

Arduino Node 1 actuator 제어 firmware 위치입니다.

역할:

- `sf/gh1/actuators/cmd` subscribe
- 환기팬/히터/순환팬/펌프 PWM 제어
- 미스트 ON/OFF 제어
- 창문 1, 2 제어
- `sf/gh1/actuators/state` publish
- `sf/gh1/actuators/heartbeat` publish
- 필요 시 fan RPM publish (추후 구현 예정)

### `arduino/control_node_2/`

Arduino Node 2 actuator 제어 firmware 위치입니다.

역할:

- `sf/gh1/actuators/cmd` subscribe
- 솔레노이드 밸브 1..6, 포깅 밸브 ON/OFF 제어
- LED (RGB + brightness) 제어
- 차광스크린 (스텝모터 DM542) 제어
- `sf/gh1/actuators/state` publish
- `sf/gh1/actuators/heartbeat` publish

### `arduino/tests/`

actuator, MQTT, fan RPM 단위 테스트 스케치 위치입니다.

## 5. 운영 실행 구조

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

## 6. 구조 설계 원칙

- 코드 디렉터리는 기능 단위로 나눕니다.
- 현재 구현/운영 대상은 `GH1`만 사용합니다.
- `GH2`는 향후 확장 대상으로만 둡니다.
- topic 구조는 현재 `sf/gh1/...`를 사용하고, 확장 시 `sf/<greenhouse>/...` 패턴을 유지합니다.
- `gh1`, `gh2`용 코드를 따로 복제하지 않습니다.
- 문서는 최소 개수로 유지하되 MQTT, UI, DB, 핀맵, 펌웨어, 네이밍 규칙은 분리 문서로 유지합니다.

## 7. 현재/추후 추가될 수 있는 파일

- `.env.example`
- `pyproject.toml`
- `platformio.ini`
- `systemd/` 서비스 파일
- `scripts/` 배포/실행 스크립트

## 8. 확인 필요

- systemd와 supervisor의 경계
- Raspberry Pi boot 자동 실행 순서
- 운영 DB 경로와 백업 방식
