<!-- File: AGENT.md -->
# AGENT.md

이 문서는 이 레포에서 AI 에이전트가 가장 먼저 읽는 짧은 안내서입니다.
상세 스펙은 `docs/` 아래 문서를 기준으로 합니다.
요구사항이 바뀌면 보통 코드보다 문서를 먼저 수정합니다.

## 1. 이 레포의 작업 원칙
- 이 레포는 "문서 우선(docs-first)" 방식으로 관리합니다.
- MQTT 토픽, JSON payload, UI 동작, Arduino 펌웨어 동작은 `docs/` 문서를 기준으로 합니다.
- 구현 세부는 에이전트가 단순하게 판단해도 되지만, 아래 항목은 임의 변경하지 않습니다.
  - 온실 구분 값: `gh1`, `gh2`
  - MQTT 토픽 프리픽스: `sf/<gh>/...`
  - 핵심 토픽 구조: `sensors/*`, `actuators/*`
- 요구사항이 바뀌면 해당 문서를 먼저 수정한 뒤 코드를 맞춥니다.
- AGENT.md 자체는 짧게 유지하고, 상세 내용은 `docs/`로 분리합니다.

## 2. 먼저 읽을 문서
- [docs/repository-structure.md](docs/repository-structure.md)
  - 폴더/파일 구조와 각 디렉터리의 역할
- [docs/mqtt-topics.md](docs/mqtt-topics.md)
  - MQTT 토픽 구조, 발행/구독 방향, payload 예시
- [docs/ui-spec.md](docs/ui-spec.md)
  - UI 탭 구조, 데이터 흐름, 화면 요구사항
- [docs/db-schema.md](docs/db-schema.md)
  - SQLite DB 스키마 초안과 latest 뷰 정의
- [docs/pin-map.md](docs/pin-map.md)
  - ADS1115 주소/채널과 Arduino 핀 배치
- [docs/arduino-firmware-spec.md](docs/arduino-firmware-spec.md)
  - 제어 노드(Arduino) 요구사항
- [docs/naming-conventions.md](docs/naming-conventions.md)
  - 토픽/키/디바이스 네이밍 규칙
- [docs/json-schemas.md](docs/json-schemas.md)
  - JSON 스키마 초안 및 placeholder
- [OWNER.md](OWNER.md)
  - 운영자/오너가 꼭 알아야 할 현재 결정 사항과 운영 메모

## 3. 현재 프로젝트 핵심 요약
- 대상: 스마트팜 온실 2동 `gh1`, `gh2`
- Raspberry Pi 5
  - ADS1115 기반 센서 수집
  - MQTT 브로커
  - SQLite 로깅
  - 웹 UI
  - Arduino 재부팅용 GPIO 제어
- Arduino UNO R4 WiFi
  - 액추에이터 제어
  - fan RPM 측정
  - heartbeat publish
  - actuator state publish
- UI는 다음 3개 탭을 가집니다.
  - 실시간 모니터링
  - 액추에이터 제어
  - 과거 추세
- DB 스키마는 `docs/db-schema.md` 초안을 기준으로 계속 다듬는 중입니다.
- 핀 배치는 `docs/pin-map.md`를 기준으로 관리합니다.

## 4. 에이전트에게 중요한 비기능 규칙
- 같은 기능이라도 `gh1`, `gh2`를 소스 코드로 분기 복제하지 말고, 설정 또는 파라미터로 처리합니다.
- 가능한 한 단순한 구조로 구현합니다.
- 문서에 없는 새 토픽/새 키를 추가해야 한다면 먼저 관련 문서를 갱신합니다.
- 하드웨어 안전과 관련된 변경은 PR 템플릿 체크리스트를 반드시 확인합니다.