import os, sys, time, json, sqlite3, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import closing
from dotenv import load_dotenv

# Path setup
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rpi.logger.db import monthly_db_path, DEFAULT_DB_DIR, init_db, connect_db

# Load .env
load_dotenv(Path(project_root) / ".env")

KST = timezone(timedelta(hours=9))
BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

def _db_path():
    return monthly_db_path(DEFAULT_DB_DIR)

def parse_float(value):
    if value in (None, "", "-9", "-9.0"): return None
    try: return float(value)
    except: return None

def parse_kma_response(text):
    header = None
    data_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped: continue
        if stripped.startswith("#"):
            # 헤더 줄 찾기
            if "YYMMDDHHMI" in stripped and "STN" in stripped:
                header = stripped.lstrip("#").strip().split()
            continue
        data_lines.append(stripped)
    
    if not header or not data_lines: return None
    
    values = data_lines[-1].split()
    # 중복된 헤더가 있을 수 있으므로 인덱스를 활용해 매핑
    record = {}
    for i, h in enumerate(header):
        if i < len(values):
            # 이미 존재하는 키라면 무시하거나 덮어씀 (필요한 값은 보통 앞에 있음)
            if h not in record:
                record[h] = values[i]
    return record

def fetch_and_save():
    auth_key = os.getenv("KMA_SERVICE_KEY")
    if not auth_key:
        print("Error: KMA_SERVICE_KEY not found in .env")
        return

    # 광주 지점(156) 기준 시간 관측 데이터 조회
    now = datetime.now(KST)
    # 기상청 ASOS 데이터는 보통 매시 10분 이후에 안정적으로 올라옴
    obs_time = now.replace(minute=0, second=0, microsecond=0)
    if now.minute < 15:
        obs_time -= timedelta(hours=1)

    params = {
        "tm": obs_time.strftime("%Y%m%d%H%M"),
        "stn": "156", # 광주
        "help": "1",
        "authKey": auth_key
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
        
        record = parse_kma_response(text)
        if not record:
            print(f"[{datetime.now()}] No valid record found. Raw response snippet: {text[:100]}")
            return

        # Mapping to DB (weather table)
        data = {
            "greenhouse": "gh1",
            "ts": datetime.strptime(record["YYMMDDHHMI"], "%Y%m%d%H%M").replace(tzinfo=KST).isoformat(timespec="seconds"),
            "ta": parse_float(record.get("TA")),
            "hm": parse_float(record.get("HM")),
            "rn": parse_float(record.get("RN")),
            "ws": parse_float(record.get("WS")),
            "icsr": parse_float(record.get("SI") or record.get("ICSR")), 
            "ss": parse_float(record.get("SS")),
            "fetched_at": datetime.now(KST).isoformat(timespec="seconds")
        }

        # Save to DB
        db_p = _db_path()
        if not db_p.exists():
            c = connect_db(db_p); init_db(c); c.close()
            
        with closing(sqlite3.connect(db_p)) as conn:
            # 1. Save to weather history table
            cols = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            sql = f"INSERT OR REPLACE INTO weather ({cols}) VALUES ({placeholders})"
            conn.execute(sql, list(data.values()))
            
            # 2. Update ui_latest for real-time dashboard
            ui_data = {
                "ta": data["ta"], "hm": data["hm"], "rn": data["rn"], "ws": data["ws"],
                "icsr": data["icsr"], "ss": data["ss"], "weather_ts": data["ts"],
                "weather_fetched_at": data["fetched_at"],
                "updated_at": datetime.now(KST).isoformat(timespec="seconds")
            }
            set_clause = ", ".join([f"{k}=?" for k in ui_data.keys()])
            sql_ui = f"UPDATE ui_latest SET {set_clause} WHERE greenhouse='gh1'"
            conn.execute(sql_ui, list(ui_data.values()))
            
            conn.commit()
        
        print(f"[{datetime.now()}] Weather data saved: {data['ts']}, Temp={data['ta']}")

    except Exception as e:
        print(f"[{datetime.now()}] Error fetching weather: {e}")

def main():
    print("Starting Weather Service (KMA ASOS 156 - Gwangju)...")
    interval = int(os.getenv("WEATHER_FETCH_INTERVAL_MIN", 60)) * 60
    while True:
        fetch_and_save()
        time.sleep(interval)

if __name__ == "__main__":
    main()
