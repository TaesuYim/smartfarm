<!-- File: rpi/README.md -->
# Raspberry Pi 영역

이 디렉터리는 Raspberry Pi 쪽 코드가 들어갈 위치입니다.
현재는 기본 폴더 구조, 의존성 목록, 테스트 스크립트를 먼저 정리하고 운영 코드는 단계적으로 채워 넣는 상태입니다.

## 1. 이 디렉터리의 역할
- 센서 수집
- MQTT publish/subscribe
- SQLite 저장
- 웹 UI
- KMA 날씨 수집
- Arduino 리셋용 GPIO 제어

## 2. 현재 구조(요약)
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

## 3. 권장 설계 메모
- `gh1`, `gh2`용 코드를 따로 복제하지 않습니다.
- 온실 구분은 설정값 또는 MQTT topic namespace로 처리합니다.
- logger를 별도 서비스로 두는 구조를 권장합니다.
- UI는 DB의 최신값을 읽는 구조를 권장합니다.
- 테스트 스크립트는 운영 코드와 별도로 유지하는 편을 권장합니다.

## 4. 테스트 현황
- 구현 완료: 5개 (센서 4 + 릴레이 1 + MQTT smoke 1)
- placeholder: 8개
- 상세: [tests/README.md](tests/README.md)
- 핀맵: [docs/pin-map.md](../docs/pin-map.md) 확정 후 반영 예정

## 5. TODO
- 현재는 `requirements.txt` 기반이며, `pyproject.toml` 전환 여부는 추후 결정
- systemd 서비스 파일 구조 확정
- 실제 실행/배포 절차 정리
