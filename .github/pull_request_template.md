<!-- File: .github/pull_request_template.md -->
# 변경 요약
- 무엇을 변경했는지 적어주세요.
- 왜 변경했는지 적어주세요.

## 관련 문서
- [ ] AGENT.md 확인
- [ ] docs/mqtt-topics.md 확인
- [ ] docs/ui-spec.md 확인
- [ ] docs/arduino-firmware-spec.md 확인
- [ ] docs/naming-conventions.md 확인

## 이번 변경이 영향 주는 온실
- [ ] gh1
- [ ] gh2
- [ ] 둘 다
- [ ] 아직 미정

## 테스트 내용
- 어디서 테스트했나요?
  - [ ] 로컬
  - [ ] Raspberry Pi
  - [ ] Arduino 실기
  - [ ] MQTT 시뮬레이션만
- 테스트 방법:
- 결과:

## 문서 반영 여부
- [ ] MQTT 토픽/키가 바뀌면 docs/mqtt-topics.md를 수정했다
- [ ] UI 요구사항이 바뀌면 docs/ui-spec.md를 수정했다
- [ ] Arduino 동작이 바뀌면 docs/arduino-firmware-spec.md를 수정했다
- [ ] 네이밍이 바뀌면 docs/naming-conventions.md를 수정했다

## 하드웨어 안전 체크리스트
다음 항목은 액추에이터 관련 변경일 때 반드시 확인합니다.

- [ ] 히터 기본값은 안전한 OFF 상태인가
- [ ] 팬/히터 연동 또는 안전 인터락에 문제가 없는가
- [ ] 펌프/밸브가 부팅 시 의도치 않게 켜지지 않는가
- [ ] 창문 제어에서 open/close가 동시에 활성화되지 않는가
- [ ] L298N 제어가 open/close/stop 규칙을 지키는가
- [ ] Arduino 리셋 릴레이 제어가 재부팅 루프를 만들지 않는가
- [ ] RPM 입력의 전압/pull-up 조건을 확인했는가
- [ ] MQTT disconnect 또는 invalid command에서 안전 상태를 고려했는가

## 배포 메모
- [ ] Raspberry Pi 서비스 재시작 필요
- [ ] Arduino 펌웨어 업로드 필요
- [ ] 설정값 변경 필요
- [ ] DB 마이그레이션 필요 없음
- [ ] DB 마이그레이션 필요 있음

## 기타 메모
- 스크린샷, 로그, 시리얼 출력, MQTT 캡처 등이 있으면 적어주세요.