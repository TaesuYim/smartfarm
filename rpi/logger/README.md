# MQTT Logger

SmartFarm MQTT messages are stored in monthly SQLite DB files.

Current production greenhouse: `GH1`.

The logger writes each MQTT message immediately when it is received. The configurable interval in the UI is the sensor hub measurement/publish interval, not a delayed DB write interval.

Monthly DB filename:

```text
smartfarm_YYYY_MM.sqlite3
```

## Run

```powershell
python -m rpi.logger.mqtt_logger --db smartfarm_2026_04.sqlite3 --host 127.0.0.1 --port 1883
```

## Subscribed topics

- `sf/gh1/sensors/snapshot`
  - Stored in `sensor_snapshot`
- `sf/gh1/actuators/state`
  - Stored in `actuator_state`
- `sf/gh1/actuators/heartbeat`
  - Stored in `heartbeat`

Debug-only ADS raw topics may remain available during development, but the production UI uses complete `sensor_snapshot` rows.
