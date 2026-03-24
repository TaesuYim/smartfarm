# Raspberry Pi Tests

이 디렉터리는 Raspberry Pi에서 센서, MQTT, GPIO, 서비스 흐름을 점검하기 위한 테스트 스크립트 모음입니다.
현재 파일명은 `test_*.py` 형식을 따르지만, 다수는 일반적인 `pytest` 단위테스트가 아니라 실기 bring-up용 수동 실행 스크립트입니다.

## 1. 현재 상태 요약
- 센서 입력 확인용 스크립트는 여러 개 작성되어 있음
- GPIO 릴레이 테스트 스크립트가 있음
- 서비스/통합/MQTT 일부는 아직 placeholder 상태임
- 운영 계약은 항상 `docs/` 문서를 우선하고, 테스트 스크립트는 bring-up 참고용으로 봅니다.

## 2. 센서 테스트
- `sensors/test_ads1115_basic.py`
  - ADS1115 단일 채널 raw/voltage 확인
- `sensors/test_temp_humidity_inputs.py`
  - 온습도 센서 입력과 변환식 점검
- `sensors/test_co2_input.py`
  - 4~20mA CO2 센서 전압 -> ppm 변환 점검
- `sensors/test_soil_moisture_inputs.py`
  - 토양수분 입력 전압 모니터링
- `sensors/test_par_input.py`
  - 아직 placeholder

## 3. 액추에이터/운영 테스트
- `actuators/test_rpi_gpio_relay_reset.py`
  - Arduino 리셋용 GPIO 릴레이 개별 점검
- `actuators/test_mqtt_command_publish.py`
  - 아직 placeholder

## 4. 서비스/통합 테스트
- `integration/test_sensor_to_mqtt.py`
  - ADS1115 값을 로컬 MQTT 브로커로 보내는 저수준 smoke test
  - 공식 계약 토픽 `sf/<gh>/...`가 아니라 임시 raw topic을 사용하므로, 문서 기준의 최종 MQTT 계약으로 보면 안 됨
- `integration/test_mqtt_to_sqlite.py`
  - 아직 placeholder
- `integration/test_end_to_end_local.py`
  - 아직 placeholder
- `services/test_logger_write_sqlite.py`
  - 아직 placeholder
- `services/test_ui_db_read_latest.py`
  - 아직 placeholder
- `services/test_weather_kma_fetch.py`
  - 아직 placeholder

## 5. 실행 전 주의
- Raspberry Pi 실기 환경, I2C/GPIO 권한, 센서 연결 상태가 필요합니다.
- Python 의존성은 상위 `rpi/requirements.txt`를 기준으로 맞춥니다.
- 무한 루프 기반 스크립트가 많으므로 `Ctrl+C`로 종료하는 형태를 전제로 합니다.
- 실제 하드웨어 연결은 저위험 센서/릴레이부터 점검하세요.

## 6. 실행 예시
```bash
python rpi/tests/sensors/test_temp_humidity_inputs.py
python rpi/tests/actuators/test_rpi_gpio_relay_reset.py
```
