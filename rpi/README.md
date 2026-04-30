<!-- File: rpi/README.md -->
# Raspberry Pi

Raspberry Pi 영역의 코드 위치입니다. 현재 운영 대상은 `GH1`입니다.

## 1. 역할

- ADS1115 센서 수집
- MQTT publish/subscribe
- 월별 SQLite 저장
- `SFES Lab` UI 제공
- 외부 날씨 수집
- Arduino reset helper
- supervisor/systemd 기반 프로세스 실행 관리

## 2. 권장 구조

```text
rpi/
├─ README.md
├─ sensor_hub/
├─ logger/
├─ ui/
├─ weather_service/
├─ supervisor/
└─ tests/
```

## 3. 실행 책임

UI는 화면 표시와 사용자 입력만 담당합니다.

백그라운드 프로그램 실행은 supervisor/systemd가 담당합니다.

대상 프로세스:

- sensor hub
- MQTT logger
- weather service
- UI server
- Arduino reset helper
- browser kiosk launcher

## 4. 센서 입력

물리 ADS 입력은 ADS1115 4개, 총 16채널입니다.

- `0x48/A0..A3`: active sensor channels
- `0x49/A0..A3`: active sensor channels
- `0x4a/A0..A3`: spare channels
- `0x4b/A0..A3`: active sensor channels

`0x4a` spare 채널은 향후 센서 확장용으로 예약합니다.

## 5. 저장 정책

- logger는 MQTT 수신 즉시 DB에 저장
- DB 파일은 월별로 분리
- 파일명 예시: `smartfarm_2026_04.sqlite3`
- 설정 탭의 측정 주기는 sensor hub의 측정/publish 주기를 의미
