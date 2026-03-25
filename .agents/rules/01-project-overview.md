<!-- File: .agents/rules/01-project-overview.md -->
# 프로젝트 개요

스마트팜 온실 2동(`gh1`, `gh2`)을 제어하는 프로젝트입니다.
상세 스펙은 `docs/` 아래 문서를 기준으로 합니다.

## 시스템 구성
- **Raspberry Pi 5**: ADS1115 센서 수집, MQTT 브로커, SQLite 로깅, 웹 UI, Arduino 재부팅용 GPIO 제어
- **Arduino UNO R4 WiFi**: 액추에이터 제어, 팬 RPM 측정, heartbeat/state publish
- **UI 탭**: 실시간 모니터링, 액추에이터 제어, 과거 추세

## 먼저 읽을 문서
- [docs/repository-structure.md](docs/repository-structure.md) — 폴더/파일 구조
- [docs/mqtt-topics.md](docs/mqtt-topics.md) — MQTT 토픽 구조, payload 예시
- [docs/ui-spec.md](docs/ui-spec.md) — UI 탭 구조, 화면 요구사항
- [docs/db-schema.md](docs/db-schema.md) — SQLite DB 스키마 초안
- [docs/pin-map.md](docs/pin-map.md) — ADS1115 주소/채널, Arduino 핀 배치
- [docs/arduino-firmware-spec.md](docs/arduino-firmware-spec.md) — Arduino 펌웨어 요구사항
- [docs/naming-conventions.md](docs/naming-conventions.md) — 네이밍 규칙
- [docs/json-schemas.md](docs/json-schemas.md) — JSON 스키마
- [OWNER.md](OWNER.md) — 운영자/오너 메모

## 임의 변경 금지 항목
- 온실 구분 값: `gh1`, `gh2`
- MQTT 토픽 프리픽스: `sf/<gh>/...`
- 핵심 토픽 구조: `sensors/*`, `actuators/*`
