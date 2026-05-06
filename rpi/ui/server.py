import json
import sys
import sqlite3
import subprocess
import time
import os
import paho.mqtt.client as mqtt
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Path setup
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rpi.logger.db import monthly_db_path, DEFAULT_DB_DIR, now_kst_iso

app = FastAPI(title="SFES Lab API")

# --- Background Services ---
def _is_running(pattern):
    if os.name == 'nt': return False
    try: return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0
    except: return False

def start_background_services():
    if not _is_running("rpi.logger.mqtt_logger"):
        log_file = Path(project_root) / "mqtt_logger.log"
        with open(log_file, "a") as f:
            subprocess.Popen([sys.executable, "-m", "rpi.logger.mqtt_logger"], cwd=project_root, stdout=f, stderr=f, start_new_session=True)

    if not _is_running("rpi.sensor_hub.main"):
        sensor_log = Path(project_root) / "sensor_pub.log"
        with open(sensor_log, "a") as f:
            cmd = [sys.executable, "-m", "rpi.sensor_hub.main"]
            if os.name == 'nt': cmd.append("--dummy")
            subprocess.Popen(cmd, cwd=project_root, stdout=f, stderr=f, start_new_session=True)
            
    if not _is_running("rpi.services.weather_service"):
        weather_log = Path(project_root) / "weather_service.log"
        with open(weather_log, "a") as f:
            subprocess.Popen([sys.executable, "-m", "rpi.services.weather_service"], cwd=project_root, stdout=f, stderr=f, start_new_session=True)

@app.on_event("startup")
def startup_event():
    start_background_services()

# --- DB Helpers ---
def _q(sql, params=(), one=False):
    p = monthly_db_path(DEFAULT_DB_DIR)
    if not p.exists(): return None if one else []
    with closing(sqlite3.connect(p)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
    if one: return dict(rows[0]) if rows else None
    return [dict(r) for r in rows]

# --- API Endpoints ---
@app.get("/api/latest")
def get_latest():
    latest = _q("SELECT * FROM ui_latest WHERE greenhouse='gh1'", one=True) or {}
    
    hb_rows = _q("SELECT source, ts, uptime_ms FROM heartbeat WHERE greenhouse='gh1' ORDER BY id DESC LIMIT 20")
    hb_map = {}
    for r in hb_rows:
        src = r.get("source", "?")
        if src not in hb_map:
            hb_map[src] = r
    
    settings_rows = _q("SELECT key, value FROM app_setting")
    settings = {"heartbeat_timeout_sec": "10"}
    for r in settings_rows:
        settings[r["key"]] = r["value"]
        
    return {
        "latest": latest,
        "heartbeat": hb_map,
        "settings": settings,
        "server_time": now_kst_iso()
    }

@app.get("/api/history")
def get_history(minutes: int = 60):
    kst = timezone(timedelta(hours=9))
    cutoff = (datetime.now(kst) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    return _q("SELECT * FROM sensor_snapshot WHERE greenhouse='gh1' AND ts>=? ORDER BY ts", (cutoff,))

class CommandPayload(BaseModel):
    cmds: Dict[str, Any]
    
@app.post("/api/command")
def send_command(payload: CommandPayload):
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        c.connect("127.0.0.1", 1883, 60)
        c.loop_start()
        
        full_payload = {"ts": now_kst_iso(), "source": "sfes_lab_ui", **payload.cmds}
        res = c.publish("sf/gh1/actuators/cmd", json.dumps(full_payload))
        
        c.loop_stop()
        c.disconnect()
        
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="MQTT publish failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/arduino/reset")
def reset_arduino():
    if os.name == 'nt':
        return {"status": "success", "msg": "dummy reset on windows"}
        
    try:
        from gpiozero import OutputDevice
        import time
        rl = OutputDevice(17, active_high=True, initial_value=True)
        rl.off()
        time.sleep(1)
        rl.on()
        rl.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def save_settings(settings: Dict[str, str]):
    p = monthly_db_path(DEFAULT_DB_DIR)
    try:
        with closing(sqlite3.connect(p)) as conn:
            for k, v in settings.items():
                conn.execute(
                    "INSERT INTO app_setting(key,value,updated_at) VALUES(?,?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                    (k, str(v), now_kst_iso())
                )
            conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
