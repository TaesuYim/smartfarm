import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


KST = timezone(timedelta(hours=9))
DEFAULT_DB_DIR = "data"
DB_FILENAME_PREFIX = "smartfarm"


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

ACTUATOR_VALUE_COLUMNS = (
    "vent_fan_pwm_pct",
    "circ_fan_1_pwm_pct",
    "circ_fan_2_pwm_pct",
    "heater_1_pwm_pct",
    "heater_2_pwm_pct",
    "pump_pwm_pct",
    "valve_pot_1_on",
    "valve_pot_2_on",
    "valve_pot_3_on",
    "valve_pot_4_on",
    "valve_pot_5_on",
    "valve_pot_6_on",
    "valve_fog_on",
    "mist_on",
    "window_1_cmd",
    "window_2_cmd",
    "shading_screen_cmd",
    "led_r",
    "led_g",
    "led_b",
    "led_brightness_pct",
)

WEATHER_VALUE_COLUMNS = (
    "internal_temp_c",
    "internal_hum_pct",
    "ta",
    "hm",
    "rn",
    "ws",
    "icsr",
    "ss",
)


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

CREATE_WEATHER_TABLE_SQL = """
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
"""

CREATE_ACTUATOR_CMD_TABLE_SQL = """
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
"""

CREATE_ACTUATOR_HISTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS actuator_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL,
    ts              TEXT    NOT NULL,
    source          TEXT,
    payload         TEXT,
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

CREATE_HEARTBEAT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS heartbeat (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    greenhouse      TEXT    NOT NULL DEFAULT 'gh1',
    ts              TEXT    NOT NULL,
    source          TEXT,
    received_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours')),
    uptime_ms       INTEGER
);
"""

CREATE_FAN_RPM_TABLE_SQL = """
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
"""

CREATE_APP_SETTING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+09:00', 'now', '+9 hours'))
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

CREATE_INDEXES_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_sensor_snapshot_gh_ts ON sensor_snapshot (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_weather_gh_ts ON weather (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_weather_fetched_at ON weather (fetched_at)",
    "CREATE INDEX IF NOT EXISTS idx_actuator_cmd_gh_ts ON actuator_cmd (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_actuator_history_gh_ts ON actuator_history (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_heartbeat_gh_ts ON heartbeat (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_fan_rpm_gh_ts ON fan_rpm (greenhouse, ts)",
    "CREATE INDEX IF NOT EXISTS idx_ads_reading_addr_channel_ts ON ads_reading (address, channel, ts)",
)


def now_kst_iso():
    return datetime.now(KST).isoformat(timespec="seconds")


def monthly_db_path(db_dir=DEFAULT_DB_DIR, now=None):
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    else:
        current = current.astimezone(KST)
    return Path(db_dir) / f"{DB_FILENAME_PREFIX}_{current.year:04d}_{current.month:02d}.sqlite3"


def connect_db(db_path):
    db_path = Path(db_path)
    if str(db_path) != ":memory:" and db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.execute(CREATE_SENSOR_SNAPSHOT_TABLE_SQL)
    conn.execute(CREATE_SENSOR_LATEST_TABLE_SQL)
    conn.execute(CREATE_WEATHER_TABLE_SQL)
    conn.execute(CREATE_ACTUATOR_CMD_TABLE_SQL)
    conn.execute(CREATE_ACTUATOR_HISTORY_TABLE_SQL)
    conn.execute(CREATE_ACTUATOR_LATEST_TABLE_SQL)
    conn.execute(CREATE_HEARTBEAT_TABLE_SQL)
    conn.execute(CREATE_FAN_RPM_TABLE_SQL)
    conn.execute(CREATE_APP_SETTING_TABLE_SQL)
    conn.execute(CREATE_ADS_READING_TABLE_SQL)
    for statement in CREATE_INDEXES_SQL:
        conn.execute(statement)
    conn.commit()


def _insert_row(conn, table, columns, values):
    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)
    return conn.execute(
        f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})",
        values,
    )


def _json_or_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def insert_sensor_snapshot(conn, greenhouse, payload):
    ts = payload.get("ts") or now_kst_iso()
    columns = ("greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values = [greenhouse, ts, payload.get("source")]
    values.extend(payload.get(column) for column in SENSOR_VALUE_COLUMNS)

    cursor = _insert_row(conn, "sensor_snapshot", columns, values)
    last_id = cursor.lastrowid

    columns_latest = ("id", "greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values_latest = [last_id, greenhouse, ts, payload.get("source")]
    values_latest.extend(payload.get(column) for column in SENSOR_VALUE_COLUMNS)
    placeholders_latest = ", ".join("?" for _ in columns_latest)
    column_names_latest = ", ".join(columns_latest)

    conn.execute(
        f"REPLACE INTO sensor_latest ({column_names_latest}) VALUES ({placeholders_latest})",
        values_latest,
    )
    conn.commit()


def insert_weather(conn, greenhouse, payload):
    ts = payload.get("ts") or payload.get("observed_at") or now_kst_iso()
    fetched_at = payload.get("fetched_at") or payload.get("requested_at") or now_kst_iso()
    columns = (
        "greenhouse",
        "ts",
        "fetched_at",
        "source",
        "station_id",
        *WEATHER_VALUE_COLUMNS,
        "qc_flags",
        "payload",
    )
    values = [
        greenhouse,
        ts,
        fetched_at,
        payload.get("source") or "kma",
        payload.get("station_id") or payload.get("stn"),
    ]
    values.extend(payload.get(column) for column in WEATHER_VALUE_COLUMNS)
    values.extend(
        [
            _json_or_text(payload.get("qc_flags")),
            json.dumps(payload, ensure_ascii=False),
        ]
    )
    _insert_row(conn, "weather", columns, values)
    conn.commit()


def insert_actuator_cmd(conn, greenhouse, payload):
    ts = payload.get("ts") or now_kst_iso()
    columns = ("greenhouse", "ts", "source", "seq", *ACTUATOR_VALUE_COLUMNS)
    values = [greenhouse, ts, payload.get("source") or "ui", payload.get("seq")]
    values.extend(payload.get(column) for column in ACTUATOR_VALUE_COLUMNS)
    _insert_row(conn, "actuator_cmd", columns, values)
    conn.commit()


def insert_actuator_state(conn, greenhouse, payload):
    ts = payload.get("ts") or now_kst_iso()
    conn.execute(
        "INSERT INTO actuator_history (greenhouse, ts, source, payload) VALUES (?, ?, ?, ?)",
        (greenhouse, ts, payload.get("source"), json.dumps(payload, ensure_ascii=False)),
    )

    applied = payload.get("applied", {})
    if not applied:
        conn.commit()
        return

    fields = {
        "ts": ts,
        "source": payload.get("source"),
        "seq": payload.get("seq"),
    }
    fields.update({column: applied.get(column) for column in ACTUATOR_VALUE_COLUMNS})

    existing = conn.execute(
        "SELECT * FROM actuator_latest WHERE greenhouse = ?",
        (greenhouse,),
    ).fetchone()

    if existing:
        new_data = dict(existing)
        for key, value in fields.items():
            if value is not None:
                new_data[key] = value
    else:
        new_data = {"greenhouse": greenhouse}
        new_data.update(fields)

    cols = ", ".join(new_data.keys())
    placeholders = ", ".join("?" for _ in new_data)
    conn.execute(
        f"REPLACE INTO actuator_latest ({cols}) VALUES ({placeholders})",
        list(new_data.values()),
    )
    conn.commit()


def insert_heartbeat(conn, greenhouse, payload):
    columns = ("greenhouse", "ts", "source", "uptime_ms")
    values = [
        greenhouse,
        payload.get("ts") or now_kst_iso(),
        payload.get("source"),
        payload.get("uptime_ms"),
    ]
    _insert_row(conn, "heartbeat", columns, values)
    conn.commit()


def insert_fan_rpm(conn, greenhouse, payload):
    columns = (
        "greenhouse",
        "ts",
        "source",
        "vent_fan_rpm",
        "circ_fan_1_rpm",
        "circ_fan_2_rpm",
    )
    values = [
        greenhouse,
        payload.get("ts") or now_kst_iso(),
        payload.get("source"),
        payload.get("vent_fan_rpm"),
        payload.get("circ_fan_1_rpm"),
        payload.get("circ_fan_2_rpm"),
    ]
    _insert_row(conn, "fan_rpm", columns, values)
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
