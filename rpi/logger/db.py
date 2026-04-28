import sqlite3


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
    conn.execute(CREATE_ADS_READING_TABLE_SQL)
    for statement in CREATE_INDEXES_SQL:
        conn.execute(statement)
    conn.commit()


def insert_sensor_snapshot(conn, greenhouse, payload):
    columns = ("greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values = [greenhouse, payload["ts"], payload.get("source")]
    values.extend(payload.get(column) for column in SENSOR_VALUE_COLUMNS)

    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    conn.execute(
        f"INSERT INTO sensor_snapshot ({column_names}) VALUES ({placeholders})",
        values,
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
