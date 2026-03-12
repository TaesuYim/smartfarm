// Window Actuator Control using L298N Motor Driver
// Actuator type: Linear Actuator (DC Motor)

// Pin Definitions
#define ENA_PIN 11  // PWM pin for speed control (Enable A)
#define IN1_PIN 13  // Direction 1
#define IN2_PIN 12  // Direction 2

void setup() {
  Serial.begin(115200);

  // Configure pins as OUTPUT
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Initial state: Motor stopped
  stopActuator();

  Serial.println("=========================================");
  Serial.println("Window Actuator (L298N) Control Test");
  Serial.println("Pins: ENA=D11, IN1=D13, IN2=D12");
  Serial.println("Commands:");
  Serial.println(" '1' : Open Window (Extend actuator)");
  Serial.println(" '0' : Close Window (Retract actuator)");
  Serial.println(" 's' : Stop Actuator");
  Serial.println("=========================================");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Ignore whitespace and newlines
    if (cmd == '\n' || cmd == '\r' || cmd == ' ') return;

    if (cmd == '1') {
      openWindow();
      Serial.println("=> Command '1': Opening window...");
    } 
    else if (cmd == '0') {
      closeWindow();
      Serial.println("=> Command '0': Closing window...");
    } 
    else if (cmd == 's' || cmd == 'S') {
      stopActuator();
      Serial.println("=> Command 's': Actuator stopped.");
    } 
    else {
      Serial.print("Unknown command: ");
      Serial.println(cmd);
    }
  }
}

// Function to open the window (extend linear actuator)
void openWindow() {
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 255); // Full speed
}

// Function to close the window (retract linear actuator)
void closeWindow() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, HIGH);
  analogWrite(ENA_PIN, 255); // Full speed
}

// Function to stop the motor
void stopActuator() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);   // Disable output
}
