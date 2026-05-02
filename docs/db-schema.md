<!-- File: docs/db-schema.md -->
# Database Schema

SQLite 기반 저장 구조를 정의합니다. 현재 구현/운용 대상은 `GH1` 1동이며, `GH2`는 향후 확장 대상으로만 둡니다.

## 1. DB 파일 정책

DB는 월별 파일로 분리합니다.

```text
smartfarm_YYYY_MM.sqlite3
```

예시:

```text
smartfarm_2026_05.sqlite3
smartfarm_2026_06.sqlite3
```

운영 규칙:

- logger는 현재 날짜 기준 월별 DB 파일을 선택해서 저장합니다.
- 월이 바뀌면 logger는 새 월별 DB 파일을 생성하고 이후 메시지를 새 파일에 저장합니다.
- UI는 기본적으로 현재 월 DB를 읽습니다.
- 월별 DB 디렉터리는 실행 옵션 `--db-dir`로 지정합니다.
- 호환/디버깅용으로 단일 파일을 쓰고 싶을 때는 `--db`를 사용할 수 있습니다.

## 2. 공통 규칙

- DB engine: SQLite 3
- 현재 저장되는 `greenhouse` 값은 `gh1`입니다.
- timestamp는 ISO 8601 문자열을 사용합니다.
- JSON key와 DB column은 `lower_snake_case`를 사용합니다.
- logger는 MQTT 메시지를 수신하는 즉시 저장합니다.
- `measurement_interval_sec`는 DB 저장 주기가 아니라 sensor hub 측정/publish 주기입니다.

## 3. 테이블 목록

| 테이블 | MQTT topic | 목적 |
| --- | --- | --- |
| `sensor_snapshot` | `sf/gh1/sensors/snapshot` | 센서 완성형 스냅샷 이력 |
| `sensor_latest` | 없음 | 센서 최신값 1행, UI 조회용 |
| `weather` | `sf/gh1/sensors/weather` | 기상청 및 내부 온습도 결합 이력 |
| `actuator_cmd` | `sf/gh1/actuators/cmd` | UI에서 발행한 제어 명령 |
| `actuator_history` | `sf/gh1/actuators/state` | Arduino 적용 상태 이력 |
| `actuator_latest` | 없음 | actuator 최신 상태 1행, UI 조회용 |
| `heartbeat` | `sf/gh1/actuators/heartbeat` | Arduino 생존 신호 |
| `fan_rpm` | `sf/gh1/actuators/fan-rpm` | 팬 RPM |
| `app_setting` | 없음 | UI/측정 주기 설정 |
| `ads_reading` | raw ADS debug topics | ADS 디버깅 로그 |

## 4. `sensor_snapshot`

ADS1115 값을 변환한 내부 센서 스냅샷입니다.

```sql
CREATE TABLE IF NOT EXISTS sensor_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL,
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),

    temp_pot_c              REAL,
    hum_pot_pct             REAL,
    temp_top_c              REAL,
    hum_top_pct             REAL,
    co2_ppm                 REAL,
    par_w_m2                REAL,
    soil_moisture_1_pct     REAL,
    soil_moisture_2_pct     REAL,
    soil_moisture_3_pct     REAL,
    soil_moisture_4_pct     REAL,
    soil_moisture_5_pct     REAL,
    soil_moisture_6_pct     REAL
);
```

## 5. `weather`

기상청 정보는 1시간에 한 번 받아옵니다. 정시 데이터는 해당 정시의 1분에 요청합니다. 예를 들어 `01:00` 데이터는 `01:01`에 요청합니다.

`ts`는 관측 데이터 시각이고, `fetched_at`은 실제로 기상청 정보를 받아온 시각입니다.

저장 필드:

- `internal_temp_c`: 내부온도
- `internal_hum_pct`: 내부습도
- `ta`: 외기온도
- `hm`: 외부습도
- `rn`: 강수
- `ws`: 풍속
- `icsr`: 일사
- `ss`: 일조
- `qc_flags`: QC 플래그 JSON 문자열

```sql
CREATE TABLE IF NOT EXISTS weather (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    fetched_at      TEXT    NOT NULL,
    source          TEXT    NOT NULL DEFAULT 'kma',
    station_id      TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),

    internal_temp_c     REAL,
    internal_hum_pct    REAL,
    ta                  REAL,
    hm                  REAL,
    rn                  REAL,
    ws                  REAL,
    icsr                REAL,
    ss                  REAL,
    qc_flags            TEXT,
    payload             TEXT
);
```

인터넷 또는 KMA API 실패 시 row를 만들지 않거나 일부 값을 `NULL`로 저장합니다. UI는 실패를 치명 오류로 처리하지 않고 빈 값으로 표시합니다.

## 6. `actuator_cmd`

UI에서 제어값이 변경될 때 저장합니다. payload에는 변경된 일부 key만 포함될 수 있습니다.

```sql
CREATE TABLE IF NOT EXISTS actuator_cmd (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    source          TEXT    NOT NULL DEFAULT 'ui',
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    seq             INTEGER,

    vent_fan_pwm_pct        INTEGER,
    circ_fan_1_pwm_pct      INTEGER,
    circ_fan_2_pwm_pct      INTEGER,
    heater_1_pwm_pct        INTEGER,
    heater_2_pwm_pct        INTEGER,
    pump_pwm_pct            INTEGER,
    valve_pot_1_on          INTEGER,
    valve_pot_2_on          INTEGER,
    valve_pot_3_on          INTEGER,
    valve_pot_4_on          INTEGER,
    valve_pot_5_on          INTEGER,
    valve_pot_6_on          INTEGER,
    valve_fog_on            INTEGER,
    mist_on                 INTEGER,
    window_1_cmd            TEXT,
    window_2_cmd            TEXT,
    shading_screen_cmd      TEXT,
    led_r                   INTEGER,
    led_g                   INTEGER,
    led_b                   INTEGER,
    led_brightness_pct      INTEGER
);
```

## 7. `actuator_history`

Arduino가 실제 적용한 결과의 이력을 저장합니다. MQTT payload 전체를 JSON 문자열로 보관합니다.

```sql
CREATE TABLE IF NOT EXISTS actuator_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL,
    ts              TEXT    NOT NULL,
    source          TEXT,
    payload         TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours'))
);
```

## 8. `heartbeat`

UI의 online/offline 판단에 사용합니다.

```sql
CREATE TABLE IF NOT EXISTS heartbeat (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    uptime_ms       INTEGER
);
```

## 9. `fan_rpm`

```sql
CREATE TABLE IF NOT EXISTS fan_rpm (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),

    vent_fan_rpm        INTEGER,
    circ_fan_1_rpm      INTEGER,
    circ_fan_2_rpm      INTEGER
);
```

## 10. 최신값 테이블

`sensor_latest`와 `actuator_latest`는 UI 조회 속도를 위해 greenhouse당 1행만 유지합니다.

```sql
CREATE TABLE IF NOT EXISTS sensor_latest (
    greenhouse      TEXT    PRIMARY KEY,
    id              INTEGER,
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    temp_pot_c      REAL,
    hum_pot_pct     REAL,
    temp_top_c      REAL,
    hum_top_pct     REAL,
    co2_ppm         REAL,
    par_w_m2        REAL,
    soil_moisture_1_pct REAL,
    soil_moisture_2_pct REAL,
    soil_moisture_3_pct REAL,
    soil_moisture_4_pct REAL,
    soil_moisture_5_pct REAL,
    soil_moisture_6_pct REAL
);
```

```sql
CREATE TABLE IF NOT EXISTS actuator_latest (
    greenhouse      TEXT    PRIMARY KEY,
    ts              TEXT    NOT NULL,
    source          TEXT,
    seq             INTEGER,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    vent_fan_pwm_pct        INTEGER,
    circ_fan_1_pwm_pct      INTEGER,
    circ_fan_2_pwm_pct      INTEGER,
    heater_1_pwm_pct        INTEGER,
    heater_2_pwm_pct        INTEGER,
    pump_pwm_pct            INTEGER,
    valve_pot_1_on          INTEGER,
    valve_pot_2_on          INTEGER,
    valve_pot_3_on          INTEGER,
    valve_pot_4_on          INTEGER,
    valve_pot_5_on          INTEGER,
    valve_pot_6_on          INTEGER,
    valve_fog_on            INTEGER,
    mist_on                 INTEGER,
    window_1_cmd            TEXT,
    window_2_cmd            TEXT,
    shading_screen_cmd      TEXT,
    led_r                   INTEGER,
    led_g                   INTEGER,
    led_b                   INTEGER,
    led_brightness_pct      INTEGER
);
```

## 11. `app_setting`

```sql
CREATE TABLE IF NOT EXISTS app_setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours'))
);
```

권장 초기값:

| key | 예시값 | 설명 |
| --- | --- | --- |
| `ui_refresh_sec` | `5` | 화면 업데이트 주기 |
| `measurement_interval_sec` | `1` | sensor hub 측정/publish 주기 |
| `heartbeat_timeout_sec` | `10` | heartbeat OFF 판단 기준 |
| `weather_fetch_minute` | `1` | 매시 1분 기상청 요청 |
| `monitoring_graph_minutes` | `60` | 모니터링 탭 기본 그래프 기간 |

## 12. `ads_reading`

ADS raw/voltage 디버깅 값 저장용 테이블입니다. 운영 UI는 기본적으로 이 테이블이 아니라 `sensor_snapshot`을 사용합니다.

```sql
CREATE TABLE IF NOT EXISTS ads_reading (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    source          TEXT    NOT NULL,
    address         TEXT    NOT NULL,
    channel         TEXT    NOT NULL,
    measurement     TEXT    NOT NULL,
    value           REAL    NOT NULL,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours'))
);
```

## 13. 인덱스

```sql
CREATE INDEX IF NOT EXISTS idx_sensor_snapshot_gh_ts
    ON sensor_snapshot (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_weather_gh_ts
    ON weather (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_weather_fetched_at
    ON weather (fetched_at);

CREATE INDEX IF NOT EXISTS idx_actuator_cmd_gh_ts
    ON actuator_cmd (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_actuator_history_gh_ts
    ON actuator_history (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_heartbeat_gh_ts
    ON heartbeat (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_fan_rpm_gh_ts
    ON fan_rpm (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_ads_reading_addr_channel_ts
    ON ads_reading (address, channel, ts);
```

## 14. 보존 정책 권장

| 테이블 | 권장 보존 기간 | 비고 |
| --- | --- | --- |
| `sensor_snapshot` | 90일 이상 | 과거 추세용 |
| `sensor_latest` | 항상 유지 | greenhouse당 1행 |
| `weather` | 90일 이상 | 내부/외부 환경 비교 |
| `actuator_cmd` | 30일 이상 | 디버깅/감사용 |
| `actuator_history` | 30일 이상 | 디버깅/감사용 |
| `actuator_latest` | 항상 유지 | greenhouse당 1행 |
| `heartbeat` | 7일 이상 | online 판단용 |
| `fan_rpm` | 30일 이상 | 모니터링용 |
| `ads_reading` | 짧게 또는 선택 저장 | 디버깅용 |

## 15. 확인 필요

- 월을 넘는 그래프 조회 시 여러 SQLite 파일을 동시에 조회하는 방식
- `ads_reading`을 운영 배포 후에도 유지할지 여부
- DB 파일 백업/보존 위치
