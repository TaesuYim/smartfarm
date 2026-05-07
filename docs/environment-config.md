# Environment Configuration

이 문서는 스마트팜 시스템의 환경 설정 정보(와이파이, 네트워크 IP 등)를 기록합니다.

> ⚠️ 실제 WiFi 비밀번호와 API 키는 `.env` 파일 또는 별도 보안 저장소에 관리하세요. 이 문서에는 구조만 기록하고, 민감한 값은 `.env.example`을 참고하세요.

## 1. 네트워크 정보

| 항목 | 값 | 비고 |
| --- | --- | --- |
| **WiFi SSID** | `.env` 참조 | |
| **WiFi Password** | `.env` 참조 | |
| **MQTT Broker (Pi)** | `192.168.5.22` | 라즈베리 파이 IP |
| **Node 1 IP** | `192.168.5.91` | 아두이노 (환기/히터/펌프/창문/미스트) |
| **Node 2 IP** | `192.168.5.92` | 아두이노 (밸브/LED/차광스크린) |

## 2. 주요 설정값
- **MQTT Port**: `1883`
- **Greenhouse ID**: `gh1`
- **Heater PWM Window**: `5000ms` (5초)
- **Fan PWM Frequency**: `20kHz` (Arduino UNO R4 전용)
- **DB Directory**: `data`
- **Monthly DB Filename**: `smartfarm_YYYY_MM.sqlite3`
- **KMA Weather Fetch**: 매시 `01`분에 정시 데이터 요청 (실패 시 1분 간격 3회 재시도 후 비움)
- **Node 2 LED Default Brightness**: `100%`

## 3. 관련 문서

- [json-schemas.md](json-schemas.md) — MQTT payload JSON 구조
- [mqtt-topics.md](mqtt-topics.md) — MQTT 토픽 구조
- [.env.example](../.env.example) — 크리덴셜 템플릿
