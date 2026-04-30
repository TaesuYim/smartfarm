#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

// ==========================================
// Network settings
// ==========================================
const char* WIFI_SSID = "iptime_2G";
const char* WIFI_PASS = "45612352";
const char* MQTT_BROKER = "192.168.5.22";
const int MQTT_PORT = 1883;

const char* GH_ID = "gh1";

IPAddress local_IP(192, 168, 5, 23);
IPAddress gateway(192, 168, 5, 1);
IPAddress subnet(255, 255, 255, 0);

// ==========================================
// MQTT topics
// ==========================================
String TOPIC_CMD = String("sf/") + GH_ID + "/actuators/cmd";
String TOPIC_STATE = String("sf/") + GH_ID + "/actuators/state";
String TOPIC_HEARTBEAT = String("sf/") + GH_ID + "/actuators/heartbeat";

// ==========================================
// Pin map
// ==========================================
const int PIN_VALVES[] = {2, 3, 4, 5, 6, 7, 8};
const int PIN_LED_STRIP = 9;                          // LED (Addressable)
const int PIN_SHADING_PUL = 10;
const int PIN_SHADING_DIR = 11;

// ==========================================
// Actuators setup
// ==========================================
#define TOTAL_LEDS 100
#define USE_LEDS 20
Adafruit_NeoPixel strip(TOTAL_LEDS, PIN_LED_STRIP, NEO_RGB + NEO_KHZ800);

const unsigned long STEP_INTERVAL_US = 1000;

// ==========================================
// State
// ==========================================
struct ActuatorState {
  bool valves[7] = {false, false, false, false, false, false, false};
  int led_r = 0, led_g = 0, led_b = 0, led_bright = 50;
  String shading_cmd = "stop";
  unsigned long last_seq = 0;
};

ActuatorState state;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;
unsigned long lastStepTime = 0;

// ==========================================
// Hardware helpers
// ==========================================
void applyAllHardware() {
  // Valves
  for(int i=0; i<7; i++) {
    digitalWrite(PIN_VALVES[i], state.valves[i] ? HIGH : LOW);
  }
  
  // LED
  strip.setBrightness(map(constrain(state.led_bright, 0, 100), 0, 100, 0, 255));
  for(int i=0; i<USE_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(state.led_r, state.led_g, state.led_b));
  }
  strip.show();
}

void handleStepper() {
  if (state.shading_cmd == "stop") return;
  
  if (micros() - lastStepTime >= STEP_INTERVAL_US) {
    lastStepTime = micros();
    digitalWrite(PIN_SHADING_DIR, (state.shading_cmd == "open") ? HIGH : LOW);
    digitalWrite(PIN_SHADING_PUL, !digitalRead(PIN_SHADING_PUL));
  }
}

// ==========================================
// Network helpers
// ==========================================
void setupWiFi() {
  Serial.println("WiFi config start");
  WiFi.config(local_IP, gateway, subnet);

  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void publishHeartbeat() {
  StaticJsonDocument<192> doc;
  doc["ts"] = "";
  doc["source"] = "arduino_node_2";
  doc["uptime_ms"] = millis();

  char output[192];
  size_t len = serializeJson(doc, output, sizeof(output));
  bool ok = mqttClient.publish(TOPIC_HEARTBEAT.c_str(), output, len);
  if (!ok) Serial.println("heartbeat publish failed");
}

void publishState() {
  StaticJsonDocument<768> doc;
  doc["ts"] = "";
  doc["source"] = "arduino_node_2";
  doc["seq"] = state.last_seq;
  doc["result"] = "ok";
  
  JsonObject applied = doc.createNestedObject("applied");
  applied["valve_pot_1_on"] = state.valves[0];
  applied["valve_pot_2_on"] = state.valves[1];
  applied["valve_pot_3_on"] = state.valves[2];
  applied["valve_pot_4_on"] = state.valves[3];
  applied["valve_pot_5_on"] = state.valves[4];
  applied["valve_pot_6_on"] = state.valves[5];
  applied["valve_fog_on"]   = state.valves[6];
  applied["led_r"] = state.led_r;
  applied["led_g"] = state.led_g;
  applied["led_b"] = state.led_b;
  applied["led_brightness_pct"] = state.led_bright;
  applied["shading_screen_cmd"] = state.shading_cmd;

  char output[768];
  size_t len = serializeJson(doc, output, sizeof(output));
  bool ok = mqttClient.publish(TOPIC_STATE.c_str(), output, len);
  if (!ok) Serial.println("state publish failed");
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("MQTT message: ");
  Serial.println(topic);

  if (String(topic) != TOPIC_CMD) return;

  StaticJsonDocument<768> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc.containsKey("seq")) state.last_seq = doc["seq"];
  
  // Valves
  if (doc.containsKey("valve_pot_1_on")) state.valves[0] = doc["valve_pot_1_on"];
  if (doc.containsKey("valve_pot_2_on")) state.valves[1] = doc["valve_pot_2_on"];
  if (doc.containsKey("valve_pot_3_on")) state.valves[2] = doc["valve_pot_3_on"];
  if (doc.containsKey("valve_pot_4_on")) state.valves[3] = doc["valve_pot_4_on"];
  if (doc.containsKey("valve_pot_5_on")) state.valves[4] = doc["valve_pot_5_on"];
  if (doc.containsKey("valve_pot_6_on")) state.valves[5] = doc["valve_pot_6_on"];
  if (doc.containsKey("valve_fog_on"))   state.valves[6] = doc["valve_fog_on"];

  // LED
  if (doc.containsKey("led_r")) state.led_r = constrain((int)doc["led_r"], 0, 255);
  if (doc.containsKey("led_g")) state.led_g = constrain((int)doc["led_g"], 0, 255);
  if (doc.containsKey("led_b")) state.led_b = constrain((int)doc["led_b"], 0, 255);
  if (doc.containsKey("led_brightness_pct")) state.led_bright = constrain((int)doc["led_brightness_pct"], 0, 100);

  // Shading screen
  if (doc.containsKey("shading_screen_cmd")) {
    String cmd = doc["shading_screen_cmd"].as<String>();
    state.shading_cmd = (cmd == "open" || cmd == "close" || cmd == "stop") ? cmd : "stop";
  }

  applyAllHardware();
  publishState();
  Serial.println("command applied");
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting MQTT...");
    String clientId = "SF-Node2-" + String(GH_ID);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      if (mqttClient.subscribe(TOPIC_CMD.c_str())) {
        Serial.print("Subscribed: ");
        Serial.println(TOPIC_CMD);
      } else {
        Serial.println("Subscribe failed");
      }
    } else {
      Serial.print("failed, state=");
      Serial.println(mqttClient.state());
      delay(5000);
    }
  }
}

// ==========================================
// Arduino lifecycle
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(3000);
  Serial.println("control_node_2 boot");

  for(int i=0; i<7; i++) {
    pinMode(PIN_VALVES[i], OUTPUT);
    digitalWrite(PIN_VALVES[i], LOW);
  }
  Serial.println("valves ready");

  pinMode(PIN_SHADING_PUL, OUTPUT);
  pinMode(PIN_SHADING_DIR, OUTPUT);
  digitalWrite(PIN_SHADING_PUL, LOW);
  digitalWrite(PIN_SHADING_DIR, LOW);
  Serial.println("stepper pins ready");

  strip.begin();
  strip.clear();
  strip.show();
  Serial.println("neopixel ready");

  applyAllHardware();
  Serial.println("hardware safe state applied");

  setupWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(768);
  Serial.println("MQTT client ready");
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }

  mqttClient.loop();
  handleStepper();

  unsigned long now = millis();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}
