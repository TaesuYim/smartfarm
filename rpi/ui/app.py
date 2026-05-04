import argparse
from contextlib import closing
import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import paho.mqtt.client as mqtt

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from rpi.logger.db import DEFAULT_DB_DIR, SENSOR_VALUE_COLUMNS, monthly_db_path, now_kst_iso

GREENHOUSES = ("gh1",)

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
def resolve_db_path(db_path=None, db_dir=DEFAULT_DB_DIR):
    return Path(db_path) if db_path else monthly_db_path(db_dir)


def fetch_latest_sensor_snapshot(db_path, greenhouse):
    db_file = Path(db_path)
    if not db_file.exists():
        return None

    with closing(sqlite3.connect(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM ui_latest WHERE greenhouse = ?",
            (greenhouse,),
        ).fetchone()


def build_sensor_payload(ui_row):
    snapshot = dict(ui_row) if ui_row else None
    sensors = []
    for column in SENSOR_VALUE_COLUMNS:
        label, unit = SENSOR_LABELS.get(column, (column, ""))
        value = snapshot.get(column) if snapshot else None
        sensors.append({"key": column, "label": label, "value": value, "unit": unit})
    return {
        "snapshot": snapshot,
        "sensors": sensors,
        "sensor_ts": snapshot["sensor_ts"] if snapshot else None,
    }

def fetch_latest_data(db_path, greenhouse):
    db_file = Path(db_path)
    if not db_file.exists():
        return None

    try:
        with closing(sqlite3.connect(db_file)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM ui_latest WHERE greenhouse = ?", (greenhouse,)
            ).fetchone()

        return dict(row) if row else None
    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return None

_mqtt_client = None

def _get_mqtt_client():
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    return _mqtt_client

def connect_mqtt(host="127.0.0.1", port=1883):
    client = _get_mqtt_client()
    try:
        client.connect(host, port, 60)
        client.loop_start()
    except Exception as e:
        print(f"MQTT connect error: {e}")

def publish_mqtt(greenhouse, command_dict):
    topic = f"sf/{greenhouse}/actuators/cmd"
    command_dict = dict(command_dict)
    command_dict.setdefault("ts", now_kst_iso())
    command_dict.setdefault("source", "sfes_lab_ui")
    payload = json.dumps(command_dict)
    try:
        client = _get_mqtt_client()
        result = client.publish(topic, payload)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"MQTT Publish Error: {e}")
        return False

class SmartFarmRequestHandler(BaseHTTPRequestHandler):
    db_path = None
    db_dir = DEFAULT_DB_DIR

    @classmethod
    def current_db_path(cls):
        return resolve_db_path(cls.db_path, cls.db_dir)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            html_response(self, INDEX_HTML)
            return

        if parsed_url.path == "/api/latest":
            query = parse_qs(parsed_url.query)
            greenhouse = query.get("greenhouse", ["gh1"])[0]
            if greenhouse not in GREENHOUSES:
                json_response(self, HTTPStatus.BAD_REQUEST, {"error": "unsupported greenhouse"})
                return
            try:
                ui_row = fetch_latest_data(self.current_db_path(), greenhouse)
                sensor_payload = build_sensor_payload(ui_row)

                payload = {
                    **sensor_payload,
                    "actuators": ui_row if ui_row else None
                }
                
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
            if greenhouse not in GREENHOUSES:
                json_response(self, HTTPStatus.BAD_REQUEST, {"error": "unsupported greenhouse"})
                return
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
  <title>SFES Lab</title>
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
    <h1 style="margin:0">SFES <span style="color:var(--primary)">Lab</span></h1>
    <div class="gh-selector">
      <button class="btn-gh active" onclick="setGH('gh1')">GH1</button>
    </div>
  </header>

  <div class="section-title">Sensors</div>
  <div id="sensor-grid" class="grid"></div>

  <div class="section-title">Climate Control</div>
  <div class="grid">
    <div class="card">
      <div class="sensor-label">Ventilation Fan</div>
      <input type="range" class="slider" id="vent_fan" min="0" max="100" value="0" oninput="document.getElementById('vent_fan_val').innerText=this.value" onchange="sendCmd({'vent_fan_pwm_pct': parseInt(this.value)})">
      <div class="ctrl-row"><span id="vent_fan_val">0</span>%</div>
    </div>
    <div class="card">
      <div class="sensor-label">Mist & Heaters</div>
      <div class="ctrl-row"><span>Mist</span><div id="mist_toggle" class="toggle" onclick="toggleMist()"></div></div>
      <div class="ctrl-row"><span>H1</span><input type="range" class="slider" style="width:40%" id="h1" min="0" max="100" value="0" onchange="sendCmd({'heater_1_pwm_pct': parseInt(this.value)})"> <span>H2</span><input type="range" class="slider" style="width:40%" id="h2" min="0" max="100" value="0" onchange="sendCmd({'heater_2_pwm_pct': parseInt(this.value)})"></div>
    </div>
    <div class="card">
      <div class="sensor-label">Circulation Fans</div>
      <div class="ctrl-row">Fan 1 <input type="range" class="slider" style="width:60%" id="circ1" min="0" max="100" value="0" onchange="sendCmd({'circ_fan_1_pwm_pct': parseInt(this.value)})"></div>
      <div class="ctrl-row">Fan 2 <input type="range" class="slider" style="width:60%" id="circ2" min="0" max="100" value="0" onchange="sendCmd({'circ_fan_2_pwm_pct': parseInt(this.value)})"></div>
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
      <div class="sensor-label">Ventilation Window 2</div>
      <div class="btn-group">
        <button class="btn-cmd" id="win2_open" onclick="sendCmd({'window_2_cmd':'open'})">Open</button>
        <button class="btn-cmd" id="win2_stop" onclick="sendCmd({'window_2_cmd':'stop'})">Stop</button>
        <button class="btn-cmd" id="win2_close" onclick="sendCmd({'window_2_cmd':'close'})">Close</button>
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
      <input type="range" class="slider" id="pump" min="0" max="100" value="0" oninput="document.getElementById('pump_val').innerText=this.value" onchange="sendCmd({'pump_pwm_pct': parseInt(this.value)})">
      <div class="ctrl-row"><span id="pump_val">0</span>%</div>
    </div>
    <div class="card" style="grid-column: span 2;">
      <div class="sensor-label">Solenoid Valves</div>
      <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-top:10px;">
        <div class="ctrl-row">P1 <div id="v1" class="toggle" onclick="toggleValve(1)"></div></div>
        <div class="ctrl-row">P2 <div id="v2" class="toggle" onclick="toggleValve(2)"></div></div>
        <div class="ctrl-row">P3 <div id="v3" class="toggle" onclick="toggleValve(3)"></div></div>
        <div class="ctrl-row">P4 <div id="v4" class="toggle" onclick="toggleValve(4)"></div></div>
        <div class="ctrl-row">P5 <div id="v5" class="toggle" onclick="toggleValve(5)"></div></div>
        <div class="ctrl-row">P6 <div id="v6" class="toggle" onclick="toggleValve(6)"></div></div>
        <div class="ctrl-row">Fog <div id="v7" class="toggle" onclick="toggleValve(7)"></div></div>
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
      <input type="range" class="slider" id="led_bright" min="0" max="100" value="0" onchange="sendCmd({'led_brightness_pct': parseInt(this.value)})">
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
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ greenhouse: curGH, commands: cmds })
  });
  // 즉시 업데이트 반영을 위해 데이터 로드
  setTimeout(loadData, 500);
}

function toggleMist() {
  currentMist = !currentMist;
  document.getElementById('mist_toggle').classList.toggle('on', currentMist);
  sendCmd({'mist_on': currentMist});
}

function toggleValve(idx) {
  valveStates[idx-1] = !valveStates[idx-1];
  document.getElementById(`v${idx}`).classList.toggle('on', valveStates[idx-1]);
  let key = (idx === 7) ? 'valve_fog_on' : `valve_pot_${idx}_on`;
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
  try {
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

    // Update Actuator Status (Feedback from Arduino)
    if(data.actuators) {
      const act = data.actuators;
      
      // Sliders (Update only if user is not dragging)
      const sliders = {
        'vent_fan': act.vent_fan_pwm_pct,
        'h1': act.heater_1_pwm_pct,
        'h2': act.heater_2_pwm_pct,
        'circ1': act.circ_fan_1_pwm_pct,
        'circ2': act.circ_fan_2_pwm_pct,
        'pump': act.pump_pwm_pct,
        'led_bright': act.led_brightness_pct
      };
      
      for(let id in sliders) {
        const el = document.getElementById(id);
        if(el && document.activeElement !== el) {
          el.value = sliders[id] || 0;
          const valEl = document.getElementById(id + '_val');
          if(valEl) valEl.innerText = sliders[id] || 0;
        }
      }
      
      // Mist
      currentMist = !!act.mist_on;
      document.getElementById('mist_toggle').classList.toggle('on', currentMist);
      
      // Valves
      for(let i=1; i<=7; i++) {
        let key = (i === 7) ? 'valve_fog_on' : `valve_pot_${i}_on`;
        valveStates[i-1] = !!act[key];
        const vEl = document.getElementById(`v${i}`);
        if(vEl) vEl.classList.toggle('on', valveStates[i-1]);
      }
      
      // Window/Screen Button States
      const btnStates = {
        'win1': act.window_1_cmd,
        'win2': act.window_2_cmd,
        'shading': act.shading_screen_cmd
      };
      
      for(let prefix in btnStates) {
        ['open', 'stop', 'close'].forEach(cmd => {
          const btn = document.getElementById(`${prefix}_${cmd}`);
          if(btn) btn.classList.toggle('active', btnStates[prefix] === cmd);
        });
      }

      // LED Color
      if(act.led_r !== undefined) {
        const hex = "#" + ((1 << 24) + (act.led_r << 16) + (act.led_g << 8) + act.led_b).toString(16).slice(1);
        document.getElementById('led_color').value = hex;
      }
    }
  } catch(e) {
    console.error("Data load failed", e);
  }
}

setInterval(loadData, 2000);
loadData();
</script>
</body>
</html>
"""

def run_server(db_path, db_dir, host, port):
    SmartFarmRequestHandler.db_path = db_path
    SmartFarmRequestHandler.db_dir = db_dir
    server = ThreadingHTTPServer((host, port), SmartFarmRequestHandler)
    print(f"SFES Lab UI: http://{host}:{port}")
    print(f"reading SQLite DB from {SmartFarmRequestHandler.current_db_path()}")
    server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description="SFES Lab Control UI")
    parser.add_argument("--db-dir", default=DEFAULT_DB_DIR, help="Directory for monthly SQLite DB files")
    parser.add_argument("--db", default=None, help="Use one fixed SQLite DB path instead of monthly DB files")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    parser.add_argument("--port", default=8000, type=int, help="HTTP port")
    parser.add_argument("--mqtt-host", default="127.0.0.1", help="MQTT broker host")
    parser.add_argument("--mqtt-port", default=1883, type=int, help="MQTT broker port")
    args = parser.parse_args()
    connect_mqtt(args.mqtt_host, args.mqtt_port)
    run_server(args.db, args.db_dir, args.host, args.port)

if __name__ == "__main__":
    main()
