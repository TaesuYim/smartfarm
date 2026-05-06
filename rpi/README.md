<!-- File: rpi/README.md -->
# Raspberry Pi

이 디렉터리는 Raspberry Pi에서 실행되는 SmartFarm 프로그램을 담습니다.

현재 목표 UI는 `SFES Lab`이며, Raspberry Pi 모니터에서 브라우저 전체 화면 또는 kiosk 모드로 실행합니다.

## 1. 역할

Raspberry Pi는 아래 역할을 담당합니다.

- ADS1115 센서 수집
- 완성형 `sensor_snapshot` MQTT publish
- MQTT subscribe 후 월별 SQLite DB 저장
- SFES Lab UI server 실행
- 외부 weather service 실행
- Arduino reset helper 실행
- supervisor/systemd 기반 boot 자동 실행

UI는 화면 표시와 사용자 입력만 담당합니다. logger, sensor hub, weather service 같은 백그라운드 프로그램은 UI가 직접 실행하지 않고 supervisor/systemd가 실행합니다.

## 2. 권장 구조

```text
rpi/
├─ README.md
├─ requirements.txt
├─ sensor_hub/          # planned
├─ logger/
├─ ui/
├─ weather_service/     # planned
├─ supervisor/          # planned
└─ tests/
```

## 3. 주요 서비스

### `sensor_hub`

ADS1115 센서값을 읽고 변환한 뒤 `sf/gh1/sensors/snapshot`으로 publish합니다.

설정 탭의 `measurement_interval_sec`는 이 서비스의 측정/publish 주기를 의미합니다.

### `logger`

MQTT 메시지를 받아 SQLite에 저장합니다.

규칙:

- 수신 즉시 저장
- 월별 DB 파일 사용
- 파일명: `smartfarm_YYYY_MM.sqlite3`
- 현재 운영 대상은 `gh1`

### `ui`

`SFES Lab` 웹 UI입니다.

역할:

- 최신 센서값 표시
- monitoring/control/graph/settings 탭 제공
- actuator command publish
- DB에 저장된 최신값/과거값 조회

구현 방향:

- FastAPI backend + 정적 HTML/CSS/바닐라 JavaScript frontend
- JavaScript는 Chromium 브라우저에서 실행되므로 Raspberry Pi에 Node.js는 필요하지 않음
- React/Vite는 현재 범위에서 사용하지 않고 향후 확장 후보로만 둠
- slider/toggle/radio 변경 시 MQTT command를 즉시 publish
- UI/backend 시작 시 창문을 닫힘 방향으로 약 5초간 구동한 뒤 `stop`하여 개도율 계산 기준점을 보정

### `weather_service`

외부 날씨 정보를 가져와 MQTT로 publish합니다.

인터넷 접속 실패 시 서비스 전체를 죽이지 않고 publish를 생략하거나 빈 값을 보냅니다.

기상청 데이터는 매시 정시 데이터 기준으로 정시의 1분에 요청합니다. 예를 들어 `01:00` 데이터는 `01:01`에 요청합니다.

저장 대상은 KMA `ta`, `hm`, `rn`, `ws`, `icsr`, `ss`, QC 플래그, 그리고 실제로 받아온 시각입니다.

### `supervisor`

여러 Python 프로그램과 kiosk browser 실행을 관리합니다.

향후 systemd service와 연결해 Raspberry Pi 부팅 시 자동 실행합니다.

## 4. 초기 수동 실행 예시

```bash
python -m rpi.logger.mqtt_logger --db-dir data
uvicorn rpi.ui.server:app --host 127.0.0.1 --port 8000
```

월별 DB 전환이 구현되면 UI와 logger 모두 같은 DB directory 설정을 사용해야 합니다.

## 5. 전체 화면 실행 예시

```bash
chromium-browser --kiosk http://127.0.0.1:8000
```

정확한 명령은 Raspberry Pi OS와 설치된 브라우저에 맞춰 조정합니다.

## 6. 확인 필요

- sensor hub 운영 파일 위치
- weather service API 종류
- supervisor/systemd service 파일 구조
- 월을 넘는 그래프 조회 방식
- Arduino reset helper의 GPIO 핀과 릴레이 회로
