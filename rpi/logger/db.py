import sqlite3
import json


CREATE_SENSOR_SNAPSHOT_TABLE_SQL = """
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
"""

CREATE_SENSOR_LATEST_TABLE_SQL = """
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
"""

CREATE_ADS_READING_TABLE_SQL = """
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
"""

CREATE_ACTUATOR_LATEST_TABLE_SQL = """
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
"""

CREATE_INDEXES_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_sensor_snapshot_gh_ts ON sensor_snapshot (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_ads_reading_source_ts ON ads_reading (source, ts)",
)

SENSOR_VALUE_COLUMNS = (
    "temp_pot_c",
    "hum_pot_pct",
    "temp_top_c",
    "hum_top_pct",
    "co2_ppm",
    "par_w_m2",
    "soil_moisture_1_pct",
    "soil_moisture_2_pct",
    "soil_moisture_3_pct",
    "soil_moisture_4_pct",
    "soil_moisture_5_pct",
    "soil_moisture_6_pct",
)


def connect_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.execute(CREATE_SENSOR_SNAPSHOT_TABLE_SQL)
    conn.execute(CREATE_SENSOR_LATEST_TABLE_SQL)
    conn.execute(CREATE_ADS_READING_TABLE_SQL)
    conn.execute(CREATE_ACTUATOR_LATEST_TABLE_SQL)
    # 액추에이터 이력 테이블도 생성 (필요시)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS actuator_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        greenhouse      TEXT    NOT NULL,
        ts              TEXT    NOT NULL,
        source          TEXT,
        payload         TEXT,
        received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours'))
    );
    """)
    for statement in CREATE_INDEXES_SQL:
        conn.execute(statement)
    conn.commit()


def insert_sensor_snapshot(conn, greenhouse, payload):
    columns = ("greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values = [greenhouse, payload["ts"], payload.get("source")]
    values.extend(payload.get(column) for column in SENSOR_VALUE_COLUMNS)

    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    cursor = conn.execute(
        f"INSERT INTO sensor_snapshot ({column_names}) VALUES ({placeholders})",
        values,
    )
    last_id = cursor.lastrowid

    # 최신값 전용 테이블 업데이트 (REPLACE INTO 사용)
    columns_latest = ("id", "greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values_latest = [last_id, greenhouse, payload["ts"], payload.get("source")]
    values_latest.extend(payload.get(column) for column in SENSOR_VALUE_COLUMNS)
    placeholders_latest = ", ".join("?" for _ in columns_latest)
    column_names_latest = ", ".join(columns_latest)

    conn.execute(
        f"REPLACE INTO sensor_latest ({column_names_latest}) VALUES ({placeholders_latest})",
        values_latest,
    )
    
    conn.commit()


def insert_ads_reading(conn, reading):
    conn.execute(
        """
        INSERT INTO ads_reading (source, address, channel, measurement, value)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            reading["source"],
            reading["address"],
            reading["channel"],
            reading["measurement"],
            reading["value"],
        ),
    )
    conn.commit()

def insert_actuator_state(conn, greenhouse, payload):
    # 1. 이력 저장
    conn.execute(
        "INSERT INTO actuator_history (greenhouse, ts, source, payload) VALUES (?, ?, ?, ?)",
        (greenhouse, payload.get("ts"), payload.get("source"), json.dumps(payload))
    )
    
    # 2. 최신 상태 업데이트
    # 아두이노가 보낸 'applied' 객체 내의 값을 추출
    applied = payload.get("applied", {})
    if not applied: return
    
    # 현재 테이블의 컬럼 목록 확인 (greenhouse, ts, source, seq, received_at 제외)
    fields = {
        "ts": payload.get("ts"),
        "source": payload.get("source"),
        "seq": payload.get("seq"),
        "vent_fan_pwm_pct": applied.get("vent_fan_pwm_pct"),
        "circ_fan_1_pwm_pct": applied.get("circ_fan_1_pwm_pct"),
        "circ_fan_2_pwm_pct": applied.get("circ_fan_2_pwm_pct"),
        "heater_1_pwm_pct": applied.get("heater_1_pwm_pct"),
        "heater_2_pwm_pct": applied.get("heater_2_pwm_pct"),
        "pump_pwm_pct": applied.get("pump_pwm_pct"),
        "mist_on": applied.get("mist_on"),
        "window_1_cmd": applied.get("window_1_cmd"),
        "window_2_cmd": applied.get("window_2_cmd"),
        "valve_pot_1_on": applied.get("valve_pot_1_on"),
        "valve_pot_2_on": applied.get("valve_pot_2_on"),
        "valve_pot_3_on": applied.get("valve_pot_3_on"),
        "valve_pot_4_on": applied.get("valve_pot_4_on"),
        "valve_pot_5_on": applied.get("valve_pot_5_on"),
        "valve_pot_6_on": applied.get("valve_pot_6_on"),
        "valve_fog_on": applied.get("valve_fog_on"),
        "led_r": applied.get("led_r"),
        "led_g": applied.get("led_g"),
        "led_b": applied.get("led_b"),
        "led_brightness_pct": applied.get("led_brightness_pct"),
        "shading_screen_cmd": applied.get("shading_screen_cmd")
    }
    
    # NULL이 아닌 값들만 업데이트하기 위해 동적 쿼리 생성
    # 하지만 REPLACE INTO를 쓰려면 전체 필드가 필요하므로, 기존 데이터를 가져와서 병합하는 것이 좋음
    existing = conn.execute("SELECT * FROM actuator_latest WHERE greenhouse = ?", (greenhouse,)).fetchone()
    
    if existing:
        # 기존 데이터와 병합 (새로 들어온 값이 None이 아니면 덮어씀)
        new_data = dict(existing)
        for k, v in fields.items():
            if v is not None:
                new_data[k] = v
    else:
        new_data = {"greenhouse": greenhouse}
        new_data.update(fields)
    
    cols = ", ".join(new_data.keys())
    placeholders = ", ".join("?" for _ in new_data)
    conn.execute(f"REPLACE INTO actuator_latest ({cols}) VALUES ({placeholders})", list(new_data.values()))
    
    conn.commit()
