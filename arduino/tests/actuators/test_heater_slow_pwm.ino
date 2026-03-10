// Heater Time-Proportional PWM Test
// Board: Arduino UNO R4 WiFi
// Output: D9 (connected via MOSFET to Heater)
//
// Method: Software Time-Proportional PWM
// Principle: Within a fixed 'window' (e.g., 5 seconds), the heater is turned ON for a proportional amount of time.
// Example for 60%: 
//   - 5000ms * 60% = 3000ms ON
//   - 5000ms * 40% = 2000ms OFF

const int HEATER_PIN = 9;

unsigned long windowStartTime;
const unsigned long WINDOW_SIZE = 5000; // 5000 milliseconds (5 seconds)
float dutyCyclePercentage = 0.0;        // Example: 0.60 for 60% (Start at 0%)

void setHeaterDuty(float percent) {
  // Clamp value between 0.0 and 1.0
  if (percent < 0.0) percent = 0.0;
  if (percent > 1.0) percent = 1.0;
  
  dutyCyclePercentage = percent;
  
  Serial.print("Heater Duty Cycle changed to: ");
  Serial.print(dutyCyclePercentage * 100);
  Serial.println("%");
}

void setup() {
  Serial.begin(115200);
  pinMode(HEATER_PIN, OUTPUT);
  digitalWrite(HEATER_PIN, LOW); // Start with heater OFF

  delay(2000); // Give time to open Serial Monitor
  Serial.println("Starting Heater Slow PWM Test...");
  Serial.print("Window Size: ");
  Serial.print(WINDOW_SIZE);
  Serial.println(" ms");

  windowStartTime = millis();

  // ----- TEST SCENARIO -----
  // In a real application, this value comes from a PID controller or similar logic.
  // For the test, we hardcode it to 60%.
  setHeaterDuty(0.60); 
}

void loop() {
  unsigned long currentTime = millis();
  unsigned long timeInWindow = currentTime - windowStartTime;
  
  // Calculate how long the heater should be ON in this window
  unsigned long onTime = (unsigned long)(WINDOW_SIZE * dutyCyclePercentage);

  // Time-Proportional Logic:
  if (timeInWindow < onTime) {
    digitalWrite(HEATER_PIN, HIGH);
  } else {
    digitalWrite(HEATER_PIN, LOW);
  }

  // If the window has expired, reset the window start time
  if (timeInWindow >= WINDOW_SIZE) {
    windowStartTime += WINDOW_SIZE;
    
    // Optional debug output every window cycle
    // Serial.print("Window Reset. Current Time: ");
    // Serial.println(currentTime);
  }

  // ----- DYNAMIC TEST INPUT -----
  // You can test different duty cycles by opening the Serial Monitor and typing a number between 0 and 100.
  if (Serial.available() > 0) {
    int inputVal = Serial.parseInt();
    // Flush newline characters if any
    while (Serial.available() > 0) { Serial.read(); }
    
    if (inputVal >= 0 && inputVal <= 100) {
      setHeaterDuty(inputVal / 100.0);
    } else {
      Serial.println("Invalid input! Please enter a number between 0 and 100.");
    }
  }
}
