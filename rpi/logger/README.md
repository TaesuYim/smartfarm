# MQTT Logger

SmartFarm MQTT messages are stored immediately into monthly SQLite DB files.

Current production greenhouse: `GH1` (`gh1`). `GH2` is a future expansion target.

Monthly DB filename:

```text
smartfarm_YYYY_MM.sqlite3
```

## Run

Default monthly DB mode:

```powershell
python -m rpi.logger.mqtt_logger --db-dir data --host 127.0.0.1 --port 1883
```

Fixed DB file mode for debugging:

```powershell
python -m rpi.logger.mqtt_logger --db smartfarm_2026_05.sqlite3 --host 127.0.0.1 --port 1883
```

## Subscribed Topics

- `sf/gh1/sensors/snapshot`
  - Stored in `sensor_snapshot`, updates `ui_latest` sensor columns
- `sf/gh1/sensors/weather`
  - Stored in `weather`, updates `ui_latest` weather columns
- `sf/gh1/actuators/cmd`
  - Stored in `actuator_cmd`
- `sf/gh1/actuators/state`
  - Stored in `actuator_history`, updates `ui_latest` actuator columns
- `sf/gh1/actuators/heartbeat`
  - Stored in `heartbeat`, updates `ui_latest` heartbeat columns
- `sf/gh1/actuators/fan-rpm`
  - Stored in `fan_rpm`, updates `ui_latest` fan RPM columns
- `sensor/ads1115_*/+/raw`, `sensor/ads1115_*/+/voltage`
  - Stored in `ads_reading` for debugging

## Weather

The weather service should request KMA hourly data at `HH:01` for the `HH:00` observation. The logger stores both `ts` (observation time) and `fetched_at` (actual fetch time), plus internal temperature/humidity, KMA `ta`, `hm`, `rn`, `ws`, `icsr`, `ss`, and QC flags.
