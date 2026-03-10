import board
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# CO2 Sensor: MH-Z series (4~20mA current loop output, 0~2000 ppm range)
# A 150-ohm shunt resistor is used to convert current to voltage:
#   0 ppm  ->  4 mA * 150 Ω = 0.60 V
#   2000 ppm -> 20 mA * 150 Ω = 3.00 V
# Linear conversion formula:
#   ppm = (V - 0.60) / (3.00 - 0.60) * 2000

V_MIN = 0.60   # voltage at 0 ppm (4 mA through 150 Ω)
V_MAX = 3.00   # voltage at 2000 ppm (20 mA through 150 Ω)
PPM_MAX = 2000

def voltage_to_ppm(voltage):
    """Convert ADS1115 voltage reading to CO2 concentration in ppm."""
    ppm = (voltage - V_MIN) / (V_MAX - V_MIN) * PPM_MAX
    return max(0, min(PPM_MAX, round(ppm, 1)))

i2c = busio.I2C(board.SCL, board.SDA)

# ADS1115 at I2C address 0x49, CO2 sensor connected to channel A1
ads = ADS.ADS1115(i2c, address=0x49)
ch1 = AnalogIn(ads, 1)  # A1

print("CO2 Sensor Test (ADS1115 @ 0x49, A1)")
print("Shunt resistor: 150 Ω  |  Range: 0~2000 ppm")
print("-" * 45)

while True:
    voltage = ch1.voltage
    ppm = voltage_to_ppm(voltage)
    print(f"CO2: {ppm:.1f} ppm")
    time.sleep(1.0)
