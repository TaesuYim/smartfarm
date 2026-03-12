#define VALVE_PIN 2 // Arduino D2 pin (MOSFET Gate connection)

void setup() {
  Serial.begin(115200);   // Start serial communication at 115200 baud rate
  
  pinMode(VALVE_PIN, OUTPUT);
  digitalWrite(VALVE_PIN, LOW); // Set initial state to VALVE OFF (Closed)
  
  Serial.println("=====================================");
  Serial.println("Solenoid Valve Control Test (Pin D2/MOSFET)");
  Serial.println("Enter commands in the Serial Monitor:");
  Serial.println(" '1' : Turn Valve ON / OPEN");
  Serial.println(" '0' : Turn Valve OFF / CLOSED");
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
      digitalWrite(VALVE_PIN, HIGH); // Set MOSFET Gate to HIGH (5V or 3.3V) to turn Valve ON
      Serial.println("=> Command received: '1' -> Valve is ON (Open)");
    } 
    else if (cmd == '0') {
      digitalWrite(VALVE_PIN, LOW);  // Set MOSFET Gate to LOW to turn Valve OFF
      Serial.println("=> Command received: '0' -> Valve is OFF (Closed)");
    } 
    else {
      // Handle undefined commands
      Serial.print("Unknown command: ");
      Serial.println(cmd);
    }
  }
}
