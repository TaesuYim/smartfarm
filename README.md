<!-- File: README.md -->
# SmartFarm

Raspberry Pi 5와 Arduino UNO R4 WiFi를 사용해 2개의 소형 온실(`gh1`, `gh2`)을 제어하는 스마트팜 프로젝트입니다.

이 레포는 코드와 문서를 함께 관리하지만, 현재는 "문서 우선(docs-first)" 방식으로 구조를 잡는 것을 목표로 합니다.
핵심 요구사항과 계약은 `docs/` 아래 문서에 정리되어 있으며, AI 에이전트는 그 문서를 기준으로 코드를 생성/수정합니다.

## 1. 시스템 개요
- 대상 온실: `gh1`, `gh2`
- Raspberry Pi 5
  - 센서 수집(ADS1115)
  - MQTT 브로커
  - SQLite 저장
  - 웹 UI
  - Arduino 리셋용 GPIO 제어
- Arduino UNO R4 WiFi
  - 액추에이터 제어
  - 팬 RPM 측정
  - heartbeat publish
  - actuator state publish

## 2. 핵심 문서
- `.agents/rules/` — AI 에이전트 규칙 (자동 로드)
- [docs/repository-structure.md](docs/repository-structure.md)
  - 현재 레포 구조와 향후 코드 배치 방향
- [docs/mqtt-topics.md](docs/mqtt-topics.md)
  - MQTT 토픽 구조와 payload 예시
- [docs/ui-spec.md](docs/ui-spec.md)
  - UI 요구사항
- [docs/db-schema.md](docs/db-schema.md)
  - SQLite DB 스키마 초안
- [docs/pin-map.md](docs/pin-map.md)
  - ADS1115 주소/채널과 Arduino 핀 배치
- [docs/arduino-firmware-spec.md](docs/arduino-firmware-spec.md)
  - Arduino 펌웨어 요구사항
- [OWNER.md](OWNER.md)
  - 오너/운영자가 먼저 읽어야 할 문서

## 3. MQTT 토픽 규칙
온실별로 토픽을 반드시 분리합니다.

- `sf/gh1/sensors/...`
- `sf/gh1/actuators/...`
- `sf/gh2/sensors/...`
- `sf/gh2/actuators/...`

예시:
- `sf/gh1/sensors/snapshot`
- `sf/gh1/actuators/cmd`
- `sf/gh2/actuators/state`

자세한 내용은 [docs/mqtt-topics.md](docs/mqtt-topics.md)를 참고하세요.

## 4. 현재 레포 구조(요약)
```text
smartfarm/
├─ OWNER.md
├─ README.md
├─ .agents/
│  └─ rules/
│     ├─ 01-project-overview.md
│     ├─ 02-docs-first.md
│     └─ 03-safety.md
├─ .github/
│  └─ pull_request_template.md
├─ docs/
│  ├─ repository-structure.md
│  ├─ mqtt-topics.md
│  ├─ ui-spec.md
│  ├─ db-schema.md
│  ├─ pin-map.md
│  ├─ arduino-firmware-spec.md
│  ├─ naming-conventions.md
│  └─ json-schemas.md
├─ rpi/
│  ├─ README.md
│  ├─ requirements.txt
│  ├─ sensor_hub/
│  ├─ logger/
│  ├─ ui/
│  ├─ weather_service/
│  └─ tests/
└─ arduino/
   ├─ README.md
   ├─ control_node/
   └─ tests/
```

## 5. 개발 흐름
1. 요구사항 변경
2. 관련 문서 수정
3. AI 에이전트가 코드 생성/수정
4. 로컬 또는 Raspberry Pi/Arduino에서 테스트
5. 필요하면 PR로 검토

## 6. 기여 방법
- 가벼운 브랜치 전략을 권장합니다.
- 모든 변경이 반드시 PR일 필요는 없지만, 아래 항목은 PR 검토를 권장합니다.
  - MQTT 토픽 구조 변경
  - UI 동작 변경
  - 히터, 모터, 릴레이, 펌프 관련 안전 변경
  - Arduino state/heartbeat/RPM 동작 변경
  - DB 스키마 초안 변경
  - 핀맵 변경

## 7. 안전 주의
이 프로젝트는 히터, 모터, 펌프, 솔레노이드 밸브, 릴레이를 포함합니다.
실기 테스트는 반드시 단계적으로 진행하세요.

- 먼저 MQTT와 소프트웨어 동작만 확인
- 그 다음 저위험 부하부터 연결
- 히터/펌프/창문 모터는 마지막에 점검

자세한 내용은 [OWNER.md](OWNER.md)와 [.github/pull_request_template.md](.github/pull_request_template.md)를 참고하세요.