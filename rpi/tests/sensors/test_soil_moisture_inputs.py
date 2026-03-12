import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# I2C Address and Pin configuration
I2C_ADDRESS = 0x4B
CHANNEL_INDEX = 2  # A2 pin

def main():
    try:
        # Initialize I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create ADS1115 object
        ads = ADS1115(i2c, address=I2C_ADDRESS)
        
        # Set Gain=1 (Max 4.096V)
        ads.gain = 1
        
        # Create analog input channel on A2
        chan = AnalogIn(ads, CHANNEL_INDEX)
        
        print("\n" + "="*45)
        print(" [Soil Moisture Sensor - Voltage Monitor] ")
        print(" Monitoring voltage on Pin A2 (0x4B)")
        print("="*45 + "\n")
        
        print(f"{'Channel':<10} | {'Voltage (V)'}")
        print("-" * 30)

        while True:
            # Only monitor and print the voltage value as requested
            voltage = chan.voltage
            print(f"A2 (0x4b)  | {voltage:>7.3f} V")
            
            time.sleep(1.0)

    except Exception as e:
        print(f"\n[Error] {e}")
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()
