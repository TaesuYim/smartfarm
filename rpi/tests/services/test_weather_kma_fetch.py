import csv
from datetime import datetime, timedelta, timezone
import os
import urllib.error
import urllib.parse
import urllib.request


KST = timezone(timedelta(hours=9))
BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
SAVE_PATH = "weather_data.csv"


def current_observation_time(now=None):
    now = now or datetime.now(KST)
    observed = now.replace(minute=0, second=0, microsecond=0)
    if now.minute < 1:
        observed -= timedelta(hours=1)
    return observed


def iso_kst_from_kma_time(value):
    return datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=KST).isoformat(timespec="seconds")


def parse_float(value):
    if value in (None, "", "-9", "-9.0"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_latest_record(text):
    header = None
    data_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            candidate = stripped.lstrip("#").strip().split()
            if "YYMMDDHHMI" in candidate and "STN" in candidate:
                header = candidate
            continue
        data_lines.append(stripped)

    if not header or not data_lines:
        raise ValueError("KMA response does not contain a parsable header/data row")

    values = data_lines[-1].split()
    return dict(zip(header, values))


def build_weather_payload(record, fetched_at):
    qc_flags = {
        "ta": record.get("TA_QCFLG"),
        "hm": record.get("HM_QCFLG"),
        "rn": record.get("RN_QCFLG"),
        "ws": record.get("WS_QCFLG"),
        "icsr": record.get("ICSR_QCFLG") or record.get("SI_QCFLG"),
        "ss": record.get("SS_QCFLG"),
    }
    return {
        "ts": iso_kst_from_kma_time(record["YYMMDDHHMI"]),
        "fetched_at": fetched_at.isoformat(timespec="seconds"),
        "source": "kma",
        "station_id": record.get("STN"),
        "internal_temp_c": None,
        "internal_hum_pct": None,
        "ta": parse_float(record.get("TA")),
        "hm": parse_float(record.get("HM")),
        "rn": parse_float(record.get("RN")),
        "ws": parse_float(record.get("WS")),
        "icsr": parse_float(record.get("ICSR") or record.get("SI")),
        "ss": parse_float(record.get("SS")),
        "qc_flags": qc_flags,
    }


def main():
    observed_at = current_observation_time()
    fetched_at = datetime.now(KST)
    params = {
        "tm": observed_at.strftime("%Y%m%d%H%M"),
        "stn": "146",
        "help": "1",
        "authKey": "zLEb4lzhRtixG-Jc4VbY0g",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            text = response.read().decode("utf-8", errors="ignore")

        payload = build_weather_payload(parse_latest_record(text), fetched_at)
        file_exists = os.path.exists(SAVE_PATH)

        with open(SAVE_PATH, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=payload.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(payload)

        print("saved:", SAVE_PATH)
        print(payload)

    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print(e.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
