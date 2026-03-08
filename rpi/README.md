<!-- File: rpi/README.md -->
# Raspberry Pi 영역

이 디렉터리는 Raspberry Pi 쪽 코드가 들어갈 위치입니다.
현재는 최소 구조만 유지하고, 구현이 시작되면 필요한 디렉터리를 추가합니다.

## 1. 이 디렉터리의 역할
- 센서 수집
- MQTT publish/subscribe
- SQLite 저장
- 웹 UI
- KMA 날씨 수집
- Arduino 리셋용 GPIO 제어

## 2. 나중에 추가될 수 있는 하위 구조(권장)
```text
rpi/
├─ README.md
├─ sensor_hub/
├─ logger/
├─ ui/
└─ weather_service/
```

## 3. 권장 설계 메모
- `gh1`, `gh2`용 코드를 따로 복제하지 않습니다.
- 온실 구분은 설정값 또는 MQTT topic namespace로 처리합니다.
- logger를 별도 서비스로 두는 구조를 권장합니다.
- UI는 DB의 최신값을 읽는 구조를 권장합니다.

## 4. TODO
- Python 프로젝트 초기화 방식 확정
- requirements 또는 pyproject 선택
- systemd 서비스 파일 구조 확정