import board
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

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
    ch_4b_0 = AnalogIn(ads_4b, 0)
    ch_4b_1 = AnalogIn(ads_4b, 1)
    ch_4b_2 = AnalogIn(ads_4b, 2)
    ch_4b_3 = AnalogIn(ads_4b, 3)
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x4B: {e}")
    ads_4b = None

# ==========================================
# Sensor 2: Address 0x49
# A0: CO2
# A1: Light
# A2: Soil Moisture 1
# A3: Soil Moisture 2
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
# A0: Soil Moisture 3
# A1: Soil Moisture 4
# A2: Soil Moisture 5
# A3: Soil Moisture 6
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

# ==========================================
# Sensor 4: Address 0x4A
# A0: Future use
# A1: Future use
# A2: Future use
# A3: Future use
# ==========================================
try:
    ads_4a = ADS.ADS1115(i2c, address=0x4a)
    ch_4a_0 = AnalogIn(ads_4a, 0)
    ch_4a_1 = AnalogIn(ads_4a, 1)
    ch_4a_2 = AnalogIn(ads_4a, 2)
    ch_4a_3 = AnalogIn(ads_4a, 3)
except Exception as e:
    print(f"Failed to initialize ADS1115 at 0x4A: {e}")
    ads_4a = None


print("Starting to read 16 channels from 4 ADS1115 sensors...")

while True:
    print("=" * 50)
    
    # Read 0x4B
    if ads_4b:
        try:
            print(f"[0x4B] A0: {ch_4b_0.value:5d} | {ch_4b_0.voltage:.3f}V (Temperature Bottom)")
            print(f"[0x4B] A1: {ch_4b_1.value:5d} | {ch_4b_1.voltage:.3f}V (Humidity Bottom)")
            print(f"[0x4B] A2: {ch_4b_2.value:5d} | {ch_4b_2.voltage:.3f}V (Temperature Top)")
            print(f"[0x4B] A3: {ch_4b_3.value:5d} | {ch_4b_3.voltage:.3f}V (Humidity Top)")
        except Exception as e:
            print(f"[0x4B] Error reading: {e}")
    
    # Read 0x49
    if ads_49:
        try:
            print(f"[0x49] A0: {ch_49_0.value:5d} | {ch_49_0.voltage:.3f}V (CO2)")
            print(f"[0x49] A1: {ch_49_1.value:5d} | {ch_49_1.voltage:.3f}V (Light)")
            print(f"[0x49] A2: {ch_49_2.value:5d} | {ch_49_2.voltage:.3f}V (Soil Moisture 1)")
            print(f"[0x49] A3: {ch_49_3.value:5d} | {ch_49_3.voltage:.3f}V (Soil Moisture 2)")
        except Exception as e:
            print(f"[0x49] Error reading: {e}")

    # Read 0x48
    if ads_48:
        try:
            print(f"[0x48] A0: {ch_48_0.value:5d} | {ch_48_0.voltage:.3f}V (Soil Moisture 3)")
            print(f"[0x48] A1: {ch_48_1.value:5d} | {ch_48_1.voltage:.3f}V (Soil Moisture 4)")
            print(f"[0x48] A2: {ch_48_2.value:5d} | {ch_48_2.voltage:.3f}V (Soil Moisture 5)")
            print(f"[0x48] A3: {ch_48_3.value:5d} | {ch_48_3.voltage:.3f}V (Soil Moisture 6)")
        except Exception as e:
            print(f"[0x48] Error reading: {e}")

    # Read 0x4A
    if ads_4a:
        try:
            print(f"[0x4A] A0: {ch_4a_0.value:5d} | {ch_4a_0.voltage:.3f}V (Future use)")
            print(f"[0x4A] A1: {ch_4a_1.value:5d} | {ch_4a_1.voltage:.3f}V (Future use)")
            print(f"[0x4A] A2: {ch_4a_2.value:5d} | {ch_4a_2.voltage:.3f}V (Future use)")
            print(f"[0x4A] A3: {ch_4a_3.value:5d} | {ch_4a_3.voltage:.3f}V (Future use)")
        except Exception as e:
            print(f"[0x4A] Error reading: {e}")

    time.sleep(1.0)
