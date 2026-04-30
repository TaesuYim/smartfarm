import urllib.request
import urllib.parse
import urllib.error
import csv
import os

params = {
    "tm": "202211300900",
    "stn": "146",
    "help": "0",
    "authKey": "zLEb4lzhRtixG-Jc4VbY0g"
}

base_url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
url = base_url + "?" + urllib.parse.urlencode(params)

save_path = "weather_data.csv"

try:
    with urllib.request.urlopen(url) as response:
        text = response.read().decode("utf-8", errors="ignore")

    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    values = lines[-1].split()

    weather = {
        "time": values[0] if len(values) > 0 else "",
        "station": values[1] if len(values) > 1 else "",
        "wind_dir": values[2] if len(values) > 2 else "",
        "wind_speed": values[3] if len(values) > 3 else "",
        "rainfall": values[10] if len(values) > 10 else "",
        "temperature": values[11] if len(values) > 11 else "",
        "dew_point": values[12] if len(values) > 12 else "",
        "humidity": values[13] if len(values) > 13 else "",
        "pressure": values[7] if len(values) > 7 else "",
        "sea_pressure": values[8] if len(values) > 8 else "",
    }

    file_exists = os.path.exists(save_path)

    with open(save_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=weather.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(weather)

    print("saved:", save_path)
    print(weather)

except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print(e.read().decode("utf-8", errors="ignore"))
except Exception as e:
    print("ERROR:", e)
