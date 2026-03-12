#define MIST_PIN 8 // Arduino D8 pin (MOSFET Gate connection)

void setup() {
  Serial.begin(115200);   // Start serial communication at 115200 baud rate
  
  pinMode(MIST_PIN, OUTPUT);
  digitalWrite(MIST_PIN, LOW); // Set initial state to MIST OFF
  
  Serial.println("=====================================");
  Serial.println("Ultrasonic Mist Control Test (Pin D8/MOSFET)");
  Serial.println("Enter commands in the Serial Monitor:");
  Serial.println(" '1' : Turn Mist ON");
  Serial.println(" '0' : Turn Mist OFF");
  Serial.println("=====================================");
}

void loop() {
  // Check for input from Serial Monitor
  if (Serial.available() > 0) {
    char cmd = Serial.read(); // Read the first incoming character
    
    // Ignore newline (\n), carriage return (\r), and spaces
    if (cmd == '\n' || cmd == '\r' || cmd == ' ') return;
    
    // Process based on command
    if (cmd == '1') {
      digitalWrite(MIST_PIN, HIGH); // Set MOSFET Gate to HIGH (5V or 3.3V) to turn Mist ON
      Serial.println("=> Command received: '1' -> Ultrasonic Mist is ON");
    } 
    else if (cmd == '0') {
      digitalWrite(MIST_PIN, LOW);  // Set MOSFET Gate to LOW to turn Mist OFF
      Serial.println("=> Command received: '0' -> Ultrasonic Mist is OFF");
    } 
    else {
      // Handle undefined commands
      Serial.print("Unknown command: ");
      Serial.println(cmd);
    }
  }
}
