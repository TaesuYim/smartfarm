# Environment Configuration

이 문서는 스마트팜 시스템의 환경 설정 정보(와이파이, 네트워크 IP 등)를 기록합니다.

## 1. 네트워크 정보

| 항목 | 값 | 비고 |
| --- | --- | --- |
| **WiFi SSID** | `iptime_2G` | |
| **WiFi Password** | `45612352` | |
| **MQTT Broker (Pi)** | `192.168.5.22` | 라즈베리 파이 IP |
| **Node 1 IP** | `192.168.5.91` | 아두이노 (환기/히터/펌프/창문/미스트) |
| **Node 2 IP** | `192.168.5.92` | 아두이노 (밸브/LED/차광스크린) |

## 2. 주요 설정값
- **MQTT Port**: `1883`
- **Greenhouse ID**: `gh1`
- **Heater PWM Window**: `5000ms` (5초)
- **Fan PWM Frequency**: `20kHz` (Arduino UNO R4 전용)
