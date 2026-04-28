from contextlib import closing
import sqlite3
import unittest


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


def create_sensor_snapshot_table(conn):
    conn.execute(CREATE_SENSOR_SNAPSHOT_TABLE_SQL)


def insert_sensor_snapshot(conn, greenhouse, payload):
    columns = ("greenhouse", "ts", "source", *SENSOR_VALUE_COLUMNS)
    values = [greenhouse, payload["ts"], payload.get("source")]
    values.extend(payload[column] for column in SENSOR_VALUE_COLUMNS)

    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    conn.execute(
        f"INSERT INTO sensor_snapshot ({column_names}) VALUES ({placeholders})",
        values,
    )
    conn.commit()


class SensorSnapshotSqliteTest(unittest.TestCase):
    def test_sensor_snapshot_values_are_written_to_sqlite(self):
        sample_payload = {
            "ts": "2026-04-28T10:15:30+09:00",
            "source": "rpi5_main",
            "temp_pot_c": 24.7,
            "hum_pot_pct": 62.5,
            "temp_top_c": 27.1,
            "hum_top_pct": 58.3,
            "co2_ppm": 812.0,
            "par_w_m2": 135.4,
            "soil_moisture_1_pct": 41.0,
            "soil_moisture_2_pct": 42.5,
            "soil_moisture_3_pct": 39.8,
            "soil_moisture_4_pct": 44.2,
            "soil_moisture_5_pct": 40.7,
            "soil_moisture_6_pct": 43.1,
        }

        with closing(sqlite3.connect(":memory:")) as conn:
            conn.row_factory = sqlite3.Row
            create_sensor_snapshot_table(conn)
            insert_sensor_snapshot(conn, greenhouse="gh1", payload=sample_payload)

            row = conn.execute(
                "SELECT * FROM sensor_snapshot WHERE greenhouse = ? ORDER BY ts DESC LIMIT 1",
                ("gh1",),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["greenhouse"], "gh1")
        self.assertEqual(row["ts"], sample_payload["ts"])
        self.assertEqual(row["source"], sample_payload["source"])
        self.assertTrue(row["received_at"])

        for column in SENSOR_VALUE_COLUMNS:
            self.assertAlmostEqual(row[column], sample_payload[column], places=6)


if __name__ == "__main__":
    unittest.main()
