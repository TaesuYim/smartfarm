import argparse
from contextlib import closing
import json
import sqlite3
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from rpi.logger.db import SENSOR_VALUE_COLUMNS

DEFAULT_DB_PATH = "smartfarm.sqlite3"
GREENHOUSES = ("gh1", "gh2")

SENSOR_LABELS = {
    "temp_pot_c": ("Pot Temperature", "°C"),
    "hum_pot_pct": ("Pot Humidity", "%"),
    "temp_top_c": ("Top Temperature", "°C"),
    "hum_top_pct": ("Top Humidity", "%"),
    "co2_ppm": ("CO2", "ppm"),
    "par_w_m2": ("PAR", "W/m2"),
    "soil_moisture_1_pct": ("Soil Moisture 1", "%"),
    "soil_moisture_2_pct": ("Soil Moisture 2", "%"),
    "soil_moisture_3_pct": ("Soil Moisture 3", "%"),
    "soil_moisture_4_pct": ("Soil Moisture 4", "%"),
    "soil_moisture_5_pct": ("Soil Moisture 5", "%"),
    "soil_moisture_6_pct": ("Soil Moisture 6", "%"),
}
# Sensor columns definition
SENSOR_VALUE_COLUMNS = [
    "temp_pot_c", "hum_pot_pct", "temp_top_c", "hum_top_pct",
    "co2_ppm", "par_w_m2", "soil_moisture_1_pct", "soil_moisture_2_pct",
    "soil_moisture_3_pct", "soil_moisture_4_pct", "soil_moisture_5_pct", "soil_moisture_6_pct"
]

def fetch_latest_data(db_path, greenhouse):
    db_file = Path(db_path)
    if not db_file.exists():
        return None, None

    try:
        with closing(sqlite3.connect(db_file)) as conn:
            conn.row_factory = sqlite3.Row
            # Sensor data
            sensor_row = conn.execute(
                "SELECT * FROM sensor_latest WHERE greenhouse = ?", (greenhouse,)
            ).fetchone()
            
            # Actuator state
            actuator_row = conn.execute(
                "SELECT * FROM actuator_latest WHERE greenhouse = ?", (greenhouse,)
            ).fetchone()

        return (dict(sensor_row) if sensor_row else None), (dict(actuator_row) if actuator_row else None)
    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return None, None

def publish_mqtt(greenhouse, command_dict):
    topic = f"sf/{greenhouse}/actuators/cmd"
    payload = json.dumps(command_dict)
    try:
        subprocess.run(["mosquitto_pub", "-t", topic, "-m", payload], check=True)
        return True
    except Exception as e:
        print(f"MQTT Publish Error: {e}")
        return False

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
                sensor_row, actuator_row = fetch_latest_data(self.db_path, greenhouse)
                
                sensors = []
                for column in SENSOR_VALUE_COLUMNS:
                    label, unit = SENSOR_LABELS.get(column, (column, ""))
                    # 더 확실하게 값을 가져오도록 수정
                    val = None
                    if sensor_row and column in sensor_row:
                        val = sensor_row[column]
                    
                    sensors.append({"key": column, "label": label, "value": val, "unit": unit})

                payload = {
                    "sensors": sensors,
                    "sensor_ts": sensor_row["ts"] if sensor_row else None,
                    "actuators": actuator_row if actuator_row else None
                }
                # DEBUG: 서버 터미널에서 데이터 확인용
                # print(f"Payload: {payload}")
                
                json_response(self, HTTPStatus.OK, payload)
            except Exception as e:
                print(f"API Error: {e}")
                json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/control":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            greenhouse = data.get("greenhouse", "gh1")
            commands = data.get("commands", {})
            
            if publish_mqtt(greenhouse, commands):
                json_response(self, HTTPStatus.OK, {"result": "ok"})
            else:
                json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to publish MQTT"})
            return

    def log_message(self, format, *args):
        return

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

# UI Template (Sensors + Actuators Control)
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SmartFarm Pro v2</title>
  <style>
    :root {
      --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --primary: #10b981; --accent: #3b82f6;
      font-family: 'Inter', system-ui, sans-serif;
    }
    body { background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
    .gh-selector { display: flex; gap: 10px; }
    button { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; transition: 0.2s; }
    .btn-gh { background: #334155; color: #94a3b8; }
    .btn-gh.active { background: var(--primary); color: white; }
    
    .section-title { font-size: 1.2rem; margin: 30px 0 15px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
    
    /* Cards */
    .card { background: var(--card); padding: 20px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .sensor-label { font-size: 0.9rem; color: #94a3b8; }
    .sensor-val { font-size: 2rem; font-weight: 700; margin: 10px 0; }
    
    /* Control Panel */
    .control-group { display: flex; flex-direction: column; gap: 15px; }
    .ctrl-row { display: flex; justify-content: space-between; align-items: center; }
    .slider { width: 100%; height: 6px; background: #334155; border-radius: 5px; outline: none; appearance: none; }
    .slider::-webkit-slider-thumb { appearance: none; width: 18px; height: 18px; background: var(--primary); border-radius: 50%; cursor: pointer; }
    
    .btn-group { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
    .btn-cmd { background: #334155; color: white; padding: 8px; font-size: 0.8rem; }
    .btn-cmd.active { background: var(--accent); }
    .toggle { width: 50px; height: 26px; background: #334155; border-radius: 13px; position: relative; cursor: pointer; transition: 0.3s; }
    .toggle.on { background: var(--primary); }
    .toggle::after { content: ''; position: absolute; width: 22px; height: 22px; background: white; border-radius: 50%; top: 2px; left: 2px; transition: 0.3s; }
    .toggle.on::after { left: 26px; }

    input[type="color"] { width: 100%; height: 40px; border: none; border-radius: 8px; background: none; cursor: pointer; }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1 style="margin:0">SmartFarm <span style="color:var(--primary)">Pro</span></h1>
    <div class="gh-selector">
      <button class="btn-gh active" onclick="setGH('gh1')">GH1</button>
      <button class="btn-gh" onclick="setGH('gh2')">GH2</button>
    </div>
  </header>

  <div class="section-title">Sensors</div>
  <div id="sensor-grid" class="grid"></div>

  <div class="section-title">Climate Control</div>
  <div class="grid">
    <div class="card">
      <div class="sensor-label">Ventilation Fan</div>
      <input type="range" class="slider" id="vent_fan" onchange="sendCmd({'vent_fan_pwm_pct': parseInt(this.value)})">
      <div class="ctrl-row"><span id="vent_fan_val">0</span>%</div>
    </div>
    <div class="card">
      <div class="sensor-label">Mist & Heaters</div>
      <div class="ctrl-row"><span>Mist</span><div id="mist_toggle" class="toggle" onclick="toggleMist()"></div></div>
      <div class="ctrl-row"><span>Heater 1</span><input type="range" class="slider" style="width:60%" id="h1" onchange="sendCmd({'heater_1_pwm_pct': parseInt(this.value)})"></div>
    </div>
    <div class="card">
      <div class="sensor-label">Circulation Fans</div>
      <div class="ctrl-row">Fan 1 <input type="range" class="slider" style="width:60%" id="circ1" onchange="sendCmd({'circ_fan_1_pwm_pct': parseInt(this.value)})"></div>
      <div class="ctrl-row">Fan 2 <input type="range" class="slider" style="width:60%" id="circ2" onchange="sendCmd({'circ_fan_2_pwm_pct': parseInt(this.value)})"></div>
    </div>
  </div>

  <div class="section-title">Windows & Screen</div>
  <div class="grid">
    <div class="card">
      <div class="sensor-label">Ventilation Window 1</div>
      <div class="btn-group">
        <button class="btn-cmd" id="win1_open" onclick="sendCmd({'window_1_cmd':'open'})">Open</button>
        <button class="btn-cmd" id="win1_stop" onclick="sendCmd({'window_1_cmd':'stop'})">Stop</button>
        <button class="btn-cmd" id="win1_close" onclick="sendCmd({'window_1_cmd':'close'})">Close</button>
      </div>
    </div>
    <div class="card">
      <div class="sensor-label">Shading Screen</div>
      <div class="btn-group">
        <button class="btn-cmd" id="shading_open" onclick="sendCmd({'shading_screen_cmd':'open'})">Open</button>
        <button class="btn-cmd" id="shading_stop" onclick="sendCmd({'shading_screen_cmd':'stop'})">Stop</button>
        <button class="btn-cmd" id="shading_close" onclick="sendCmd({'shading_screen_cmd':'close'})">Close</button>
      </div>
    </div>
  </div>

  <div class="section-title">Irrigation</div>
  <div class="grid">
    <div class="card">
      <div class="sensor-label">Main Pump</div>
      <input type="range" class="slider" id="pump" onchange="sendCmd({'pump_pwm_pct': parseInt(this.value)})">
      <div class="ctrl-row"><span id="pump_val">0</span>%</div>
    </div>
    <div class="card">
      <div class="sensor-label">Valves</div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
        <div class="ctrl-row">Pot 1 <div id="v1" class="toggle" onclick="toggleValve(1)"></div></div>
        <div class="ctrl-row">Pot 2 <div id="v2" class="toggle" onclick="toggleValve(2)"></div></div>
      </div>
    </div>
  </div>

  <div class="section-title">Lighting</div>
  <div class="grid">
    <div class="card">
      <div class="sensor-label">RGB Color</div>
      <input type="color" id="led_color" onchange="sendRGB(this.value)">
    </div>
    <div class="card">
      <div class="sensor-label">Brightness</div>
      <input type="range" class="slider" id="led_bright" onchange="sendCmd({'led_brightness_pct': parseInt(this.value)})">
    </div>
  </div>
</div>

<script>
let curGH = 'gh1';
let currentMist = false;
let valveStates = [false, false, false, false, false, false, false];

function setGH(gh) {
  curGH = gh;
  document.querySelectorAll('.btn-gh').forEach(b => b.classList.toggle('active', b.innerText === gh.toUpperCase()));
  loadData();
}

async function sendCmd(cmds) {
  await fetch('/api/control', {
    method: 'POST',
    body: JSON.stringify({ greenhouse: curGH, commands: cmds })
  });
}

function toggleMist() {
  currentMist = !currentMist;
  sendCmd({'mist_on': currentMist});
}

function toggleValve(idx) {
  valveStates[idx-1] = !valveStates[idx-1];
  let key = `valve_pot_${idx}_on`;
  if(idx === 7) key = 'valve_fog_on';
  let cmd = {}; cmd[key] = valveStates[idx-1];
  sendCmd(cmd);
}

function sendRGB(hex) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  sendCmd({'led_r': r, 'led_g': g, 'led_b': b});
}

async function loadData() {
  const res = await fetch(`/api/latest?greenhouse=${curGH}`);
  const data = await res.json();
  
  // Update Sensors
  const grid = document.getElementById('sensor-grid');
  grid.innerHTML = data.sensors.map(s => `
    <div class="card">
      <div class="sensor-label">${s.label}</div>
      <div class="sensor-val">${s.value !== null ? s.value.toFixed(1) : '--'}<span style="font-size:1rem; margin-left:5px">${s.unit}</span></div>
    </div>
  `).join('');

  // Update Actuator Status (Feedback)
  if(data.actuators) {
    const act = data.actuators;
    document.getElementById('vent_fan').value = act.vent_fan_pwm_pct || 0;
    document.getElementById('vent_fan_val').innerText = act.vent_fan_pwm_pct || 0;
    document.getElementById('pump').value = act.pump_pwm_pct || 0;
    document.getElementById('pump_val').innerText = act.pump_pwm_pct || 0;
    
    currentMist = act.mist_on;
    document.getElementById('mist_toggle').classList.toggle('on', !!act.mist_on);
    
    // Update Window/Screen Button States
    ['window_1_cmd', 'shading_screen_cmd'].forEach(key => {
        const prefix = key.startsWith('win') ? 'win1' : 'shading';
        ['open', 'stop', 'close'].forEach(cmd => {
            const btn = document.getElementById(`${prefix}_${cmd}`);
            if(btn) btn.classList.toggle('active', act[key] === cmd);
        });
    });
  }
}

setInterval(loadData, 2000);
loadData();
</script>
</body>
</html>
"""

def run_server(db_path, host, port):
    SmartFarmRequestHandler.db_path = db_path
    server = ThreadingHTTPServer((host, port), SmartFarmRequestHandler)
    print(f"SmartFarm Pro UI: http://{host}:{port}")
    server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description="SmartFarm Control UI")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    parser.add_argument("--port", default=8000, type=int, help="HTTP port")
    args = parser.parse_args()
    run_server(args.db, args.host, args.port)

if __name__ == "__main__":
    main()
