<!-- File: OWNER.md -->
# OWNER.md

이 문서는 "오너/운영자" 관점에서 꼭 알아야 할 사항을 짧게 정리한 문서입니다.
개발 상세는 `docs/` 문서를 참고하세요.

## 1. 먼저 읽을 문서
- [docs/repository-structure.md](docs/repository-structure.md)
- [docs/mqtt-topics.md](docs/mqtt-topics.md)
- [docs/ui-spec.md](docs/ui-spec.md)
- [docs/db-schema.md](docs/db-schema.md)
- [docs/arduino-firmware-spec.md](docs/arduino-firmware-spec.md)

## 2. 현재 시스템 운영 방향
- 온실 2동: `gh1`, `gh2`
- **gh1과 gh2는 MQTT 토픽만 다르고 코드는 동일** — 별도 코드 복제 금지
- MQTT 토픽은 온실별로 분리 (`sf/gh1/...`, `sf/gh2/...`)
- UI는 실시간 모니터링, 액추에이터 제어, 과거 추세 탭을 제공
- SQLite 저장은 UI와 분리된 logger 구조를 권장
- DB 구조는 `docs/db-schema.md` **초안**을 기준으로 계속 다듬는 중

## 3. 현재 합의된 중요한 결정
- AGENT.md는 짧게 유지하고 상세는 `docs/`로 분리
- 실시간 UI는 가능하면 MQTT 직접 구독보다 DB의 최신값을 읽어 표시
- Arduino는 다음을 publish
  - actuator state
  - heartbeat
  - fan RPM
- Arduino 재부팅은 MQTT가 아니라 Raspberry Pi GPIO + 릴레이로 수행
- UI는 각 탭별로 마지막 업데이트 시간 1개만 표시

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

## 6. 테스트 현황 요약
- RPi 테스트: 5개 구현 / 8개 placeholder
- Arduino 테스트: 7개 구현 / 6개 placeholder
- 상세 현황은 `rpi/tests/README.md`, `arduino/tests/README.md` 참고

## 7. 핀맵/배선
- 핀맵 문서: [docs/pin-map.md](docs/pin-map.md) (확정 후 작성 예정)

## 8. 요구사항이 바뀌면 어떻게 하나
- 먼저 관련 문서를 고칩니다.
  - UI: `docs/ui-spec.md`
  - DB: `docs/db-schema.md`
  - MQTT: `docs/mqtt-topics.md`
  - 펌웨어: `docs/arduino-firmware-spec.md`
  - 핀맵: `docs/pin-map.md`
  - 키 이름: `docs/naming-conventions.md`
- 그 다음 코드를 수정합니다.

## 9. 나중에 채워야 할 TODO
- 실제 Raspberry Pi 실행/배포 절차
- systemd 서비스 이름과 실행 커맨드
- DB 스키마 초안 검토 및 최종안 확정
- KMA API 설정값 정리
- 핀맵/배선도 확정 (`docs/pin-map.md`)

