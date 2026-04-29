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

# ==========================================
# Sensor 1: Address 0x4B
# A0: Temperature (Bottom)
# A1: Humidity (Bottom)
# A2: Temperature (Top)
# A3: Humidity (Top)
# ==========================================
try:
    ads_4b = ADS.ADS1115(i2c, address=0x4b)
    ch_4b = [AnalogIn(ads_4b, i) for i in range(4)]
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x4B: {e}")
    ads_4b = None
    ch_4b = []

# ==========================================
# Sensor 2: Address 0x49
# A0: CO2
# A1: Light
# A2: Soil Moisture 1
# A3: Soil Moisture 2
# ==========================================
try:
    ads_49 = ADS.ADS1115(i2c, address=0x49)
    ch_49 = [AnalogIn(ads_49, i) for i in range(4)]
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x49: {e}")
    ads_49 = None
    ch_49 = []

# ==========================================
# Sensor 3: Address 0x48
# A0: Soil Moisture 3
# A1: Soil Moisture 4
# A2: Soil Moisture 5
# A3: Soil Moisture 6
# ==========================================
try:
    ads_48 = ADS.ADS1115(i2c, address=0x48)
    ch_48 = [AnalogIn(ads_48, i) for i in range(4)]
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x48: {e}")
    ads_48 = None
    ch_48 = []

# ==========================================
# Sensor 4: Address 0x4A
# A0: Future use
# A1: Future use
# A2: Future use
# A3: Future use
# ==========================================
try:
    ads_4a = ADS.ADS1115(i2c, address=0x4a)
    ch_4a = [AnalogIn(ads_4a, i) for i in range(4)]
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x4A: {e}")
    ads_4a = None
    ch_4a = []

# Map: (ads_object, channels_list, address_hex_string)
sensors = [
    (ads_4b, ch_4b, "4B"),
    (ads_49, ch_49, "49"),
    (ads_48, ch_48, "48"),
    (ads_4a, ch_4a, "4A"),
]

period = 1.0 / RATE

print("Publishing 16 channels from 4 ADS1115 sensors to MQTT...")

while True:
    for ads, channels, addr in sensors:
        if ads is None:
            continue
        try:
            for i, ch in enumerate(channels):
                # 채널 전환 시 안정화를 위해 첫 번째 값은 무시하고 짧은 딜레이 후 다시 읽습니다.
                _ = ch.voltage
                time.sleep(0.05)
                
                v = ch.voltage
                val = ch.value
                topic_base = f"sensor/ads1115_0x{addr}/a{i}"
                client.publish(f"{topic_base}/raw", int(val))
                client.publish(f"{topic_base}/voltage", float(v))
                print(f"[0x{addr}] A{i}: {val:5d} | {v:.3f}V")
        except Exception as e:
            print(f"[0x{addr}] Error reading: {e}")

    print("-" * 50)
    time.sleep(period)
