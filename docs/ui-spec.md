<!-- File: docs/ui-spec.md -->
# SFES Lab UI Specification

이 문서는 SmartFarm UI의 목표 화면과 동작 요구사항을 정리합니다.

## 1. 기본 방향

- UI 이름: `SFES Lab`
- **UI 구조: FastAPI backend + 정적 HTML/CSS/바닐라 JavaScript frontend**
- 브라우저 기본 JavaScript를 사용하므로 Raspberry Pi에 Node.js를 설치하지 않아도 됩니다.
- React/Vite는 현재 범위에서 사용하지 않고, UI가 커질 경우 향후 전환 후보로만 둡니다.
- 대상 화면: Raspberry Pi 모니터 기준 `1280x800`
- 대상 디스플레이: 10.1 inch IPS 1280×800, 정전식 터치
- 실제 디스플레이 사이즈: 216.57mm × 135.36mm
- 다른 해상도에서도 깨지지 않도록 반응형으로 구현
- 브라우저 전체 화면 또는 kiosk 모드 사용
- 긴 단일 페이지가 아니라 탭 기반 화면 구성
- 현재 구현/운용 대상 온실은 `GH1`만 사용
- `GH2`는 향후 확장 대상으로만 둠
- UI는 화면 표시와 사용자 입력만 담당
- 필요한 Python 백그라운드 프로그램은 별도 supervisor/systemd가 실행
- 향후 Raspberry Pi 부팅 시 supervisor/systemd가 UI와 백그라운드 프로그램을 자동 실행

## 2. 화면 구조

상단에는 앱 이름 `SFES Lab`, 현재 시각, 연결 상태 요약을 표시합니다.

탭은 아래 4개로 구성합니다.

| 탭 | 목적 |
| --- | --- |
| 모니터링 | 현재 센서값, Arduino heartbeat, 날씨 확인 (성능 위해 그래프 제외) |
| 제어 | actuator 제어값 입력 및 명령 전송 |
| 그래프 | 사용자가 선택한 기간의 DB 추세 분석 |
| 설정 | 화면 업데이트 주기와 센서 측정 주기 설정 |

## 3. 공통 정책

- 화면 어디서든 현재 날짜/시간 표시
- 각 탭별로 마지막 업데이트 시간 1개 표시
- UI의 모니터링 탭은 SQLite의 `ui_latest` 테이블을 읽어 표시
- UI의 그래프 탭은 SQLite의 과거값을 읽어 표시
- 제어 입력은 MQTT command로 publish
- 기준 운영 대상은 `GH1` 1개이며, topic 구조는 `sf/gh1/...`를 유지

## 4. 모니터링 탭

모니터링 탭은 실시간 현황을 한 화면에서 빠르게 확인하는 화면입니다.

필수 요소:

- 최신 `ui_latest` 테이블에서 센서값 및 날씨 정보 표시
- Arduino heartbeat 상태 표시
- Arduino 리셋 버튼

현재 UI 구현 방향:

- FastAPI가 API와 정적 파일 서빙을 담당합니다.
- HTML/CSS/바닐라 JavaScript가 kiosk 화면을 구성합니다.
- JavaScript는 브라우저에서 실행되므로 Raspberry Pi에는 Python, FastAPI/uvicorn, Chromium만 있으면 됩니다.

표시 대상 센서 항목:

- 온도 2개
- 습도 2개
- CO2 1개
- PAR 1개
- 토양수분 6개

Heartbeat 표시:

- LED 형태로 표시
- heartbeat 신호가 최근 기준 시간 안에 들어오면 ON
- heartbeat 신호가 기준 시간 이상 끊기면 OFF
- 기준 시간은 설정 탭에서 조정 가능하게 설계

Arduino 전원 제어:

- UI에서 아두이노 전원 ON/OFF 토글 스위치 제공
- 실제 구현은 Raspberry Pi GPIO 17번 릴레이를 제어하며, 백엔드의 `/api/arduino/power` 엔드포인트를 사용
- 전원 OFF 시 시스템 멈춤 방지를 위해 재확인(confirm) 창을 띄워 오작동 방지
- 백엔드에서는 전역 객체를 사용하여 핀 초기화를 방지하고 상태를 안정적으로 유지

날씨 정보:

- ui_latest 테이블의 외부 날씨 정보를 가져와 표시
- 현재 표시 중인 날씨 정보가 업데이트된 시간 정보를 함께 표시
- ui_latest 에 날씨 정보가 없을 경우 공란으로 둠

## 5. 제어 탭

제어 탭은 UI에서 actuator 값을 변경하고 MQTT command를 발행하는 화면입니다.

입력 방식:

- ON/OFF 제어는 toggle 사용
- PWM 제어는 slider 사용
- PWM 값은 숫자 입력으로도 조절 가능
- window 제어는 `open`, `close`, `stop` 선택 방식 사용
- LED 제어가 포함될 경우 RGB와 brightness 입력 제공
- 사용자가 slider/toggle/radio를 변경하면 즉시 MQTT command를 publish합니다.
- 별도 "적용" 버튼을 기다리지 않는 즉시 반응형 제어 UX를 기본 정책으로 합니다.

제어 대상 예시:

- 환기팬
- 히터
- 순환팬
- 펌프
- 솔레노이드 밸브
- 미스트
- 창문 1, 2
- 필요 시 LED
- 필요 시 팬 RPM 표시

제어값 저장:

- 사용자가 제어값을 변경하면 MQTT command를 publish
- 동시에 변경된 제어값을 DB에 저장
- 저장 대상은 `actuator_cmd` 테이블
- Arduino가 실제 적용 상태를 publish하면 `actuator_history` 테이블에 저장하고 `ui_latest`를 갱신
- 즉시 전송 정책을 사용하므로 프론트엔드는 중복 이벤트와 너무 잦은 slider 이벤트를 방지해야 합니다.
- PWM slider는 필요 시 짧은 debounce 또는 change 이벤트 기준으로 전송합니다.

창문 초기 보정:

- 창문에는 별도 위치 센서가 없으므로 UI 로드 시 기준점을 맞추는 보정 동작이 필요합니다.
- 실제 창문 모터의 제어 방향이 반전되어 있으므로, 닫힘 방향 구동을 위해 `open` 명령을 약 5초간 전송한 뒤 `stop` 명령을 보내 완전히 닫힌 상태를 기준점으로 삼습니다. (화면의 열기/닫기 버튼 동작 시에도 내부적으로 반전된 명령 전송)
- 초기 보정 시퀀스는 창문 1과 창문 2에만 적용되며, 차광스크린은 보정 대상에서 제외됩니다.
- 이 동작은 의도된 운영 정책이며, 이후 개도율 계산의 기준이 됩니다.
- 보정 명령도 일반 actuator command와 같은 `sf/gh1/actuators/cmd` topic을 사용합니다.

## 6. 그래프 탭

그래프 탭은 과거 DB 데이터를 기간 기준으로 조회하는 화면입니다.

필수 요소:

- 시작 시간과 종료 시간으로 그래프 기간 설정
- 선택 기간 동안의 `sensor_snapshot` 추세 그래프 표시
- 온도, 습도, CO2, PAR, 토양수분을 선택해서 볼 수 있는 구조
- 데이터가 없는 기간은 빈 그래프로 표시하고 UI는 멈추지 않음

권장 그래프 그룹:

- 하나의 그래프에 내부 온도, 외기 온도, 내부 습도, 외기 습도, 내부 이산화탄소를 동시에 표시(왼쪽 y축은 온도와 습도를 동일 스케일로 표시, 오른쪽 y축은 co2 농도(ppm)를 표시)
- 토양수분 그래프
- PAR 개별 그래프

## 7. 설정 탭

설정 탭은 UI와 측정 동작의 주기를 조정하는 화면입니다.

설정 항목:
- 화면 업데이트 주기
- 센서 측정/publish 주기
- heartbeat OFF 판단 기준 시간

주의:
- logger는 MQTT 수신 즉시 DB에 저장
- 설정 탭의 주기는 DB 저장 주기가 아니라 sensor hub의 측정/publish 주기를 의미
- 측정 주기 변경은 sensor hub 설정에 반영되어야 함

## 8. 데이터 흐름

기본 흐름:

```text
sensor_hub -> MQTT -> logger -> monthly SQLite DB -> SFES Lab UI
SFES Lab UI -> MQTT command -> Arduino control node
Arduino control node -> MQTT state/heartbeat/RPM -> logger -> monthly SQLite DB
weather_service -> KMA hourly fetch at HH:01 -> MQTT -> logger -> monthly SQLite DB -> SFES Lab UI
```

supervisor/systemd가 함께 실행할 프로그램 후보:

- sensor hub
- MQTT logger
- weather service
- Arduino reset helper
- local MQTT broker 상태 확인 helper
- UI server
- kiosk browser launcher

UI 자체는 위 프로세스들을 직접 subprocess로 실행하지 않습니다.

## 9. 반응형 요구사항

기준 해상도는 `1280x800`입니다.

설계 원칙:

- 1280x800에서 모든 탭의 핵심 조작이 스크롤 없이 가능하도록 우선 설계
- 더 작은 화면에서는 탭 내부 영역을 세로 스크롤 허용
- 더 큰 화면에서는 카드/그래프 영역을 넓게 확장
- 버튼, 토글, 슬라이더는 터치 가능한 크기로 유지

## 10. 전체 화면 실행

운영 시 Raspberry Pi 브라우저는 전체 화면 또는 kiosk 모드로 실행합니다.

FastAPI UI 서버 실행:

```bash
cd /home/pi/smartfarm/smartfarm
uvicorn rpi.ui.server:app --host 127.0.0.1 --port 8000
```

Kiosk 브라우저 실행:

```bash
chromium-browser --kiosk http://127.0.0.1:8000
```

정확한 실행 명령은 Raspberry Pi OS와 설치된 브라우저에 맞춰 조정합니다.

## 11. 상태/에러 표시 권장사항

- Arduino online/offline 표시 권장
- 마지막 actuator state 수신 여부 표시 권장
- weather 데이터 미수신 시 경고 또는 빈 상태 표시 권장
- MQTT broker 연결 상태 표시 권장

## 12. 확인 필요

- 설정 탭의 저장 관련 주기는 실제로는 sensor hub 측정/publish 주기임
- UI는 화면만 담당하고 프로세스 실행/재시작은 supervisor/systemd가 담당
- supervisor와 systemd service 파일의 구체적인 분리는 구현 단계에서 설계 필요
