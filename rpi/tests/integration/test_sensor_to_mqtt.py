# -*- coding: utf-8 -*-

import time
import board
import busio
import paho.mqtt.client as mqtt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
RATE = 1

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

i2c = busio.I2C(board.SCL, board.SDA)


def init_ads(address):
    try:
        ads = ADS.ADS1115(i2c, address=address)
        ads.data_rate = 128

        channels = [AnalogIn(ads, i) for i in range(4)]

        print("Initialized ADS1115 at 0x%02X" % address)
        return ads, channels

    except Exception as e:
        print("Failed to initialize ADS1115 at 0x%02X: %s" % (address, e))
        return None, []


ads_4b, ch_4b = init_ads(0x4B)
ads_49, ch_49 = init_ads(0x49)
ads_48, ch_48 = init_ads(0x48)
ads_4a, ch_4a = init_ads(0x4A)


sensors = [
    {
        "address": "4B",
        "ads": ads_4b,
        "channels": ch_4b,
        "names": [
            "temperature_bottom",
            "humidity_bottom",
            "temperature_top",
            "humidity_top",
        ],
    },
    {
        "address": "49",
        "ads": ads_49,
        "channels": ch_49,
        "names": [
            "co2",
            "light",
            "soil_moisture_1",
            "soil_moisture_2",
        ],
    },
    {
        "address": "48",
        "ads": ads_48,
        "channels": ch_48,
        "names": [
            "soil_moisture_3",
            "soil_moisture_4",
            "soil_moisture_5",
            "soil_moisture_6",
        ],
    },
    {
        "address": "4A",
        "ads": ads_4a,
        "channels": ch_4a,
        "names": [
            "future_0",
            "future_1",
            "future_2",
            "future_3",
        ],
    },
]


period = 1.0 / RATE

print("Publishing 16 channels from 4 ADS1115 sensors to MQTT...")


while True:
    loop_start = time.monotonic()

    for sensor in sensors:
        ads = sensor["ads"]
        channels = sensor["channels"]
        addr = sensor["address"]
        names = sensor["names"]

        if ads is None:
            continue

        try:
            for i, ch in enumerate(channels):
                val = ch.value
                v = val * ads.bits_to_volts

                sensor_name = names[i]

                topic_base = "sensor/ads1115_0x%s/a%d" % (addr, i)
                topic_name = "sensor/%s" % sensor_name

                client.publish(topic_base + "/raw", int(val))
                client.publish(topic_base + "/voltage", float(v))

                client.publish(topic_name + "/raw", int(val))
                client.publish(topic_name + "/voltage", float(v))

                print("[0x%s] A%d %-22s: %5d | %.3f V" % (
                    addr,
                    i,
                    sensor_name,
                    val,
                    v,
                ))

        except Exception as e:
            print("[0x%s] Error reading: %s" % (addr, e))

    print("-" * 50)

    elapsed = time.monotonic() - loop_start
    sleep_time = max(0, period - elapsed)
    time.sleep(sleep_time)