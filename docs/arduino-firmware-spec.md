<!-- File: docs/arduino-firmware-spec.md -->
# Arduino Firmware Specification

대상 보드:
- Arduino UNO R4 WiFi

역할:
- MQTT 액추에이터 명령 구독
- 하드웨어 제어 수행
- actuator state publish
- heartbeat publish
- fan RPM publish

## 1. 토픽 연결

### 1.1 Subscribe
- `sf/<gh>/actuators/cmd`

### 1.2 Publish
- `sf/<gh>/actuators/state`
- `sf/<gh>/actuators/heartbeat`
- `sf/<gh>/actuators/fan-rpm`

### 1.3 온실 구분
- `<gh>`는 `gh1` 또는 `gh2`
- **gh1과 gh2는 동일한 펌웨어를 사용** — MQTT 토픽의 `<gh>` 부분만 설정으로 구분
- 온실별로 별도 코드를 만들지 않음

## 2. 액추에이터 제어 요구사항

### 2.1 PWM 제어
1. 환기팬 1
- 입력: `vent_fan_pwm_pct`
- 범위: `0..100`
- 출력: PWM duty `0..100%`
- 현재 테스트 기준 주파수: `20kHz`
- 최종 운영값은 펌웨어 통합 시 다시 확정 가능

2. 순환팬 2
- 입력:
  - `circ_fan_1_pwm_pct`
  - `circ_fan_2_pwm_pct`
- 범위: `0..100`
- 출력: PWM duty `0..100%`
- 현재 테스트 기준 주파수: `20kHz`
- 최종 운영값은 펌웨어 통합 시 다시 확정 가능

3. 히터 2
- 입력:
  - `heater_1_pwm_pct`
  - `heater_2_pwm_pct`
- 범위: `0..100`
- 출력: 2~5초 주기의 매우 느린 PWM
- 사실상 ON/OFF에 가까운 제어
- 현재 테스트 기준 윈도우: `5초`
- 구현 권장:
  - `delay()` 대신 `millis()` 기반 상태머신

4. 펌프 1
- 입력: `pump_pwm_pct`
- 범위: `0..100`
- 출력: PWM duty `0..100%`
- 초기 주파수: 기본값 사용 가능

### 2.2 ON/OFF 제어
1. 솔레노이드 밸브 7
- 입력:
  - `valve_pot_1_on`
  - `valve_pot_2_on`
  - `valve_pot_3_on`
  - `valve_pot_4_on`
  - `valve_pot_5_on`
  - `valve_pot_6_on`
  - `valve_fog_on`
- 동작:
  - `true` -> HIGH
  - `false` -> LOW

2. 초음파 미스트 1
- 입력: `mist_on`
- 동작:
  - `true` -> HIGH
  - `false` -> LOW

### 2.3 창문 개폐기 2
- 드라이버: L298N
- 기본 제어 개념은 방향 제어 2핀 + enable 1핀 구조를 권장
- 실제 핀 번호는 별도 핀맵 문서에서 확정
- 입력:
  - `window_1_cmd`
  - `window_2_cmd`
- 명령:
  - `open` -> `(1,0)`
  - `close` -> `(0,1)`
  - `stop` -> `(0,0)`

### 2.4 LED
- addressable LED strip
- 입력:
  - `led_r`
  - `led_g`
  - `led_b`
  - `led_brightness_pct`
- 현재 테스트 기준
  - `Adafruit_NeoPixel` 라이브러리 사용
  - WS2811 계열 addressable LED 방식으로 점검
- 실제 LED 모델, 색 순서, 개수는 최종 하드웨어 기준으로 다시 확정

## 3. Fan RPM 측정
- 측정 대상
  - 환기팬 1
  - 순환팬 2
- publish topic
  - `sf/<gh>/actuators/fan-rpm`

### 3.1 전기적 주의
- tach 출력은 오픈컬렉터/오픈드레인 가능성을 고려
- 적절한 pull-up 필요
- 12V로 pull-up되지 않도록 주의
- 입력 전압은 보드 허용 범위 내로 유지

### 3.2 측정 방식
- 인터럽트 기반 펄스 카운트 또는 주기 측정 방식 권장
- fan spec에 따른 PPR 값 확인 필요
- 측정 결과는 `vent_fan_rpm`, `circ_fan_1_rpm`, `circ_fan_2_rpm`로 publish

## 4. Heartbeat
- 주기적으로 `sf/<gh>/actuators/heartbeat` publish
- 최소 포함 필드
  - `ts`
  - `source`
  - `uptime_ms`

## 5. State Publish
- 명령 적용 후 `sf/<gh>/actuators/state` publish
- 최소 포함 필드
  - `ts`
  - `source`
  - `seq`
  - `result`
  - `errors`
  - `applied`

## 6. 안전 기본값(권장)
부팅 직후 또는 통신 불안정 시 기본적으로 아래 상태를 권장합니다.

- 팬 PWM = 0
- 히터 PWM = 0
- 펌프 PWM = 0
- 모든 밸브 OFF
- 미스트 OFF
- 창문 = stop
- LED OFF

## 7. 안전 보강 항목(권장)
- 히터가 켜질 때 대응 순환팬이 반드시 동작하도록 연동 검토
- fan RPM이 비정상일 때 heater 차단 로직 검토
- MQTT disconnect 시 안전 상태로 이동하는 정책 검토
- invalid command 수신 시 무시하고 error 상태 publish

## 8. TODO
- Wi-Fi/MQTT 재연결 전략
- LWT 사용 여부
- 핀맵/배선도 → [docs/pin-map.md](pin-map.md) 확정 후 작성
- `20kHz` fan PWM과 `5초` heater window를 운영 기본값으로 유지할지 최종 확정
- 실제 LED 모델(칩셋/색 순서/개수) 최종 확정
