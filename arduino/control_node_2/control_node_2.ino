#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

// ==========================================
// 설정 (환경에 맞게 수정하세요)
// ==========================================
const char* WIFI_SSID = "iptime_2G";
const char* WIFI_PASS = "45612352";
const char* MQTT_BROKER = "192.168.5.22"; // 라즈베리파이 실제 IP
const int MQTT_PORT = 1883;

// 온실 ID 설정
const char* GH_ID = "gh1";

// Node 2 고정 IP 설정 (Node 1: .21, Pi: .22 -> Node 2: .23)
IPAddress local_IP(192, 168, 5, 23);
IPAddress gateway(192, 168, 5, 1);
IPAddress subnet(255, 255, 255, 0);

// ==========================================
// MQTT 토픽
// ==========================================
String TOPIC_CMD = String("sf/") + GH_ID + "/actuators/cmd";
String TOPIC_STATE = String("sf/") + GH_ID + "/actuators/state";
String TOPIC_HEARTBEAT = String("sf/") + GH_ID + "/actuators/heartbeat";

// ==========================================
// 핀 배치 (docs/pin-map.md 기준 Node 2)
// ==========================================
const int PIN_VALVES[] = {2, 3, 4, 5, 6, 7, 8}; // 밸브 1~6 및 포깅 밸브
const int PIN_LED = 9;                          // LED (Addressable)
const int PIN_SHADING_PUL = 10;                 // 차광스크린 PUL
const int PIN_SHADING_DIR = 11;                 // 차광스크린 DIR

// LED 설정 (test_led_addressable.ino 참조)
#define TOTAL_LEDS 100
#define USE_LEDS 20
Adafruit_NeoPixel strip(TOTAL_LEDS, PIN_LED, NEO_RGB + NEO_KHZ800);

// ==========================================
// 전역 상태 변수
// ==========================================
struct ActuatorState {
  bool valves[7] = {false, false, false, false, false, false, false};
  int led_r = 0, led_g = 0, led_b = 0, led_bright = 50;
  String shading_cmd = "stop";
  unsigned long last_seq = 0;
} state;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeat = 0;
unsigned long lastStepTime = 0;
const unsigned long STEP_INTERVAL_US = 1000; // 스텝 펄스 간격 (1ms)

// 함수 선언
void applyAllHardware();
void setupWiFi();
void reconnectMQTT();
void publishState();
void publishHeartbeat();

void setup() {
  Serial.begin(115200);
  
  // 밸브 핀 초기화
  for(int i=0; i<7; i++) {
    pinMode(PIN_VALVES[i], OUTPUT);
    digitalWrite(PIN_VALVES[i], LOW);
  }
  
  // 스텝모터 핀 초기화
  pinMode(PIN_SHADING_PUL, OUTPUT);
  pinMode(PIN_SHADING_DIR, OUTPUT);
  digitalWrite(PIN_SHADING_PUL, LOW);
  digitalWrite(PIN_SHADING_DIR, LOW);
  
  // LED 초기화
  strip.begin();
  strip.clear();
  strip.show();

  WiFi.config(local_IP, gateway, subnet);
  setupWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();
  
  // 차광스크린 스텝모터 구동 (Non-blocking)
  if (state.shading_cmd != "stop") {
    if (micros() - lastStepTime >= STEP_INTERVAL_US) {
      lastStepTime = micros();
      digitalWrite(PIN_SHADING_DIR, (state.shading_cmd == "open") ? HIGH : LOW);
      digitalWrite(PIN_SHADING_PUL, !digitalRead(PIN_SHADING_PUL));
    }
  }

  unsigned long now = millis();
  if (now - lastHeartbeat >= 5000) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}

// ==========================================
// 하드웨어 제어 로직
// ==========================================
void applyAllHardware() {
  // 밸브 적용
  for(int i=0; i<7; i++) {
    digitalWrite(PIN_VALVES[i], state.valves[i] ? HIGH : LOW);
  }
  
  // LED 적용
  strip.setBrightness(map(state.led_bright, 0, 100, 0, 255));
  for(int i=0; i<USE_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(state.led_r, state.led_g, state.led_b));
  }
  strip.show();
  
  // 스텝모터는 loop() 내 handle 로직에서 처리됨
}

// ==========================================
// 통신 로직 (WiFi & MQTT)
// ==========================================
void setupWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "SF-Node2-" + String(GH_ID);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe(TOPIC_CMD.c_str());
    } else {
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  if (String(topic) == TOPIC_CMD) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    if (error) return;

    if (doc.containsKey("seq")) state.last_seq = doc["seq"];
    
    // 밸브 명령 (배열 또는 개별 필드 처리 가능하게 구성)
    if (doc.containsKey("valve_pot_1_on")) state.valves[0] = doc["valve_pot_1_on"];
    if (doc.containsKey("valve_pot_2_on")) state.valves[1] = doc["valve_pot_2_on"];
    if (doc.containsKey("valve_pot_3_on")) state.valves[2] = doc["valve_pot_3_on"];
    if (doc.containsKey("valve_pot_4_on")) state.valves[3] = doc["valve_pot_4_on"];
    if (doc.containsKey("valve_pot_5_on")) state.valves[4] = doc["valve_pot_5_on"];
    if (doc.containsKey("valve_pot_6_on")) state.valves[5] = doc["valve_pot_6_on"];
    if (doc.containsKey("valve_fog_on"))   state.valves[6] = doc["valve_fog_on"];

    // LED 명령
    if (doc.containsKey("led_r")) state.led_r = doc["led_r"];
    if (doc.containsKey("led_g")) state.led_g = doc["led_g"];
    if (doc.containsKey("led_b")) state.led_b = doc["led_b"];
    if (doc.containsKey("led_brightness_pct")) state.led_bright = doc["led_brightness_pct"];

    // 차광스크린 명령
    if (doc.containsKey("shading_screen_cmd")) state.shading_cmd = doc["shading_screen_cmd"].as<String>();

    applyAllHardware();
    publishState();
  }
}

void publishState() {
  StaticJsonDocument<1024> doc;
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
  char output[1024];
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_STATE.c_str(), output);
}

void publishHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["source"] = "arduino_node_2";
  doc["uptime_ms"] = millis();
  char output[256];
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_HEARTBEAT.c_str(), output);
}
