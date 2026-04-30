# Raspberry Pi Tests

이 디렉터리는 Raspberry Pi에서 센서, MQTT, GPIO, 서비스 흐름을 점검하기 위한 테스트 스크립트 모음입니다.
대부분은 `pytest` 단위테스트가 아니라 실기 bring-up용 수동 실행 스크립트입니다.
운영 계약은 `docs/` 문서를 우선합니다.

## 1. 테스트 현황

| 파일 | 상태 | 설명 |
|------|------|------|
| `sensors/test_ads1115_basic.py` | ✅ 구현 | ADS1115 단일 채널 raw/voltage 확인 |
| `sensors/test_temp_humidity_inputs.py` | ✅ 구현 | 온습도 센서 전압 → 온도/습도 변환 점검 |
| `sensors/test_co2_input.py` | ✅ 구현 | 4~20mA CO2 센서 전압 → ppm 변환 점검 |
| `sensors/test_soil_moisture_inputs.py` | ✅ 구현 | 토양수분 전압 모니터링 |
| `sensors/test_par_input.py` | ❌ placeholder | |
| `actuators/test_rpi_gpio_relay_reset.py` | ✅ 구현 | Arduino 리셋용 GPIO 릴레이 점검 |
| `actuators/test_mqtt_command_publish.py` | ❌ placeholder | |
| `integration/test_sensor_to_mqtt.py` | ✅ 구현 | ADS1115 → 로컬 MQTT smoke test (임시 raw topic) |
| `integration/test_mqtt_to_sqlite.py` | ❌ placeholder | |
| `integration/test_end_to_end_local.py` | ❌ placeholder | |
| `services/test_logger_write_sqlite.py` | ❌ placeholder | |
| `services/test_ui_db_read_latest.py` | ❌ placeholder | |
| `services/test_weather_kma_fetch.py` | ❌ placeholder | |

> 핀 번호·I2C 주소 등 하드웨어 세부사항은 [docs/pin-map.md](../../docs/pin-map.md) 확정 후 반영 예정

## 2. 실행 전 주의
- Raspberry Pi 실기 환경, I2C/GPIO 권한, 센서 연결 필요
- Python 의존성은 `rpi/requirements.txt` 기준
- 무한 루프 기반이므로 `Ctrl+C`로 종료
- 저위험 센서/릴레이부터 점검

## 3. 실행 예시
```bash
python rpi/tests/sensors/test_temp_humidity_inputs.py
python rpi/tests/actuators/test_rpi_gpio_relay_reset.py
```
