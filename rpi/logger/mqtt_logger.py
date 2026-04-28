import argparse
import json
import re

import sys
from pathlib import Path

# Add project root to sys.path to allow absolute imports when running as a script
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from rpi.logger.db import connect_db, init_db, insert_ads_reading, insert_sensor_snapshot


SNAPSHOT_TOPIC_RE = re.compile(r"^sf/(?P<greenhouse>gh[12])/sensors/snapshot$")
ADS_TOPIC_RE = re.compile(
    r"^sensor/ads1115_(?P<address>0x[0-9a-fA-F]+)/(?P<channel>a[0-3])/(?P<measurement>raw|voltage)$"
)


def parse_mqtt_payload(payload_bytes):
    text = payload_bytes.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return float(text)


def handle_mqtt_message(conn, topic, payload_bytes):
    snapshot_match = SNAPSHOT_TOPIC_RE.match(topic)
    if snapshot_match:
        payload = parse_mqtt_payload(payload_bytes)
        if not isinstance(payload, dict):
            raise ValueError(f"snapshot payload must be JSON object: {topic}")
        insert_sensor_snapshot(conn, snapshot_match.group("greenhouse"), payload)
        return "sensor_snapshot"

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


def build_on_message(conn):
    def on_message(client, userdata, msg):
        try:
            stored_table = handle_mqtt_message(conn, msg.topic, msg.payload)
            if stored_table:
                print(f"stored {msg.topic} -> {stored_table}")
            else:
                print(f"ignored topic: {msg.topic}")
        except Exception as exc:
            print(f"failed to store {msg.topic}: {exc}")

    return on_message


def main():
    parser = argparse.ArgumentParser(description="Store SmartFarm MQTT sensor messages into SQLite.")
    parser.add_argument("--db", default="smartfarm.sqlite3", help="SQLite database path")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT broker host")
    parser.add_argument("--port", default=1883, type=int, help="MQTT broker port")
    args = parser.parse_args()

    import paho.mqtt.client as mqtt

    conn = connect_db(args.db)
    init_db(conn)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = build_on_message(conn)
    client.connect(args.host, args.port, 60)
    client.subscribe("sensor/+/+/+")
    client.subscribe("sf/+/sensors/snapshot")
    print(f"logging MQTT messages from {args.host}:{args.port} into {args.db}")
    client.loop_forever()


if __name__ == "__main__":
    main()
