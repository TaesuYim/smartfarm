// Circulation Fan PWM Control Test
// Board: Arduino UNO R4 WiFi
// Output: D3 (connected via MOSFET to Fan)
//
// PWM Frequency config: 20 kHz
// Note: UNO R4 does not support analogWriteFreq(). We use the low-level FspTimer
// (or the PwmOut class) to set custom frequencies. Here we use the standard
// analogWrite but change the timer frequency using the Renesas core API.

#include "pwm.h" // Required for UNO R4 PWM API

const int FAN_PIN = 3;
const unsigned int PWM_FREQ = 20000; // 20 kHz

// For UNO R4, we can set PWM frequency using the PwmOut class
PwmOut pwm(FAN_PIN);

void setFanSpeed(int percentage) {
  // Clamp percentage from 0 to 100
  if (percentage < 0) percentage = 0;
  if (percentage > 100) percentage = 100;

  // User testing indicates the fan reaches max practical speed around 200/2400 duty cycle at 20kHz
  // Map 0-100% to 0-200. Since we use a float for pulse width (0.0 to 1.0),
  // 2400 is the hardware Top, so 200/2400 = 0.08333 (8.33% duty cycle max)
  float maxDuty = 200.0 / 2400.0;
  float dutyCycle = (percentage / 100.0) * maxDuty;
  
  pwm.pulse_perc(dutyCycle * 100.0);

  Serial.print("Fan Speed set to: ");
  Serial.print(percentage);
  Serial.print("% (Duty Cycle applied: ");
  Serial.print(dutyCycle * 100.0, 3);
  Serial.println("%) [Max corresponds to timer top ~200/2400]");
}

void setup() {
  Serial.begin(115200);
  delay(2000); // Give time to open Serial Monitor
  
  Serial.println("Starting Circulation Fan PWM Test (UNO R4 PwmOut API)...");
  Serial.print("Target Frequency: ");
  Serial.print(PWM_FREQ / 1000);
  Serial.println(" kHz");

  // Initialize PWM.
  // PwmOut::begin(float period, float pulse) takes duty cycle configuration.
  // Alternatively, providing raw period/pulse or using basic begin() followed by setting value.
  // 1 / 20kHz = 50 microseconds. 
  // For R4 PwmOut, usually we use begin() then set parameters, or begin(period, pulse).
  pwm.begin();
  pwm.period_us(50); // 50us period = 20,000 Hz
  pwm.pulse_perc(0.0); // 0% duty initially
  
  Serial.println("Enter a number between 0 and 100 to set fan speed percentage.");

  // Test starting at 50% speed
  setFanSpeed(0);
}

void loop() {
  // Direct interactive test from Serial Monitor
  if (Serial.available() > 0) {
    // Read the string until newline to avoid empty parseInt() timeouts returning 0
    String inputStr = Serial.readStringUntil('\n');
    inputStr.trim(); // Remove any \r or spaces
    
    if (inputStr.length() > 0) {
      int inputVal = inputStr.toInt();
      
      // Valid input 0-100
      if (inputVal >= 0 && inputVal <= 100) {
        setFanSpeed(inputVal);
      } else { 
        Serial.println("Invalid input! Please enter 0 to 100.");
      }
    }
  }
}
