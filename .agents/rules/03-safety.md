<!-- File: .agents/rules/03-safety.md -->
# 하드웨어 안전 규칙

이 프로젝트는 히터, 모터, 펌프, 솔레노이드 밸브, 릴레이를 포함합니다.
하드웨어 안전과 관련된 변경은 반드시 아래 사항을 확인합니다.

## 필수 확인 항목
- 히터 기본값은 안전한 OFF 상태인가
- 팬/히터 연동 또는 안전 인터락에 문제가 없는가
- 펌프/밸브가 부팅 시 의도치 않게 켜지지 않는가
- 창문 제어에서 open/close가 동시에 활성화되지 않는가
- L298N 제어가 open/close/stop 규칙을 지키는가
- Arduino 리셋 릴레이 제어가 재부팅 루프를 만들지 않는가
- RPM 입력의 전압/pull-up 조건이 올바른가
- MQTT disconnect 또는 invalid command에서 안전 상태를 유지하는가

## PR 체크리스트
액추에이터 관련 변경 시 [.github/pull_request_template.md](.github/pull_request_template.md)의
하드웨어 안전 체크리스트를 **반드시** 확인합니다.
