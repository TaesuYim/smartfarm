import argparse
from contextlib import closing
import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add project root to sys.path to allow absolute imports when running as a script
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from rpi.logger.db import SENSOR_VALUE_COLUMNS


DEFAULT_DB_PATH = "smartfarm.sqlite3"
GREENHOUSES = ("gh1", "gh2")

SENSOR_LABELS = {
    "temp_pot_c": ("Pot Temperature", "V"),
    "hum_pot_pct": ("Pot Humidity", "V"),
    "temp_top_c": ("Top Temperature", "V"),
    "hum_top_pct": ("Top Humidity", "V"),
    "co2_ppm": ("CO2", "V"),
    "par_w_m2": ("PAR", "V"),
    "soil_moisture_1_pct": ("Soil Moisture 1", "V"),
    "soil_moisture_2_pct": ("Soil Moisture 2", "V"),
    "soil_moisture_3_pct": ("Soil Moisture 3", "V"),
    "soil_moisture_4_pct": ("Soil Moisture 4", "V"),
    "soil_moisture_5_pct": ("Soil Moisture 5", "V"),
    "soil_moisture_6_pct": ("Soil Moisture 6", "V"),
}


def fetch_latest_sensor_snapshot(db_path, greenhouse):
    if greenhouse not in GREENHOUSES:
        raise ValueError("greenhouse must be gh1 or gh2")

    db_file = Path(db_path)
    if not db_file.exists():
        return None

    with closing(sqlite3.connect(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT *
            FROM sensor_snapshot
            WHERE greenhouse = ?
            ORDER BY ts DESC, id DESC
            LIMIT 1
            """,
            (greenhouse,),
        ).fetchone()

    return dict(row) if row else None


def build_sensor_payload(row):
    if row is None:
        return {"snapshot": None, "sensors": []}

    sensors = []
    for column in SENSOR_VALUE_COLUMNS:
        label, unit = SENSOR_LABELS[column]
        sensors.append(
            {
                "key": column,
                "label": label,
                "value": row.get(column),
                "unit": unit,
            }
        )

    return {
        "snapshot": {
            "id": row["id"],
            "greenhouse": row["greenhouse"],
            "ts": row["ts"],
            "source": row["source"],
            "received_at": row["received_at"],
        },
        "sensors": sensors,
    }


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler, body):
    encoded = body.encode("utf-8")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


class SmartFarmRequestHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB_PATH

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            html_response(self, INDEX_HTML)
            return

        if parsed_url.path == "/api/latest":
            query = parse_qs(parsed_url.query)
            greenhouse = query.get("greenhouse", ["gh1"])[0]
            try:
                row = fetch_latest_sensor_snapshot(self.db_path, greenhouse)
            except sqlite3.Error as exc:
                json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            except ValueError as exc:
                json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            json_response(self, HTTPStatus.OK, build_sensor_payload(row))
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SmartFarm Monitor</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f4f7f5;
      color: #1d2b24;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: #f4f7f5;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 24px;
      border-bottom: 1px solid #d8e2dc;
      background: #ffffff;
    }

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
    }

    main {
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .segmented {
      display: inline-grid;
      grid-template-columns: repeat(2, 64px);
      border: 1px solid #cbd8d1;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .segmented button {
      min-height: 40px;
      border: 0;
      background: transparent;
      color: #263a31;
      font-size: 14px;
      cursor: pointer;
    }

    .segmented button.active {
      background: #1f7a4d;
      color: #ffffff;
      font-weight: 700;
    }

    .meta {
      color: #506259;
      font-size: 14px;
      text-align: right;
    }

    .status {
      min-height: 22px;
      margin: 0 0 16px;
      color: #7a4d15;
      font-size: 14px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .sensor {
      min-height: 118px;
      padding: 16px;
      border: 1px solid #d8e2dc;
      border-radius: 8px;
      background: #ffffff;
    }

    .sensor-name {
      margin: 0 0 14px;
      color: #506259;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .sensor-value {
      display: flex;
      align-items: baseline;
      gap: 8px;
      min-width: 0;
    }

    .number {
      font-size: 32px;
      font-weight: 800;
      line-height: 1;
      color: #142119;
    }

    .unit {
      color: #506259;
      font-size: 14px;
    }

    @media (max-width: 880px) {
      .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 560px) {
      header,
      .toolbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .meta {
        text-align: left;
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>SmartFarm Monitor</h1>
    <div class="meta" id="clock"></div>
  </header>
  <main>
    <section class="toolbar">
      <div class="segmented" aria-label="Greenhouse">
        <button type="button" data-greenhouse="gh1" class="active">GH1</button>
        <button type="button" data-greenhouse="gh2">GH2</button>
      </div>
      <div class="meta" id="snapshot-meta">-</div>
    </section>
    <p class="status" id="status"></p>
    <section class="grid" id="sensor-grid"></section>
  </main>
  <script>
    const grid = document.getElementById("sensor-grid");
    const status = document.getElementById("status");
    const meta = document.getElementById("snapshot-meta");
    const clock = document.getElementById("clock");
    let greenhouse = "gh1";

    function formatValue(value) {
      if (value === null || value === undefined) {
        return "-";
      }
      const numeric = Number(value);
      return Number.isFinite(numeric) ? numeric.toFixed(1) : String(value);
    }

    function renderSensors(sensors) {
      grid.innerHTML = sensors.map((sensor) => `
        <article class="sensor">
          <p class="sensor-name">${sensor.label}</p>
          <div class="sensor-value">
            <span class="number">${formatValue(sensor.value)}</span>
            <span class="unit">${sensor.unit}</span>
          </div>
        </article>
      `).join("");
    }

    async function loadLatest() {
      try {
        const response = await fetch(`/api/latest?greenhouse=${greenhouse}`, { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Failed to load data");
        }

        if (!payload.snapshot) {
          grid.innerHTML = "";
          meta.textContent = `${greenhouse.toUpperCase()} no data`;
          status.textContent = "No sensor_snapshot rows found in smartfarm.sqlite3.";
          return;
        }

        renderSensors(payload.sensors);
        meta.textContent = `${payload.snapshot.greenhouse.toUpperCase()} updated ${payload.snapshot.ts}`;
        status.textContent = "";
      } catch (error) {
        status.textContent = error.message;
      }
    }

    document.querySelectorAll("[data-greenhouse]").forEach((button) => {
      button.addEventListener("click", () => {
        greenhouse = button.dataset.greenhouse;
        document.querySelectorAll("[data-greenhouse]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        loadLatest();
      });
    });

    function updateClock() {
      clock.textContent = new Date().toLocaleString();
    }

    updateClock();
    loadLatest();
    setInterval(updateClock, 1000);
    setInterval(loadLatest, 5000);
  </script>
</body>
</html>
"""


def run_server(db_path, host, port):
    SmartFarmRequestHandler.db_path = db_path
    server = ThreadingHTTPServer((host, port), SmartFarmRequestHandler)
    print(f"SmartFarm UI: http://{host}:{port}")
    print(f"Reading DB: {Path(db_path).resolve()}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Show latest SmartFarm sensor_snapshot values.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host")
    parser.add_argument("--port", default=8000, type=int, help="HTTP port")
    args = parser.parse_args()
    run_server(args.db, args.host, args.port)


if __name__ == "__main__":
    main()
