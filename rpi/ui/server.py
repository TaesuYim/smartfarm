import json
import sys
import sqlite3
import subprocess
import time
import os
import threading
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

from rpi.logger.db import monthly_db_path, DEFAULT_DB_DIR, now_kst_iso, init_db, connect_db

app = FastAPI(title="SFES Lab API")
calibration_started = False

# --- Background Services ---
def _is_running(pattern):
    if os.name == 'nt': return False
    try: return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0
    except: return False

def start_background_services():
    print("--- Starting Background Services ---")
    
    # 1. MQTT Logger
    if not _is_running("rpi.logger.mqtt_logger"):
        print("  Starting MQTT Logger...")
        log_file = Path(project_root) / "mqtt_logger.log"
        try:
            with open(log_file, "a") as f:
                subprocess.Popen([sys.executable, "-m", "rpi.logger.mqtt_logger"], 
                                 cwd=project_root, stdout=f, stderr=f, start_new_session=True)
            print("  MQTT Logger started.")
        except Exception as e:
            print(f"  Failed to start MQTT Logger: {e}")
    else:
        print("  MQTT Logger is already running.")

    # 2. Sensor Hub (Publisher)
    if not _is_running("rpi.sensor_hub.sensor_to_publish"):
        print("  Starting Sensor Hub...")
        sensor_log = Path(project_root) / "sensor_pub.log"
        try:
            cmd = [sys.executable, "-m", "rpi.sensor_hub.sensor_to_publish"]
            with open(sensor_log, "a") as f:
                subprocess.Popen(cmd, cwd=project_root, stdout=f, stderr=f, start_new_session=True)
            print("  Sensor Hub started.")
        except Exception as e:
            print(f"  Failed to start Sensor Hub: {e}")
    else:
        print("  Sensor Hub is already running.")
            
    # 3. Weather Service
    if not _is_running("rpi.services.weather_service"):
        print("  Starting Weather Service...")
        weather_log = Path(project_root) / "weather_service.log"
        try:
            with open(weather_log, "a") as f:
                subprocess.Popen([sys.executable, "-m", "rpi.services.weather_service"], 
                                 cwd=project_root, stdout=f, stderr=f, start_new_session=True)
            print("  Weather Service started.")
        except Exception as e:
            print(f"  Failed to start Weather Service: {e}")
    else:
        print("  Weather Service is already running.")
    
    print("--- Background Services Check Complete ---\n")

def publish_actuator_command(cmds):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        c.connect("127.0.0.1", 1883, 60)
        c.loop_start()

        full_payload = {"ts": now_kst_iso(), "source": "sfes_lab_ui", **cmds}
        res = c.publish("sf/gh1/actuators/cmd", json.dumps(full_payload))
        res.wait_for_publish(timeout=3)

        if res.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError("MQTT publish failed")
    finally:
        c.loop_stop()
        c.disconnect()

def run_window_startup_calibration():
    try:
        print("Starting window startup calibration...")
        publish_actuator_command({
            "window_1_cmd": "open",
            "window_2_cmd": "open",
        })
        time.sleep(5)
        publish_actuator_command({
            "window_1_cmd": "stop",
            "window_2_cmd": "stop",
        })
        print("Window startup calibration complete.")
    except Exception as e:
        print(f"Window startup calibration failed: {e}")

def start_window_startup_calibration_once():
    global calibration_started
    if calibration_started:
        return
    calibration_started = True
    threading.Thread(target=run_window_startup_calibration, daemon=True).start()

@app.on_event("startup")
def startup_event():
    # Ensure DB is initialized
    try:
        p = monthly_db_path(DEFAULT_DB_DIR)
        print(f"Initializing DB: {p}")
        conn = connect_db(p)
        init_db(conn)
        conn.close()
        print("DB Initialization successful.")
    except Exception as e:
        print(f"DB Initialization failed: {e}")
    
    start_background_services()
    start_window_startup_calibration_once()

# --- DB Helpers (Connection Pooling) ---
_db_conn = None
_db_conn_path = None
_db_lock = threading.Lock()

def _get_read_conn():
    """월별 DB에 대한 캐싱된 읽기 연결을 반환. WAL 모드로 읽기 성능 향상."""
    global _db_conn, _db_conn_path
    p = monthly_db_path(DEFAULT_DB_DIR)
    if not p.exists():
        return None
    with _db_lock:
        if _db_conn is None or _db_conn_path != p:
            if _db_conn is not None:
                try: _db_conn.close()
                except: pass
            _db_conn = sqlite3.connect(str(p), check_same_thread=False)
            _db_conn.row_factory = sqlite3.Row
            _db_conn.execute("PRAGMA journal_mode=WAL")
            _db_conn.execute("PRAGMA synchronous=NORMAL")
            _db_conn_path = p
        return _db_conn

def _q(sql, params=(), one=False):
    conn = _get_read_conn()
    if conn is None:
        return None if one else []
    with _db_lock:
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
    """Legacy endpoint: get sensor history by minutes."""
    kst = timezone(timedelta(hours=9))
    cutoff = (datetime.now(kst) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    return _q("SELECT * FROM sensor_snapshot WHERE greenhouse='gh1' AND ts>=? ORDER BY ts", (cutoff,))

@app.get("/api/history/sensors")
def get_sensor_history(start: str = None, end: str = None):
    """Get sampled sensor_snapshot data to prevent UI lag."""
    if not start or not end:
        kst = timezone(timedelta(hours=9))
        end_dt = datetime.now(kst)
        start_dt = end_dt - timedelta(hours=1)
        start = start_dt.isoformat(timespec="seconds")
        end = end_dt.isoformat(timespec="seconds")

    # 1. 전체 데이터 개수 확인
    count_res = _q(
        "SELECT COUNT(*) as cnt FROM sensor_snapshot WHERE greenhouse='gh1' AND ts>=? AND ts<=?",
        (start, end), one=True
    )
    total_count = count_res['cnt'] if count_res else 0

    # 2. 데이터가 1,000개를 넘으면 샘플링 (id % N == 0 방식 사용)
    if total_count > 1000:
        step = total_count // 1000
        return _q(
            f"SELECT * FROM sensor_snapshot WHERE greenhouse='gh1' AND ts>=? AND ts<=? AND (id % {step} = 0) ORDER BY ts",
            (start, end)
        )
    
    return _q(
        "SELECT * FROM sensor_snapshot WHERE greenhouse='gh1' AND ts>=? AND ts<=? ORDER BY ts",
        (start, end)
    )

@app.get("/api/history/weather")
def get_weather_history(start: str = None, end: str = None):
    """Get weather data between start and end ISO timestamps."""
    if not start or not end:
        kst = timezone(timedelta(hours=9))
        end_dt = datetime.now(kst)
        start_dt = end_dt - timedelta(hours=1)
        start = start_dt.isoformat(timespec="seconds")
        end = end_dt.isoformat(timespec="seconds")
    return _q(
        "SELECT * FROM weather WHERE greenhouse='gh1' AND ts>=? AND ts<=? ORDER BY ts",
        (start, end)
    )

class CommandPayload(BaseModel):
    cmds: Dict[str, Any]
    
@app.post("/api/command")
def send_command(payload: CommandPayload):
    try:
        publish_actuator_command(payload.cmds)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

arduino_relay = None

class PowerPayload(BaseModel):
    state: str

@app.post("/api/arduino/power")
def set_arduino_power(payload: PowerPayload):
    global arduino_relay
    try:
        from gpiozero import OutputDevice
        if arduino_relay is None:
            # 객체를 전역에 유지하여 핀 상태 초기화 방지
            arduino_relay = OutputDevice(17, active_high=True, initial_value=None)
            
        if payload.state == "on":
            arduino_relay.on()
        else:
            arduino_relay.off()
            
        return {"status": "success", "state": payload.state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def save_settings(settings: Dict[str, str]):
    conn = _get_read_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB not available")
    try:
        with _db_lock:
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
