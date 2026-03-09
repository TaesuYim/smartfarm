import board
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)

ads1 = ADS.ADS1115(i2c, address=0x49)

ch0 = AnalogIn(ads1, 0)

while True:
    print("A0 raw:", ch0.value, "V:", round(ch0.voltage, 3))
    time.sleep(0.2)
