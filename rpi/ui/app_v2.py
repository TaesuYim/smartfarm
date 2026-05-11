"""SFES Lab v2 — Streamlit 기반 SmartFarm 탭 UI (부분 업데이트 최적화 버전).

실행:
    cd /home/pi/smartfarm/smartfarm
    streamlit run rpi/ui/app_v2.py
"""

import json, sys, sqlite3, subprocess, time, os
import pandas as pd
from pathlib import Path
from contextlib import closing
from datetime import datetime, timedelta, timezone

import streamlit as st
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rpi.logger.db import (
    DEFAULT_DB_DIR, SENSOR_VALUE_COLUMNS, ACTUATOR_VALUE_COLUMNS,
    WEATHER_VALUE_COLUMNS, monthly_db_path, now_kst_iso, connect_db, init_db,
)

KST = timezone(timedelta(hours=9))

# ---------------------------------------------------------------------------
# Background Services & GPIO
# ---------------------------------------------------------------------------
@st.cache_resource
def _start_background_services():
    def _is_running(pattern):
        if os.name == 'nt': return False # Windows에서는 중복 실행 방지를 st.cache_resource에 의존
        try: return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0
        except: return False

    if not _is_running("rpi.logger.mqtt_logger"):
        log_file = Path(project_root) / "mqtt_logger.log"
        with open(log_file, "a") as f:
            subprocess.Popen([sys.executable, "-m", "rpi.logger.mqtt_logger"], cwd=project_root, stdout=f, stderr=f, start_new_session=True)

    if not _is_running("rpi.sensor_hub.sensor_to_publish"):
        sensor_log = Path(project_root) / "sensor_pub.log"
        with open(sensor_log, "a") as f:
            cmd = [sys.executable, "-m", "rpi.sensor_hub.sensor_to_publish"]
            subprocess.Popen(cmd, cwd=project_root, stdout=f, stderr=f, start_new_session=True)
            
    if not _is_running("rpi.services.weather_service"):
        weather_log = Path(project_root) / "weather_service.log"
        with open(weather_log, "a") as f:
            subprocess.Popen([sys.executable, "-m", "rpi.services.weather_service"], cwd=project_root, stdout=f, stderr=f, start_new_session=True)

    def init_windows():
        time.sleep(3)
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        try:
            client.connect("127.0.0.1", 1883, 60)
            client.loop_start()
            ts = datetime.now(KST).isoformat(timespec="seconds")
            client.publish("sf/gh1/actuators/cmd", json.dumps({"ts": ts, "source": "ui_init", "window_1_cmd": "open", "window_2_cmd": "open"}))
            time.sleep(5)
            ts = datetime.now(KST).isoformat(timespec="seconds")
            client.publish("sf/gh1/actuators/cmd", json.dumps({"ts": ts, "source": "ui_init", "window_1_cmd": "stop", "window_2_cmd": "stop"}))
            client.disconnect()
        except: pass
    import threading
    threading.Thread(target=init_windows, daemon=True).start()
    return True

_start_background_services()

@st.cache_resource
def get_relay():
    if os.name == 'nt':
        # Windows에서는 가상의 릴레이 객체 반환
        class DummyRelay:
            def on(self): pass
            def off(self): pass
        return DummyRelay()
    try:
        from gpiozero import OutputDevice
        return OutputDevice(17, active_high=True, initial_value=True)
    except: return None

# ---------------------------------------------------------------------------
# Constants & DB
# ---------------------------------------------------------------------------
SENSOR_META = {
    "temp_pot_c":  ("온도(하부)", "°C", "🌡️"), "hum_pot_pct": ("습도(하부)", "%",  "💧"),
    "temp_top_c":  ("온도(상부)", "°C", "🌡️"), "hum_top_pct": ("습도(상부)", "%",  "💧"),
    "co2_ppm":     ("CO₂",       "ppm","💨"), "par_w_m2":    ("PAR",       "W/m²","☀️"),
    "soil_moisture_1_pct": ("토양①","%","🌱"), "soil_moisture_2_pct": ("토양②","%","🌱"),
    "soil_moisture_3_pct": ("토양③","%","🌱"), "soil_moisture_4_pct": ("토양④","%","🌱"),
    "soil_moisture_5_pct": ("토양⑤","%","🌱"), "soil_moisture_6_pct": ("토양⑥","%","🌱"),
}

DEFAULT_SETTINGS = {"ui_refresh_sec": "5", "measurement_interval_sec": "1", "heartbeat_timeout_sec": "10", "monitoring_graph_minutes": "60"}

def _db_path(): return monthly_db_path(DEFAULT_DB_DIR)

def _q(sql, params=(), one=False):
    p = _db_path()
    if not p.exists(): return None if one else []
    with closing(sqlite3.connect(p)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
    if one: return dict(rows[0]) if rows else None
    return [dict(r) for r in rows]

@st.cache_data(ttl=1)
def get_latest_cached(gh="gh1"):
    row = _q("SELECT * FROM ui_latest WHERE greenhouse=?", (gh,), one=True)
    return row or {}

@st.cache_data(ttl=1)
def get_heartbeat_cached(gh="gh1"):
    rows = _q("SELECT source,ts,uptime_ms FROM heartbeat WHERE greenhouse=? ORDER BY id DESC LIMIT 20", (gh,))
    d = {}
    for r in rows:
        src = r.get("source","?")
        if src not in d: d[src] = r
    return d

@st.cache_data(ttl=5)
def get_weather_cached(gh="gh1"):
    return _q("SELECT * FROM weather WHERE greenhouse=? ORDER BY id DESC LIMIT 1", (gh,), one=True)

@st.cache_data(ttl=30)
def get_history_cached(gh="gh1", minutes=60, start=None, end=None):
    if start and end: return _q("SELECT * FROM sensor_snapshot WHERE greenhouse=? AND ts>=? AND ts<=? ORDER BY ts", (gh,start,end))
    cutoff = (datetime.now(KST) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    return _q("SELECT * FROM sensor_snapshot WHERE greenhouse=? AND ts>=? ORDER BY ts", (gh,cutoff))

def get_settings():
    res = dict(DEFAULT_SETTINGS)
    for r in _q("SELECT key,value FROM app_setting"): res[r["key"]] = r["value"]
    return res

def save_settings(s):
    with closing(sqlite3.connect(_db_path())) as conn:
        for k,v in s.items():
            conn.execute("INSERT INTO app_setting(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (k,str(v),now_kst_iso()))
        conn.commit()
    st.cache_data.clear()

# ---------------------------------------------------------------------------
# MQTT & Controls
# ---------------------------------------------------------------------------
def _mqtt():
    if "mqtt" not in st.session_state:
        try:
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            c.connect("127.0.0.1", 1883, 60); c.loop_start(); st.session_state.mqtt = c
        except: st.session_state.mqtt = None
    return st.session_state.mqtt

def send_cmd(cmds, gh="gh1"):
    c = _mqtt()
    if not c: return False
    payload = {"ts": now_kst_iso(), "source": "sfes_lab_ui", **cmds}
    r = c.publish(f"sf/{gh}/actuators/cmd", json.dumps(payload))
    return r.rc == mqtt.MQTT_ERR_SUCCESS

def on_control_change():
    cmds = {}
    if "s_vent" in st.session_state: cmds["vent_fan_pwm_pct"] = st.session_state.s_vent
    if "s_h1" in st.session_state: cmds["heater_1_pwm_pct"] = st.session_state.s_h1
    if "s_h2" in st.session_state: cmds["heater_2_pwm_pct"] = st.session_state.s_h2
    if "s_cf1" in st.session_state: cmds["circ_fan_1_pwm_pct"] = st.session_state.s_cf1
    if "s_cf2" in st.session_state: cmds["circ_fan_2_pwm_pct"] = st.session_state.s_cf2
    if "t_mist" in st.session_state: cmds["mist_on"] = 1 if st.session_state.t_mist else 0
    if "s_pump" in st.session_state: cmds["pump_pwm_pct"] = st.session_state.s_pump
    for i in range(1, 7):
        if f"t_v{i}" in st.session_state: cmds[f"valve_pot_{i}_on"] = 1 if st.session_state[f"t_v{i}"] else 0
    if "t_fog" in st.session_state: cmds["valve_fog_on"] = 1 if st.session_state.t_fog else 0
    if "r_window_1_cmd" in st.session_state: cmds["window_1_cmd"] = st.session_state.r_window_1_cmd
    if "r_window_2_cmd" in st.session_state: cmds["window_2_cmd"] = st.session_state.r_window_2_cmd
    if "r_shading_screen_cmd" in st.session_state: cmds["shading_screen_cmd"] = st.session_state.r_shading_screen_cmd
    if "cp_led" in st.session_state:
        col = st.session_state.cp_led
        cmds["led_r"], cmds["led_g"], cmds["led_b"] = int(col[1:3],16), int(col[3:5],16), int(col[5:7],16)
    if "s_br" in st.session_state: cmds["led_brightness_pct"] = st.session_state.s_br
    if cmds:
        if send_cmd(cmds): st.toast("✅ 명령 전송됨")
        else: st.toast("❌ 전송 실패")

# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SFES Lab", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[data-testid="stApp"]{font-family:'Inter',sans-serif}
.header-title{font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,#10b981,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
[data-testid="stMetric"]{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:10px 14px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
.on{background:#10b981;box-shadow:0 0 6px #10b981}
.off{background:#ef4444;box-shadow:0 0 6px #ef4444}
.weather-box{background:linear-gradient(135deg,rgba(6,182,212,0.08),rgba(16,185,129,0.08));border:1px solid rgba(6,182,212,0.15);border-radius:12px;padding:14px;font-size:0.9rem;line-height:1.8}
</style>""", unsafe_allow_html=True)

settings = get_settings()
ref_sec = int(settings.get("ui_refresh_sec", 5))

# ----- Startup Sync (시작 후 12초 동안만 전체 새로고침하여 초기화 상태 동기화) -----
from streamlit_autorefresh import st_autorefresh
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

elapsed = time.time() - st.session_state.start_time
if elapsed < 12:
    st_autorefresh(interval=2000, key="init_sync_refresh")

# ----- Fragmented Header (부분 업데이트) -----
@st.fragment(run_every=ref_sec)
def header_fragment():
    h1,h2,h3 = st.columns([2,4,2])
    with h1: st.markdown('<p class="header-title">🌱 SFES Lab</p>', unsafe_allow_html=True)
    with h2: st.markdown(f"📅 **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")
    with h3:
        hb = get_heartbeat_cached()
        timeout = int(settings.get("heartbeat_timeout_sec", 10))
        now, html = datetime.now(KST), ""
        for name, src in [("Node1","arduino_node_1"),("Node2","arduino_node_2")]:
            on = False
            if src in hb:
                try:
                    last = datetime.fromisoformat(hb[src]["ts"])
                    if last.tzinfo is None: last = last.replace(tzinfo=KST)
                    on = (now - last).total_seconds() < timeout
                except: pass
            c = "on" if on else "off"
            html += f'<span class="dot {c}"></span>{name}&nbsp;&nbsp;'
        st.markdown(html, unsafe_allow_html=True)
    st.divider()

header_fragment()

# Tab Selection
if "active_tab" not in st.session_state: st.session_state.active_tab = "📊 모니터링"
tabs = ["📊 모니터링", "🎛️ 제어", "📈 그래프", "⚙️ 설정"]
tcols = st.columns(len(tabs))
for i, tname in enumerate(tabs):
    if tcols[i].button(tname, use_container_width=True, type="primary" if st.session_state.active_tab == tname else "secondary"):
        st.session_state.active_tab = tname
        st.rerun()

active = st.session_state.active_tab

# ----- Monitoring Tab (Fragmented) -----
@st.fragment(run_every=ref_sec)
def monitoring_tab_fragment():
    ui = get_latest_cached()
    st.markdown("##### 🌡️ 환경 센서")
    c1 = st.columns(6)
    for i, k in enumerate(["temp_pot_c","hum_pot_pct","temp_top_c","hum_top_pct","co2_ppm","par_w_m2"]):
        lbl,unit,ico = SENSOR_META[k]; v = ui.get(k) if ui else None
        with c1[i]: st.metric(f"{ico} {lbl}", f"{v:.1f} {unit}" if v is not None else "—")
    st.markdown("##### 🌱 토양수분")
    c2 = st.columns(6)
    for i in range(6):
        k = f"soil_moisture_{i+1}_pct"; lbl,unit,ico = SENSOR_META[k]; v = ui.get(k) if ui else None
        with c2[i]: st.metric(f"{ico} {lbl}", f"{v:.1f}{unit}" if v is not None else "—")
    l, c, r = st.columns([1.5, 1.2, 1.3])
    with l:
        w_ts = ui.get("weather_ts") if ui else None
        if w_ts:
            w = ui
            st.markdown(f'''
            <div class="weather-box" style="font-size: 1.05rem; line-height: 1.6;">
                <b>🌡️ 외기온</b> {w.get("ta","—")}°C &nbsp; <b>💧 외습도</b> {w.get("hm","—")}% &nbsp; <b>☔ 강수</b> {w.get("rn","—")}mm<br>
                <b>💨 풍속</b> {w.get("ws","—")}m/s &nbsp; <b>☀️ 일사</b> {w.get("icsr","—")}MJ/m² &nbsp; <b>🕐 일조</b> {w.get("ss","—")}hr
            </div>
            ''', unsafe_allow_html=True)
        else: st.info("데이터 대기 중...")
    with c:
        st.markdown("##### 📡 통신 상태")
        hb_ts = ui.get("heartbeat_ts") if ui else None
        timeout = int(settings.get("heartbeat_timeout_sec", 10)); now = datetime.now(KST)
        for name, src in [("Node1", "arduino_node_1"), ("Node2", "arduino_node_2")]:
            on = False
            if hb_ts:
                try:
                    last = datetime.fromisoformat(hb_ts)
                    if last.tzinfo is None: last = last.replace(tzinfo=KST)
                    on = (now - last).total_seconds() < timeout
                except: pass
            col = "#10b981" if on else "#ef4444"
            st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:{col};box-shadow:0 0 8px {col};margin-right:12px"></div><b>{name}</b></div>', unsafe_allow_html=True)
    with r:
        st.markdown("##### 🔌 전원")
        if "t_pwr" not in st.session_state: st.session_state.t_pwr = True
        
        def on_p_ch():
            # 콜백 내에서는 UI 요소를 직접 그리지 않고 로직만 수행
            rl = get_relay()
            if rl:
                state = st.session_state.t_arduino_pwr = st.session_state.t_pwr
                if state: rl.on()
                else: rl.off()
            else:
                st.session_state.pwr_err = True

        st.toggle("아두이노 전원", key="t_pwr", on_change=on_p_ch)

        # 에러가 발생했다면 본문에서 출력 (Fragment 안전 방식)
        if st.session_state.get("pwr_err"):
            st.error("⚠️ GPIO 접근 실패! (다른 프로그램 확인 필요)")
            if st.button("에러 닫기"): del st.session_state["pwr_err"]; st.rerun()
        elif "t_arduino_pwr" in st.session_state:
            st.toast(f"🔌 전원 {'ON' if st.session_state.t_arduino_pwr else 'OFF'}")
            del st.session_state["t_arduino_pwr"]
    st.caption(f"마지막 업데이트: {ui.get('sensor_ts','—') if ui else '—'}")

# ----- Render Tabs -----
if active == "📊 모니터링":
    monitoring_tab_fragment()

elif active == "🎛️ 제어":
    act = get_latest_cached()
    cL, cR = st.columns(2)
    with cL:
        st.markdown("##### 🌬️ 환기 · 난방")
        st.slider("환기팬", 0, 100, int(act.get("vent_fan_pwm_pct") or 0), key="s_vent", on_change=on_control_change)
        cc1,cc2 = st.columns(2)
        cc1.slider("히터1", 0, 100, int(act.get("heater_1_pwm_pct") or 0), key="s_h1", on_change=on_control_change)
        cc2.slider("히터2", 0, 100, int(act.get("heater_2_pwm_pct") or 0), key="s_h2", on_change=on_control_change)
        cc3,cc4 = st.columns(2)
        cc3.slider("순환팬1", 0, 100, int(act.get("circ_fan_1_pwm_pct") or 0), key="s_cf1", on_change=on_control_change)
        cc4.slider("순환팬2", 0, 100, int(act.get("circ_fan_2_pwm_pct") or 0), key="s_cf2", on_change=on_control_change)
        st.toggle("미스트", value=bool(act.get("mist_on",0)), key="t_mist", on_change=on_control_change)
    with cR:
        st.markdown("##### 💧 관수")
        st.slider("펌프", 0, 100, int(act.get("pump_pwm_pct") or 0), key="s_pump", on_change=on_control_change)
        st.caption("솔레노이드 밸브")
        vc = st.columns(4)
        for i in range(1,7):
            with vc[(i-1)%4]: st.toggle(f"화분{i}", value=bool(act.get(f"valve_pot_{i}_on",0)), key=f"t_v{i}", on_change=on_control_change)
        st.toggle("포깅", value=bool(act.get("valve_fog_on",0)), key="t_fog", on_change=on_control_change)
    cL2, cR2 = st.columns(2)
    with cL2:
        st.markdown("##### 🪟 창문 · 스크린")
        def fmt_win(x, is_win):
            if is_win: return {"open":"닫기", "stop":"정지", "close":"열기"}.get(x, x)
            return {"open":"열기", "stop":"정지", "close":"닫기"}.get(x, x)
        for lbl, k in [("창문1","window_1_cmd"),("창문2","window_2_cmd"),("차광스크린","shading_screen_cmd")]:
            cur, opts = act.get(k,"stop") or "stop", ["open","stop","close"]
            st.radio(lbl, opts, index=opts.index(cur) if cur in opts else 1, horizontal=True, key=f"r_{k}", format_func=lambda x, is_win=("창문" in lbl): fmt_win(x, is_win), on_change=on_control_change)
    with cR2:
        st.markdown("##### 💡 LED 조명")
        st.color_picker("RGB 색상", value="#ffffff", key="cp_led", on_change=on_control_change)
        st.slider("밝기", 0, 100, int(act.get("led_brightness_pct") or 0), key="s_br", on_change=on_control_change)

elif active == "📈 그래프":
    st.markdown("##### 📈 기간별 센서 추세")
    
    with st.form("graph_filter"):
        gc1, gc2, gc3 = st.columns([2, 3, 3])
        period = gc1.selectbox("조회 방식", ["최근 시간 기준", "직접 입력 (기간 지정)"], key="g_period")
        
        start_dt = end_dt = None
        
        if period == "최근 시간 기준":
            mins = gc2.number_input("조회 범위 (분)", 10, 10080, 60, step=10)
            st.caption("※ 버튼을 누른 시점의 데이터를 고정해서 가져옵니다.")
        else:
            c1, c2 = gc2.columns(2)
            sd = c1.date_input("시작일", key="g_sd")
            st_ = c2.time_input("시작시각", value=datetime.min.time(), key="g_st")
            
            c3, c4 = gc3.columns(2)
            ed = c3.date_input("종료일", key="g_ed")
            et_ = c4.time_input("종료시각", value=datetime.now(KST).time(), key="g_et")
            
            start_dt = datetime.combine(sd, st_).replace(tzinfo=KST).isoformat(timespec="seconds")
            end_dt = datetime.combine(ed, et_).replace(tzinfo=KST).isoformat(timespec="seconds")
        
        groups = gc3.multiselect("센서 그룹", ["온도","습도","CO₂","PAR","토양수분"], default=["온도","습도"], key="g_grp")
        submitted = st.form_submit_button("🔍 데이터 조회 (정적 모드)", type="primary", use_container_width=True)

    if submitted:
        if period == "최근 시간 기준":
            # 조회 시점의 시간을 끝점으로 고정하여 렉 방지
            now_fixed = datetime.now(KST)
            start_fixed = (now_fixed - timedelta(minutes=mins)).isoformat(timespec="seconds")
            end_fixed = now_fixed.isoformat(timespec="seconds")
            gdata = get_history_cached(start=start_fixed, end=end_fixed)
        else:
            gdata = get_history_cached(start=start_dt, end=end_dt)
            
        st.session_state.current_gdata = gdata
    else:
        gdata = st.session_state.get("current_gdata")

    if gdata:
        c_map = {"온도":["temp_pot_c","temp_top_c"],"습도":["hum_pot_pct","hum_top_pct"],"CO₂":["co2_ppm"],"PAR":["par_w_m2"],"토양수분":[f"soil_moisture_{i}_pct" for i in range(1,7)]}
        df = pd.DataFrame(gdata); df["ts"] = pd.to_datetime(df["ts"]); df = df.set_index("ts")
        for grp in groups:
            gcols = [c for c in c_map.get(grp,[]) if c in df.columns]
            if gcols: st.markdown(f"###### {grp}"); st.line_chart(df[gcols], height=200)
    elif not st.session_state.get("current_gdata"):
        st.info("조회 버튼을 눌러 고정된 시점의 데이터를 불러오세요.")

elif active == "⚙️ 설정":
    st.markdown("##### ⚙️ 시스템 설정")
    cur = get_settings(); sc1,sc2 = st.columns(2)
    v1 = sc1.number_input("화면 업데이트 주기 (초)", 1, 60, int(cur.get("ui_refresh_sec",5)))
    v2 = sc1.number_input("센서 측정 주기 (초)", 1, 60, int(cur.get("measurement_interval_sec",1)))
    v3 = sc2.number_input("Heartbeat 타임아웃 (초)", 5, 120, int(cur.get("heartbeat_timeout_sec",10)))
    v4 = sc2.number_input("모니터링 그래프 기간 (분)", 10, 1440, int(cur.get("monitoring_graph_minutes",60)))
    if st.button("💾 설정 저장", type="primary"):
        save_settings({"ui_refresh_sec":v1,"measurement_interval_sec":v2,"heartbeat_timeout_sec":v3,"monitoring_graph_minutes":v4})
        st.success("설정 저장 완료"); st.rerun()
    st.divider(); st.json({"db_path": str(_db_path()), "greenhouse": "gh1", "ver": "2.1-fragmented"})
