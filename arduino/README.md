<!-- File: arduino/README.md -->
# Arduino 영역

이 디렉터리는 Arduino 제어 노드 펌웨어가 들어갈 위치입니다.
현재는 최소 구조만 유지하고, 구현이 시작되면 실제 펌웨어 프로젝트를 생성합니다.

## 1. 이 디렉터리의 역할
- MQTT command 구독
- 팬, 히터, 펌프, 밸브, 창문, LED 제어
- actuator state publish
- heartbeat publish
- fan RPM publish

## 2. 나중에 추가될 수 있는 하위 구조(권장)
```text
arduino/
├─ README.md
└─ control_node/
```

`control_node/`는 Arduino IDE 프로젝트 또는 PlatformIO 프로젝트가 될 수 있습니다.

## 3. 권장 설계 메모
- `gh1`, `gh2`용 별도 코드 복제는 피합니다.
- 같은 펌웨어 코드베이스를 사용하고, 온실 ID는 설정값으로 처리합니다.
- 토픽/키 구조는 반드시 docs 문서를 따릅니다.

## 4. TODO
- 빌드 도구 선택
  - Arduino IDE
  - PlatformIO
- 실제 핀맵 확정
- RPM 측정 구현 방식 확정