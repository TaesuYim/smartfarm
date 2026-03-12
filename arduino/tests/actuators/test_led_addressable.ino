#include <Adafruit_NeoPixel.h>

// Connection Configuration
#define LED_PIN     5   // Arduino Uno R4 WiFi D5 pin (250 ohm resistor connected between data line and pin)
#define TOTAL_LEDS  100 // 100 LEDs connected in series
#define USE_LEDS    20  // 20 LEDs to be used among them

Adafruit_NeoPixel strip(TOTAL_LEDS, LED_PIN, NEO_RGB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);   // Start serial communication at 115200 baud rate
  
  strip.begin();           // Initialize LED strip object
  strip.clear();           // Set all 100 LEDs to OFF initially
  strip.show();            // Apply initial OFF state
  strip.setBrightness(50); // Set brightness (0~255)
  
  Serial.println("=========================================");
  Serial.println("WS2811 Manual Control Mode (Pin D5)");
  Serial.println("Enter R,G,B values separated by commas in Serial Monitor.");
  Serial.println("The color will remain on until the next command is sent!");
  Serial.println("Examples:");
  Serial.println(" '255,0,0'   : Turn on RED");
  Serial.println(" '0,255,0'   : Turn on GREEN");
  Serial.println(" '255,255,0' : Turn on YELLOW");
  Serial.println(" '0,0,0'     : Turn completely OFF");
  Serial.println("=========================================");
  Serial.println("Waiting for input...");
}

void loop() {
  // Wait for serial input
  if (Serial.available() > 0) {
    // Read the entire line until newline character (\n)
    String input = Serial.readStringUntil('\n');
    input.trim(); // Trim whitespace and carriage returns to prevent garbage values
    
    // Ignore empty input (e.g., just Enter key)
    if (input.length() > 0) {
      
      // Check for two commas and split the string
      int firstComma = input.indexOf(',');
      int secondComma = input.indexOf(',', firstComma + 1);
      
      if (firstComma > 0 && secondComma > firstComma) {
        int r = input.substring(0, firstComma).toInt();
        int g = input.substring(firstComma + 1, secondComma).toInt();
        int b = input.substring(secondComma + 1).toInt();
        
        // Limit input values to the safe 0~255 range
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        Serial.print("=> Applying received RGB: (");
        Serial.print(r);
        Serial.print(", ");
        Serial.print(g);
        Serial.print(", ");
        Serial.print(b);
        Serial.println(") - Maintaining state");

        // Set the LEDs to the received color
        setColor(r, g, b);
      } else {
        Serial.println("Invalid format. Please enter three numbers separated by commas like '255,0,0'.");
      }
    }
  }
}

// Function to update the specified number of LEDs (USE_LEDS) and apply changes
void setColor(uint8_t red, uint8_t green, uint8_t blue) {
  strip.clear(); // Clear all pixels first to prevent residual colors
  
  // Apply color to the first USE_LEDS defined
  for(int i = 0; i < USE_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(red, green, blue));
  }
  strip.show(); // Transmit color data to hardware and update
}
