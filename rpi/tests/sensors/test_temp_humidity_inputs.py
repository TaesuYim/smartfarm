import board
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Temperature & Humidity Sensor (analog voltage output, 0~3.3V range)
# Three 10k-ohm resistors are used as a voltage divider, tapping 3.3V into the ADS1115.
# ADS1115 at I2C address 0x49:
#   A0 -> Temperature  :  0 V = -19.9 °C  |  3.3 V = 60.0 °C
#   A1 -> Humidity     :  0 V =   0.0 %RH |  3.3 V = 99.9 %RH
#
# Linear conversion formulas:
#   temp (°C)  = V / 3.3 * (60.0 - (-19.9)) + (-19.9)
#   humi (%RH) = V / 3.3 * 99.9

V_REF_TEMP = 3.784  # Calibrated for: ~2.226 V -> 27.1 °C
V_REF_HUMI = 5.747  # Calibrated for: 1.208 V -> 21.0 %RH

TEMP_MIN = -19.9  # °C at 0 V
TEMP_MAX =  60.0  # °C at 3.3 V

HUMI_MIN =   0.0  # %RH at 0 V
HUMI_MAX =  99.9  # %RH at 3.3 V


def voltage_to_temperature(voltage):
    """Convert ADS1115 voltage to temperature in °C."""
    temp = voltage / V_REF_TEMP * (TEMP_MAX - TEMP_MIN) + TEMP_MIN
    return max(TEMP_MIN, min(TEMP_MAX, round(temp, 1)))


def voltage_to_humidity(voltage):
    """Convert ADS1115 voltage to relative humidity in %RH."""
    humi = voltage / V_REF_HUMI * (HUMI_MAX - HUMI_MIN) + HUMI_MIN
    return max(HUMI_MIN, min(HUMI_MAX, round(humi, 1)))


i2c = busio.I2C(board.SCL, board.SDA)

# ADS1115 at I2C address 0x49
ads = ADS.ADS1115(i2c, address=0x49)
ch_temp = AnalogIn(ads, 0)  # A0 - Temperature
ch_humi = AnalogIn(ads, 1)  # A1 - Humidity

print("Temperature & Humidity Sensor Test (ADS1115 @ 0x49)")
print("Resistor: 10k Ω x 3 (voltage divider, 3.3V ref)")
print("-" * 50)

while True:
    temp = voltage_to_temperature(ch_temp.voltage)
    humi = voltage_to_humidity(ch_humi.voltage)
    print(f"Temperature: {temp:.1f} °C  |  Humidity: {humi:.1f} %RH")
    time.sleep(1.0)
