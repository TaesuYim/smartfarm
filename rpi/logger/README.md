# MQTT Logger

ADS1115 MQTT messages and SmartFarm sensor snapshots are stored in SQLite.

## Run

```powershell
python -m rpi.logger.mqtt_logger --db smartfarm.sqlite3 --host 127.0.0.1 --port 1883
```

## Subscribed topics

- `sensor/ads1115_+/+/+`
  - Example from `rpi/tests/integration/test_sensor_to_mqtt.py`:
    - `sensor/ads1115_0x49/a0/raw`
    - `sensor/ads1115_0x49/a0/voltage`
  - Stored in `ads_reading`
- `sf/+/sensors/snapshot`
  - Stored in `sensor_snapshot`
