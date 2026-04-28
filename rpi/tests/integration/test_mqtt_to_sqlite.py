from contextlib import closing
import json
import sqlite3
import unittest

from rpi.logger.db import init_db
from rpi.logger.mqtt_logger import handle_mqtt_message


class MqttToSqliteTest(unittest.TestCase):
    def test_ads_mqtt_message_is_written_to_ads_reading_table(self):
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.row_factory = sqlite3.Row
            init_db(conn)

            stored_table = handle_mqtt_message(
                conn,
                "sensor/ads1115_0x49/a0/voltage",
                b"2.226",
            )

            row = conn.execute("SELECT * FROM ads_reading").fetchone()

        self.assertEqual(stored_table, "ads_reading")
        self.assertIsNotNone(row)
        self.assertEqual(row["source"], "ads1115")
        self.assertEqual(row["address"], "0x49")
        self.assertEqual(row["channel"], "a0")
        self.assertEqual(row["measurement"], "voltage")
        self.assertAlmostEqual(row["value"], 2.226, places=6)

    def test_sensor_snapshot_mqtt_message_is_written_to_sensor_snapshot_table(self):
        payload = {
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
            init_db(conn)

            stored_table = handle_mqtt_message(
                conn,
                "sf/gh1/sensors/snapshot",
                json.dumps(payload).encode("utf-8"),
            )

            row = conn.execute("SELECT * FROM sensor_snapshot").fetchone()

        self.assertEqual(stored_table, "sensor_snapshot")
        self.assertIsNotNone(row)
        self.assertEqual(row["greenhouse"], "gh1")
        self.assertEqual(row["ts"], payload["ts"])
        self.assertEqual(row["source"], payload["source"])
        self.assertAlmostEqual(row["temp_pot_c"], payload["temp_pot_c"], places=6)


if __name__ == "__main__":
    unittest.main()
