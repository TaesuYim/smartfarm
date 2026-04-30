<!-- File: docs/db-schema.md -->
# Database Schema

SQLite 기반 저장 구조를 정의합니다. 현재 운용 대상은 `GH1`만 사용합니다.

## 1. DB 파일 정책

DB는 월별로 분리합니다.

파일명 규칙:

```text
smartfarm_YYYY_MM.sqlite3
```

예시:

```text
smartfarm_2026_04.sqlite3
smartfarm_2026_05.sqlite3
```

운영 규칙:

- logger는 현재 날짜 기준 월별 DB 파일을 선택해서 저장
- 월이 바뀌면 새 DB 파일을 생성
- UI는 기본적으로 현재 월 DB를 읽음
- 그래프 탭에서 기간이 여러 월을 넘으면 여러 DB 파일을 조회할 수 있어야 함
- 월별 DB 위치는 설정 파일 또는 실행 옵션으로 지정

## 2. 공통 규칙

- DB engine: SQLite 3
- `greenhouse` 값은 현재 `gh1`만 사용
- timestamp는 ISO 8601 형식 사용
- JSON key와 DB column은 `lower_snake_case`
- 제어값 변경과 센서값 저장은 모두 DB에 기록
- logger는 MQTT 수신 즉시 저장
- `measurement_interval_sec`는 DB 저장 주기가 아니라 sensor hub 측정/publish 주기

## 3. 테이블 목록

| 테이블 | MQTT topic | 목적 |
| --- | --- | --- |
| `sensor_snapshot` | `sf/gh1/sensors/snapshot` | 센서 완성형 스냅샷 (이력) |
| `sensor_latest` | 없음 (logger가 관리) | 센서 최신값 1행 (UI 조회용) |
| `weather` | `sf/gh1/sensors/weather` | 외부 날씨 정보 |
| `actuator_cmd` | `sf/gh1/actuators/cmd` | UI에서 보낸 제어 명령 |
| `actuator_history` | `sf/gh1/actuators/state` | Arduino 적용 상태 이력 (JSON payload 전체 저장) |
| `actuator_latest` | 없음 (logger가 관리) | actuator 최신 상태 1행 (UI 조회용) |
| `heartbeat` | `sf/gh1/actuators/heartbeat` | Arduino 생존 신호 |
| `fan_rpm` | `sf/gh1/actuators/fan-rpm` | 팬 RPM |
| `app_setting` | 없음 | UI/측정 주기 설정 |
| `ads_reading` | raw ADS debug topics | ADS 디버깅 로그 |

## 4. ADS 채널 구성

물리 ADS 입력은 ADS1115 4개, 총 16채널을 사용합니다.

| ADS address | Channel | 용도 |
| --- | --- | --- |
| `0x48` | `A0`..`A3` | sensor input |
| `0x49` | `A0`..`A3` | sensor input |
| `0x4a` | `A0`..`A3` | spare |
| `0x4b` | `A0`..`A3` | sensor input |

운영 UI는 `sensor_snapshot`의 완성형 센서값만 표시합니다. `0x4a`의 4개 spare 채널은 현재 운영 화면에 표시하지 않고, 향후 센서 추가를 위해 비워둡니다.

raw ADS 디버깅 값이 필요하면 별도 `ads_reading` 테이블 또는 로그로 보관할 수 있습니다.

## 5. `sensor_snapshot`

```sql
CREATE TABLE IF NOT EXISTS sensor_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
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

## 6. `weather`

인터넷 또는 weather API 실패 시 row를 만들지 않거나 값을 `NULL`로 저장합니다. UI는 실패를 오류로 처리하지 않고 빈 값으로 표시합니다.

```sql
CREATE TABLE IF NOT EXISTS weather (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),

    region              TEXT,
    outdoor_temp_c      REAL,
    outdoor_hum_pct     REAL
);
```

## 7. `actuator_cmd`

UI에서 제어값이 변경될 때 저장합니다.

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

    valve_pot_1_on      INTEGER,
    valve_pot_2_on      INTEGER,
    valve_pot_3_on      INTEGER,
    valve_pot_4_on      INTEGER,
    valve_pot_5_on      INTEGER,
    valve_pot_6_on      INTEGER,
    valve_fog_on        INTEGER,
    mist_on             INTEGER,

    window_1_cmd    TEXT,
    window_2_cmd    TEXT,
    shading_screen_cmd  TEXT,

    led_r               INTEGER,
    led_g               INTEGER,
    led_b               INTEGER,
    led_brightness_pct  INTEGER
);
```

## 8. `actuator_history`

Arduino가 실제 적용한 결과의 이력을 저장합니다. MQTT payload 전체를 JSON 문자열로 저장합니다.

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

## 9. `heartbeat`

UI의 LED 상태 판단에 사용합니다.

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

## 10. `fan_rpm`

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

## 11. `app_setting`

UI 설정 탭에서 조정한 값을 저장합니다.

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
| `monitoring_graph_minutes` | `30` | 모니터링 탭 기본 그래프 기간 |

## 12. `ads_reading`

ADS raw/voltage 디버깅 값 저장용 테이블입니다.

```sql
CREATE TABLE IF NOT EXISTS ads_reading (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    ads_address     TEXT    NOT NULL,
    channel         TEXT    NOT NULL,
    kind            TEXT    NOT NULL,
    value           REAL    NOT NULL
);
```

## 13. 인덱스

```sql
CREATE INDEX IF NOT EXISTS idx_sensor_snapshot_gh_ts
    ON sensor_snapshot (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_weather_gh_ts
    ON weather (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_actuator_cmd_gh_ts
    ON actuator_cmd (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_actuator_state_gh_ts
    ON actuator_state (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_heartbeat_gh_ts
    ON heartbeat (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_fan_rpm_gh_ts
    ON fan_rpm (greenhouse, ts);

CREATE INDEX IF NOT EXISTS idx_ads_reading_addr_channel_ts
    ON ads_reading (ads_address, channel, ts);
```

## 14. 최신값 전용 테이블

UI에서 최신값을 빠르게 조회하기 위해 별도 테이블을 사용합니다. logger가 이력 테이블에 INSERT할 때 동시에 `REPLACE INTO`로 최신값 테이블을 갱신합니다. UI는 이 테이블만 읽습니다.

### `sensor_latest`

greenhouse당 1행만 유지됩니다. `sensor_snapshot`에 새 row가 들어올 때 logger가 함께 갱신합니다.

```sql
CREATE TABLE IF NOT EXISTS sensor_latest (
    greenhouse      TEXT    PRIMARY KEY,
    id              INTEGER,
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

### `actuator_latest`

greenhouse당 1행만 유지됩니다. `actuator_history`에 새 row가 들어올 때 logger가 `applied` 내부 값을 풀어서 기존 행과 병합(merge)한 뒤 갱신합니다. 새로 들어온 값이 `null`이 아닌 필드만 덮어씁니다.

```sql
CREATE TABLE IF NOT EXISTS actuator_latest (
    greenhouse      TEXT    PRIMARY KEY,
    ts              TEXT    NOT NULL,
    source          TEXT,
    seq             INTEGER,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),

    vent_fan_pwm_pct     INTEGER,
    circ_fan_1_pwm_pct   INTEGER,
    circ_fan_2_pwm_pct   INTEGER,
    heater_1_pwm_pct     INTEGER,
    heater_2_pwm_pct     INTEGER,
    pump_pwm_pct         INTEGER,
    mist_on              BOOLEAN,
    window_1_cmd         TEXT,
    window_2_cmd         TEXT,
    valve_pot_1_on       BOOLEAN,
    valve_pot_2_on       BOOLEAN,
    valve_pot_3_on       BOOLEAN,
    valve_pot_4_on       BOOLEAN,
    valve_pot_5_on       BOOLEAN,
    valve_pot_6_on       BOOLEAN,
    valve_fog_on         BOOLEAN,
    led_r                INTEGER,
    led_g                INTEGER,
    led_b                INTEGER,
    led_brightness_pct   INTEGER,
    shading_screen_cmd   TEXT
);
```

## 15. 보존 정책 권장

| 테이블 | 권장 보존 기간 | 비고 |
| --- | --- | --- |
| `sensor_snapshot` | 90일 이상 | 과거 추세용 |
| `sensor_latest` | 항상 유지 | greenhouse당 1행, 삭제 불필요 |
| `weather` | 90일 이상 | 과거 추세용 |
| `actuator_cmd` | 30일 이상 | 디버깅/감사용 |
| `actuator_history` | 30일 이상 | 디버깅/감사용 |
| `actuator_latest` | 항상 유지 | greenhouse당 1행, 삭제 불필요 |
| `heartbeat` | 7일 이상 | online 판단용 |
| `fan_rpm` | 30일 이상 | 모니터링용 |
| `ads_reading` | 짧게 또는 선택 저장 | 디버깅용 |

## 16. 확인 필요

- 월을 넘는 그래프 조회 시 여러 SQLite 파일을 동시에 조회하는 방식 구현 필요
- `ads_reading`을 운영 배포 후에도 유지할지 결정 필요
- DB 파일 경로와 백업 전략 확정 필요
