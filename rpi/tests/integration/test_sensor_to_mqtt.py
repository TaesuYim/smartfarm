import time
import board
import busio
import paho.mqtt.client as mqtt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
ADDR = 0x49
RATE = 5

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=ADDR)
ch0 = AnalogIn(ads, 0)

period = 1.0 / RATE

while True:
    client.publish(f"sensor/ads1115_0x{ADDR:02X}/a0/raw", int(ch0.value))
    client.publish(f"sensor/ads1115_0x{ADDR:02X}/a0/voltage", float(ch0.voltage))
    print(ch0.value, ch0.voltage)
    time.sleep(period)
