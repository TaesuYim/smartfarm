import board
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)

# ==========================================
# Sensor 1: Address 0x4B
# A0: Future use
# A1: Future use
# A2: Soil moisture sensor
# A3: Future use
# ==========================================
try:
    ads_4b = ADS.ADS1115(i2c, address=0x4b)
    ch_4b_0 = AnalogIn(ads_4b, 0)
    ch_4b_1 = AnalogIn(ads_4b, 1)
    ch_4b_2 = AnalogIn(ads_4b, 2)
    ch_4b_3 = AnalogIn(ads_4b, 3)
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x4B: {e}")
    ads_4b = None

# ==========================================
# Sensor 2: Address 0x49
# A0: Temperature sensor
# A1: Humidity sensor
# A2: Future use
# A3: Future use
# ==========================================
try:
    ads_49 = ADS.ADS1115(i2c, address=0x49)
    ch_49_0 = AnalogIn(ads_49, 0)
    ch_49_1 = AnalogIn(ads_49, 1)
    ch_49_2 = AnalogIn(ads_49, 2)
    ch_49_3 = AnalogIn(ads_49, 3)
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x49: {e}")
    ads_49 = None

# ==========================================
# Sensor 3: Address 0x48
# A0: Future use
# A1: Future use
# A2: Future use
# A3: Future use
# ==========================================
try:
    ads_48 = ADS.ADS1115(i2c, address=0x48)
    ch_48_0 = AnalogIn(ads_48, 0)
    ch_48_1 = AnalogIn(ads_48, 1)
    ch_48_2 = AnalogIn(ads_48, 2)
    ch_48_3 = AnalogIn(ads_48, 3)
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x48: {e}")
    ads_48 = None


print("Starting to read 12 channels from 3 ADS1115 sensors...")

while True:
    print("=" * 50)
    
    # Read 0x4B
    if ads_4b:
        try:
            print(f"[0x4B] A0: {ch_4b_0.value:5d} | {ch_4b_0.voltage:.3f}V (Future use)")
            print(f"[0x4B] A1: {ch_4b_1.value:5d} | {ch_4b_1.voltage:.3f}V (Future use)")
            print(f"[0x4B] A2: {ch_4b_2.value:5d} | {ch_4b_2.voltage:.3f}V (Soil moisture sensor)")
            print(f"[0x4B] A3: {ch_4b_3.value:5d} | {ch_4b_3.voltage:.3f}V (Future use)")
        except Exception as e:
            print(f"[0x4B] Error reading: {e}")
    
    # Read 0x49
    if ads_49:
        try:
            print(f"[0x49] A0: {ch_49_0.value:5d} | {ch_49_0.voltage:.3f}V (Temperature sensor)")
            print(f"[0x49] A1: {ch_49_1.value:5d} | {ch_49_1.voltage:.3f}V (Humidity sensor)")
            print(f"[0x49] A2: {ch_49_2.value:5d} | {ch_49_2.voltage:.3f}V (Future use)")
            print(f"[0x49] A3: {ch_49_3.value:5d} | {ch_49_3.voltage:.3f}V (Future use)")
        except Exception as e:
            print(f"[0x49] Error reading: {e}")

    # Read 0x48
    if ads_48:
        try:
            print(f"[0x48] A0: {ch_48_0.value:5d} | {ch_48_0.voltage:.3f}V (Future use)")
            print(f"[0x48] A1: {ch_48_1.value:5d} | {ch_48_1.voltage:.3f}V (Future use)")
            print(f"[0x48] A2: {ch_48_2.value:5d} | {ch_48_2.voltage:.3f}V (Future use)")
            print(f"[0x48] A3: {ch_48_3.value:5d} | {ch_48_3.voltage:.3f}V (Future use)")
        except Exception as e:
            print(f"[0x48] Error reading: {e}")

    time.sleep(1.0)
