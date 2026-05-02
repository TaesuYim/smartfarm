import argparse
import json
import re
import sys
from pathlib import Path

# Add project root to sys.path to allow absolute imports when running as a script
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from rpi.logger.db import (
    DEFAULT_DB_DIR,
    connect_db,
    init_db,
    insert_actuator_cmd,
    insert_actuator_state,
    insert_ads_reading,
    insert_fan_rpm,
    insert_heartbeat,
    insert_sensor_snapshot,
    insert_weather,
    monthly_db_path,
)

SNAPSHOT_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/sensors/snapshot$")
WEATHER_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/sensors/weather$")
ACTUATOR_CMD_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/actuators/cmd$")
ACTUATOR_STATE_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/actuators/state$")
HEARTBEAT_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/actuators/heartbeat$")
FAN_RPM_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/actuators/fan-rpm$")
ADS_TOPIC_RE = re.compile(
    r"^sensor/ads1115_(?P<address>0x[0-9a-fA-F]+)/(?P<channel>a[0-3])/(?P<measurement>raw|voltage)$"
)


class FixedDbManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = connect_db(self.db_path)
        init_db(self.conn)

    def get_connection(self):
        return self.conn

    @property
    def description(self):
        return str(self.db_path)

    def close(self):
        self.conn.close()


class MonthlyDbManager:
    def __init__(self, db_dir=DEFAULT_DB_DIR):
        self.db_dir = Path(db_dir)
        self.current_path = None
        self.conn = None

    def get_connection(self):
        db_path = monthly_db_path(self.db_dir)
        if self.conn is None or db_path != self.current_path:
            if self.conn is not None:
                self.conn.close()
            self.current_path = db_path
            self.conn = connect_db(db_path)
            init_db(self.conn)
            print(f"using monthly DB: {db_path}")
        return self.conn

    @property
    def description(self):
        return str(self.db_dir / "smartfarm_YYYY_MM.sqlite3")

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def parse_mqtt_payload(payload_bytes):
    text = payload_bytes.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return float(text)
        except ValueError:
            return text


def _parse_json_object(topic, payload_bytes):
    payload = parse_mqtt_payload(payload_bytes)
    if not isinstance(payload, dict):
        raise ValueError(f"payload must be JSON object: {topic}")
    return payload


def handle_mqtt_message(conn, topic, payload_bytes):
    snapshot_match = SNAPSHOT_TOPIC_RE.match(topic)
    if snapshot_match:
        insert_sensor_snapshot(
            conn,
            snapshot_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "sensor_snapshot"

    weather_match = WEATHER_TOPIC_RE.match(topic)
    if weather_match:
        insert_weather(
            conn,
            weather_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "weather"

    cmd_match = ACTUATOR_CMD_TOPIC_RE.match(topic)
    if cmd_match:
        insert_actuator_cmd(
            conn,
            cmd_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "actuator_cmd"

    state_match = ACTUATOR_STATE_TOPIC_RE.match(topic)
    if state_match:
        insert_actuator_state(
            conn,
            state_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "actuator_history"

    heartbeat_match = HEARTBEAT_TOPIC_RE.match(topic)
    if heartbeat_match:
        insert_heartbeat(
            conn,
            heartbeat_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "heartbeat"

    fan_rpm_match = FAN_RPM_TOPIC_RE.match(topic)
    if fan_rpm_match:
        insert_fan_rpm(
            conn,
            fan_rpm_match.group("greenhouse"),
            _parse_json_object(topic, payload_bytes),
        )
        return "fan_rpm"

    ads_match = ADS_TOPIC_RE.match(topic)
    if ads_match:
        value = parse_mqtt_payload(payload_bytes)
        insert_ads_reading(
            conn,
            {
                "source": "ads1115",
                "address": ads_match.group("address").lower(),
                "channel": ads_match.group("channel"),
                "measurement": ads_match.group("measurement"),
                "value": float(value),
            },
        )
        return "ads_reading"

    return None


def build_on_message(conn_or_provider):
    def on_message(client, userdata, msg):
        try:
            conn = conn_or_provider() if callable(conn_or_provider) else conn_or_provider
            stored_table = handle_mqtt_message(conn, msg.topic, msg.payload)
            if stored_table:
                print(f"stored {msg.topic} -> {stored_table}")
            else:
                print(f"ignored topic: {msg.topic}")
        except Exception as exc:
            print(f"failed to store {msg.topic}: {exc}")

    return on_message


def subscribe_topics(client):
    topics = (
        "sensor/+/+/+",
        "sf/+/sensors/snapshot",
        "sf/+/sensors/weather",
        "sf/+/actuators/cmd",
        "sf/+/actuators/state",
        "sf/+/actuators/heartbeat",
        "sf/+/actuators/fan-rpm",
    )
    for topic in topics:
        client.subscribe(topic)


def main():
    parser = argparse.ArgumentParser(description="Store SmartFarm MQTT messages into SQLite.")
    parser.add_argument("--db-dir", default=DEFAULT_DB_DIR, help="Directory for monthly SQLite DB files")
    parser.add_argument("--db", default=None, help="Use one fixed SQLite DB path instead of monthly DB files")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT broker host")
    parser.add_argument("--port", default=1883, type=int, help="MQTT broker port")
    args = parser.parse_args()

    import paho.mqtt.client as mqtt

    db_manager = FixedDbManager(args.db) if args.db else MonthlyDbManager(args.db_dir)
    db_manager.get_connection()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = build_on_message(db_manager.get_connection)
    client.connect(args.host, args.port, 60)
    subscribe_topics(client)
    print(f"logging MQTT messages from {args.host}:{args.port} into {db_manager.description}")

    try:
        client.loop_forever()
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
