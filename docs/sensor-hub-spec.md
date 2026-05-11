<!-- File: docs/sensor-hub-spec.md -->
# Sensor Hub Specification

이 문서는 `rpi/sensor_hub/sensor_to_publish.py`가 수행하는 역할과 구현 상세를 정리합니다.
코드를 다시 작성할 때 이 문서를 기준으로 동일한 동작을 재현할 수 있도록 작성되었습니다.

## 1. 개요

Sensor Hub는 Raspberry Pi에 연결된 ADS1115 ADC 모듈에서 아날로그 센서값을 읽고, 전압을 물리량으로 변환한 뒤, MQTT로 완성형 `sensor_snapshot` payload를 주기적으로 발행하는 서비스입니다.

```text
ADS1115 (I2C) → 전압 읽기 → 노이즈 필터링 → 물리량 변환 → JSON payload 생성 → MQTT publish
```

## 2. 실행 방법

```bash
# 기본 실행
./rpi/.venv/bin/python rpi/sensor_hub/sensor_to_publish.py --gh gh1

# 발행 주기 변경 (초당 0.5회 = 2초 간격)
./rpi/.venv/bin/python rpi/sensor_hub/sensor_to_publish.py --rate 0.5

# 모듈 실행
python -m rpi.sensor_hub.sensor_to_publish
```

### CLI 인자

| 인자 | 기본값 | 설명 |
| --- | --- | --- |
| `--gh` | `gh1` | 온실 ID (현재 `gh1`만 지원) |
| `--host` | `127.0.0.1` | MQTT 브로커 호스트 |
| `--port` | `1883` | MQTT 브로커 포트 |
| `--rate` | `2.0` | 초당 발행 횟수 (기본 주기 = `1.0 / rate`) |

## 3. 의존성

### 외부 라이브러리

| 패키지 | 용도 |
| --- | --- |
| `paho-mqtt` | MQTT 클라이언트 (`paho.mqtt.client`) |
| `adafruit-circuitpython-ads1x15` | ADS1115 ADC 드라이버 |
| `adafruit-blinka` | `board`, `busio` 등 하드웨어 추상화 |

### 내부 모듈

| 모듈 | 용도 |
| --- | --- |
| `rpi.logger.db` | `DEFAULT_DB_DIR`, `monthly_db_path()`, `connect_db()`, `init_db()` — 월별 DB 경로 계산 및 `app_setting` 테이블에서 측정 주기 읽기 |

### 하드웨어 옵셔널 구조

하드웨어 라이브러리(`board`, `busio`, `adafruit_ads1x15`)는 `try/except`로 임포트하며, 임포트 실패 시 `HAS_HARDWARE = False`로 설정하여 하드웨어 없이도 프로그램이 종료되지 않습니다. 이 경우 모든 센서값은 `None`이 됩니다.

## 4. 초기화 순서

`main()` 함수 실행 시 아래 순서로 초기화합니다:

1. **CLI 인자 파싱** — `argparse`로 `--gh`, `--host`, `--port`, `--rate` 파싱
2. **MQTT 연결** — `paho.mqtt.client.Client(CallbackAPIVersion.VERSION2)` 생성 후 `connect()` 및 `loop_start()`
3. **데이터베이스 초기화** — `monthly_db_path()`로 현재 월 DB 파일 경로를 구하고, `connect_db()` + `init_db()`로 테이블 생성 (프로그램 시작 시 한 번만)
4. **I2C 버스 초기화** — `busio.I2C(board.SCL, board.SDA)`
5. **ADS1115 초기화** — 3개 주소(`0x4b`, `0x49`, `0x48`)에 대해 각각 `ADS1115` 객체 생성 및 4채널 `AnalogIn` 생성, `data_rate = 860` SPS 설정

## 5. ADS1115 채널 매핑

`docs/pin-map.md` 기준의 채널-센서 매핑입니다:

| ADS 주소 | 채널 | 센서 | payload 필드 | 변환 함수 |
| --- | --- | --- | --- | --- |
| `0x4b` | `A0` | 온도 하부 | `temp_pot_c` | `voltage_to_temp_c` |
| `0x4b` | `A1` | 습도 하부 | `hum_pot_pct` | `voltage_to_hum_pct` |
| `0x4b` | `A2` | 온도 상부 | `temp_top_c` | `voltage_to_temp_c` |
| `0x4b` | `A3` | 습도 상부 | `hum_top_pct` | `voltage_to_hum_pct` |
| `0x49` | `A0` | CO2 | `co2_ppm` | `voltage_to_co2_ppm` |
| `0x49` | `A1` | 조도(PAR) | `par_w_m2` | `voltage_to_par_w_m2` |
| `0x49` | `A2` | 토양수분1 | `soil_moisture_1_pct` | `voltage_to_soil_moisture_pct` |
| `0x49` | `A3` | 토양수분2 | `soil_moisture_2_pct` | `voltage_to_soil_moisture_pct` |
| `0x48` | `A0` | 토양수분3 | `soil_moisture_3_pct` | `voltage_to_soil_moisture_pct` |
| `0x48` | `A1` | 토양수분4 | `soil_moisture_4_pct` | `voltage_to_soil_moisture_pct` |
| `0x48` | `A2` | 토양수분5 | `soil_moisture_5_pct` | `voltage_to_soil_moisture_pct` |
| `0x48` | `A3` | 토양수분6 | `soil_moisture_6_pct` | `voltage_to_soil_moisture_pct` |

> **참고**: `0x4a` (spare) 주소는 현재 사용하지 않습니다.

## 6. 전압 → 물리량 변환

### 6.1 온도 (`voltage_to_temp_c`)

```text
기준: 0.66666667V = -20.0°C, 3.33333333V = 60°C
범위: -20.0°C ~ 60.0°C (전압 범위 2.66666667V)
```

계산식:
```python
v_adj = max(0, voltage - 0.66666667)
temp_c = (v_adj * (80 / 2.66666667)) - 20 + TEMP_OFFSET
```

### 6.2 습도 (`voltage_to_hum_pct`)

```text
기준: 0.66666667V = 0%, 3.33333333V = 100%
범위: 0% ~ 100% (clamp 적용)
```

계산 방식:
- **기본**: 2점 선형 보간 `(HUM_V_MIN, HUM_PCT_MIN)` ~ `(HUM_V_MIN + HUM_V_SPAN, HUM_PCT_MAX)`

### 6.3 CO2 (`voltage_to_co2_ppm`)

```text
기준: 0.6V = 0ppm, 3.0V = 2000ppm
범위: 0 ~ 2000 ppm
```

계산식:
```python
v_adj = max(0, voltage - 0.6)
co2_ppm = v_adj * (2000 / 2.4) 
```

### 6.4 PAR (`voltage_to_par_w_m2`)

현재 **임시 구현**: 전압값을 그대로 반환합니다 (소수점 4자리).

### 6.5 토양수분 (`voltage_to_soil_moisture_pct`)

현재 **임시 구현**: 전압값을 그대로 반환합니다 (소수점 4자리).

### 6.6 보정 상수 (offset)

각 변환 함수의 결과에 더해지며, 실측 보정 시 이 값을 조정합니다.


## 7. 측정 주기 관리

### 7.1 기본 주기

CLI 인자 `--rate`로 결정합니다: `default_period = 1.0 / rate` (기본 0.5초).

### 7.2 DB 기반 동적 주기

매 루프에서 `read_measurement_period_seconds()` 함수를 호출하여 `app_setting` 테이블의 `measurement_interval_sec` 값을 확인합니다.

- DB에 값이 있으면 해당 값을 주기로 사용 (최소 0.1초)
- DB에 값이 없거나 오류 시 `default_period` 사용
- **캐싱**: 5초 이내 재호출 시 캐시된 값을 반환하여 DB 부하를 줄임

### 8.3 루프 타이밍

```python
elapsed = time.time() - loop_start
period = read_measurement_period_seconds(default_period)
time.sleep(max(0, period - elapsed))
```

센서 읽기/필터링에 걸린 시간을 빼고 남은 시간만큼만 대기합니다.

## 9. MQTT 발행

### 9.1 토픽

```text
sf/{gh}/sensors/snapshot
```

기본값: `sf/gh1/sensors/snapshot`

### 9.2 payload 구조

```json
{
  "ts": "2026-05-08T17:00:00",
  "source": "rpi5_main",
  "temp_pot_c": 27.3,
  "hum_pot_pct": 55.2,
  "temp_top_c": 26.8,
  "hum_top_pct": 57.1,
  "co2_ppm": 820.0,
  "par_w_m2": 1.2345,
  "soil_moisture_1_pct": 1.5678,
  "soil_moisture_2_pct": 1.5432,
  "soil_moisture_3_pct": 1.4567,
  "soil_moisture_4_pct": 1.4321,
  "soil_moisture_5_pct": 1.3456,
  "soil_moisture_6_pct": 1.3210
}
```

- `ts`: YYYY-MM-DDTHH:MM:SS
- `source`: 고정 `"rpi5_main"`
- 센서 값: 해당 ADS1115이 초기화되지 않은 경우 `null`


## 10. 타임스탬프

```python
def now_kst():
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S")
```

KST(UTC+9) 기준, `YYYY-MM-DDTHH:MM:SS` 형식, 초 단위 정밀도. 타임존 접미사는 포함하지 않습니다.

## 11. 종료 처리

- `Ctrl+C` (`KeyboardInterrupt`)로 종료
- `finally` 블록에서 `client.loop_stop()` + `client.disconnect()` 호출

## 12. 주요 설계 결정 사항

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| ADS1115 data_rate | `860` SPS | 읽기 속도 향상 (기본 128 → 860) |
| DB 캐싱 | 5초 | DB 접근 빈도 최소화 |

> **참고**: UI 서버(`server.py`)는 `PRAGMA journal_mode=WAL`로 DB를 읽으므로, sensor_hub → mqtt_logger의 쓰기와 UI 읽기가 서로 블로킹하지 않습니다. 상세 내용은 [ui-spec.md](ui-spec.md) 섹션 12를 참조하세요.

## 13. 관련 문서

- [pin-map.md](pin-map.md) — ADS1115 채널-센서 물리 배선
- [mqtt-topics.md](mqtt-topics.md) — MQTT 토픽 구조 및 payload 계약
- [json-schemas.md](json-schemas.md) — sensor_snapshot JSON 스키마
- [db-schema.md](db-schema.md) — app_setting 테이블 및 sensor_snapshot 테이블 구조
- [naming-conventions.md](naming-conventions.md) — 필드 네이밍 규칙
- [environment-config.md](environment-config.md) — MQTT 브로커 및 네트워크 설정
- [repository-structure.md](repository-structure.md) — 프로젝트 구조에서 sensor_hub 위치
