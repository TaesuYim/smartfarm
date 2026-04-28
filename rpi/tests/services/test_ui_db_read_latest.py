from contextlib import closing
import sqlite3
import unittest
import uuid
from pathlib import Path

from rpi.logger.db import init_db, insert_sensor_snapshot
from rpi.ui.app import build_sensor_payload, fetch_latest_sensor_snapshot

REPO_ROOT = Path(__file__).resolve().parents[3]


class UiLatestSensorSnapshotTest(unittest.TestCase):
    def test_reads_latest_sensor_snapshot_for_greenhouse(self):
        db_path = REPO_ROOT / f"ui_latest_{uuid.uuid4().hex}.sqlite3"

        first_payload = {
            "ts": "2026-04-28T10:15:30+09:00",
            "source": "rpi5_main",
            "temp_pot_c": 24.0,
        }
        latest_payload = {
            "ts": "2026-04-28T10:16:30+09:00",
            "source": "rpi5_main",
            "temp_pot_c": 25.5,
            "hum_pot_pct": 61.2,
        }

        try:
            with closing(sqlite3.connect(db_path)) as conn:
                init_db(conn)
                insert_sensor_snapshot(conn, "gh1", first_payload)
                insert_sensor_snapshot(conn, "gh1", latest_payload)

            row = fetch_latest_sensor_snapshot(db_path, "gh1")
            payload = build_sensor_payload(row)

            self.assertEqual(payload["snapshot"]["greenhouse"], "gh1")
            self.assertEqual(payload["snapshot"]["ts"], latest_payload["ts"])
            self.assertEqual(payload["sensors"][0]["key"], "temp_pot_c")
            self.assertAlmostEqual(payload["sensors"][0]["value"], 25.5, places=6)
        finally:
            for suffix in ("", "-journal", "-wal", "-shm"):
                path = Path(f"{db_path}{suffix}")
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
