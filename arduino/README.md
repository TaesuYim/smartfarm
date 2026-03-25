<!-- File: arduino/README.md -->
# Arduino 영역

이 디렉터리는 Arduino 제어 노드 펌웨어가 들어갈 위치입니다.
현재는 `control_node/` 폴더와 하드웨어 bring-up용 테스트 스케치를 함께 유지하는 상태입니다.

## 1. 이 디렉터리의 역할
- MQTT command 구독
- 팬, 히터, 펌프, 밸브, 창문, LED 제어
- actuator state publish
- heartbeat publish
- fan RPM publish

## 2. 현재 구조(요약)
```text
arduino/
├─ README.md
├─ control_node/
└─ tests/
```

## 3. 권장 설계 메모
- `gh1`, `gh2`용 별도 코드 복제는 피합니다.
- 같은 펌웨어 코드베이스를 사용하고, 온실 ID는 설정값으로 처리합니다.
- 토픽/키 구조는 반드시 docs 문서를 따릅니다.
- `tests/`의 스케치는 하드웨어 검증용이며, 최종 운영 펌웨어는 `control_node/`에 모으는 것을 권장합니다.
- 실제 핀 배치는 `docs/pin-map.md`를 기준으로 관리합니다.

## 4. TODO
- 빌드 도구 선택
  - Arduino IDE
  - PlatformIO
- 실제 배선도 문서
- RPM 측정 구현 방식 확정