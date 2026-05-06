<!-- File: OWNER.md -->
# OWNER.md

이 문서는 "오너/운영자" 관점에서 꼭 알아야 할 사항을 짧게 정리한 문서입니다.
개발 상세는 `docs/` 문서를 참고하세요.

## 1. 먼저 읽을 문서
- [docs/repository-structure.md](docs/repository-structure.md)
- [docs/mqtt-topics.md](docs/mqtt-topics.md)
- [docs/ui-spec.md](docs/ui-spec.md)
- [docs/db-schema.md](docs/db-schema.md)
- [docs/pin-map.md](docs/pin-map.md)
- [docs/arduino-firmware-spec.md](docs/arduino-firmware-spec.md)
- [docs/naming-conventions.md](docs/naming-conventions.md)
- [docs/json-schemas.md](docs/json-schemas.md)
- [docs/environment-config.md](docs/environment-config.md)

## 2. 현재 시스템 운영 방향
- 현재 구현/운용 온실: `GH1` (`gh1`)
- 향후 확장 온실: `GH2` (`gh2`)
- MQTT 토픽은 온실별로 반드시 분리하되 현재는 `sf/gh1/...`만 사용
- UI는 실시간 모니터링, 액추에이터 제어, 과거 추세 탭을 제공
- SQLite 저장은 UI와 분리된 logger 구조를 권장
- Arduino heartbeat는 logger가 감시하고 상태를 기록하는 방향을 권장
- DB는 월별 SQLite 파일(`smartfarm_YYYY_MM.sqlite3`)로 저장
- 핀 배치는 `docs/pin-map.md`를 기준으로 관리

## 3. 현재 합의된 중요한 결정
- 에이전트 규칙은 `.agents/rules/`에 분리하고 상세는 `docs/`로 분리
- 실시간 UI는 DB의 최신값을 읽어 표시
- UI는 FastAPI + 정적 HTML/CSS/바닐라 JavaScript로 구현
- 제어 UI는 slider/toggle/radio 변경 시 MQTT command를 즉시 publish
- Arduino는 다음을 publish
  - actuator state
  - heartbeat
  - fan RPM
- Arduino 재부팅은 Raspberry Pi GPIO + 릴레이로 수행
- UI는 각 탭별로 마지막 업데이트 시간 1개만 표시
- 기상청 데이터는 매시 1분에 정시 데이터를 요청하고, 받아온 시각도 DB에 저장
- 창문은 위치 센서가 없으므로 UI/backend 시작 시 닫힘 방향 5초 구동 후 `stop`하여 완전 닫힘 기준점을 보정

## 4. 센서/하드웨어 관련 메모
- ADS1115는 3.3V 기준으로 사용
- 1~5V 센서 출력은 분압 후 읽는 방향
- CO2 4~20mA는 150옴 저항으로 전압 변환
- PAR 센서의 최종 환산/게인은 실측 후 조정 예정
- 팬 RPM은 Arduino에서 읽고 MQTT로 publish

## 5. 운영상 주의
- 히터는 팬과 함께 안전하게 동작해야 함
- 창문 구동은 open/close/stop 신호가 동시에 충돌하지 않도록 점검
- Arduino 리셋 릴레이는 재부팅 루프가 되지 않도록 주의
- SQLite 파일은 정기 백업 권장

## 6. 요구사항이 바뀌면 어떻게 하나
- 먼저 관련 문서를 고칩니다.
  - UI 변경: `docs/ui-spec.md`
  - DB 변경: `docs/db-schema.md`
  - 핀맵 변경: `docs/pin-map.md`
  - MQTT 변경: `docs/mqtt-topics.md`
  - 펌웨어 변경: `docs/arduino-firmware-spec.md`
  - 키 이름 변경: `docs/naming-conventions.md`
- 그 다음 코드를 수정합니다.

## 7. 나중에 채워야 할 TODO
- 실제 Raspberry Pi 실행/배포 절차
- systemd 서비스 이름과 실행 커맨드
- KMA API 설정값 정리
- 실제 배선도 문서
