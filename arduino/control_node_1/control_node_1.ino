#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <pwm.h> // UNO R4 PWM 전용 라이브러리

// ==========================================
// 설정 (환경에 맞게 수정하세요)
// ==========================================
const char* WIFI_SSID = "iptime_2G";
const char* WIFI_PASS = "45612352";
const char* MQTT_BROKER = "192.168.5.22"; // 라즈베리파이 실제 IP
const int MQTT_PORT = 1883;

// 온실 ID 설정
const char* GH_ID = "gh1";

// Node 1 고정 IP 설정 (라즈베리파이와 같은 서브넷)
IPAddress local_IP(192, 168, 5, 21);
IPAddress gateway(192, 168, 5, 1);
IPAddress subnet(255, 255, 255, 0);

// ==========================================
// MQTT 토픽
// ==========================================
String TOPIC_CMD = String("sf/") + GH_ID + "/actuators/cmd";
String TOPIC_STATE = String("sf/") + GH_ID + "/actuators/state";
String TOPIC_HEARTBEAT = String("sf/") + GH_ID + "/actuators/heartbeat";

// ==========================================
// 핀 배치 (docs/pin-map.md 기준 Node 1)
// ==========================================
const int PIN_MIST = 2;         
const int PIN_VENT_FAN = 3;     
const int PIN_HEATER_1 = 5;     
const int PIN_HEATER_2 = 6;     
const int PIN_WIN1_IN1 = 7;     
const int PIN_WIN1_IN2 = 8;     
const int PIN_CIRC_FAN_1 = 9;   
const int PIN_CIRC_FAN_2 = 10;  
const int PIN_PUMP = 11;        
const int PIN_WIN2_IN1 = 12;    
const int PIN_WIN2_IN2 = 13;    

// UNO R4 고주파 PWM 객체 생성 (20kHz)
PwmOut pwmVent(PIN_VENT_FAN);
PwmOut pwmCirc1(PIN_CIRC_FAN_1);
PwmOut pwmCirc2(PIN_CIRC_FAN_2);
PwmOut pwmPump(PIN_PUMP);

// ==========================================
// 전역 상태 변수
// ==========================================
struct ActuatorState {
  int vent_fan_pwm_pct = 0;
  int circ_fan_1_pwm_pct = 0;
  int circ_fan_2_pwm_pct = 0;
  int heater_1_pwm_pct = 0;
  int heater_2_pwm_pct = 0;
  int pump_pwm_pct = 0;
  bool mist_on = false;
  String window_1_cmd = "stop";
  String window_2_cmd = "stop";
  unsigned long last_seq = 0;
} state;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 5000;
const unsigned long HEATER_WINDOW_MS = 5000;

// ==========================================
// 하드웨어 제어 로직
// ==========================================
void setupPWM(PwmOut &p) {
  p.begin();
  p.period_us(50); // 50us = 20kHz
  p.pulse_perc(0.0);
}

// 테스트 파일의 특수 듀티 매핑 로직 (0~100% -> 실질 0~8.3% 듀티)
void setPwmPct(PwmOut &p, int percentage) {
  percentage = constrain(percentage, 0, 100);
  float maxDuty = 200.0 / 2400.0; // 테스트 파일 기준 실질 최대 듀티
  float dutyCycle = (percentage / 100.0) * maxDuty;
  p.pulse_perc(dutyCycle * 100.0);
}

void applyAllHardware() {
  digitalWrite(PIN_MIST, state.mist_on ? HIGH : LOW);

  // 고주파 PWM 적용
  setPwmPct(pwmVent, state.vent_fan_pwm_pct);
  setPwmPct(pwmCirc1, state.circ_fan_1_pwm_pct);
  setPwmPct(pwmCirc2, state.circ_fan_2_pwm_pct);
  setPwmPct(pwmPump, state.pump_pwm_pct);

  // 창문 릴레이/모터 방향 제어
  setWindow(PIN_WIN1_IN1, PIN_WIN1_IN2, state.window_1_cmd);
  setWindow(PIN_WIN2_IN1, PIN_WIN2_IN2, state.window_2_cmd);
}

void setWindow(int in1, int in2, const String& cmd) {
  if (cmd == "open") {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else if (cmd == "close") {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }
}

void handleSlowPWM() {
  unsigned long now = millis();
  unsigned long offset = now % HEATER_WINDOW_MS;
  unsigned long h1_on_time = (HEATER_WINDOW_MS * state.heater_1_pwm_pct) / 100;
  digitalWrite(PIN_HEATER_1, (offset < h1_on_time) ? HIGH : LOW);
  unsigned long h2_on_time = (HEATER_WINDOW_MS * state.heater_2_pwm_pct) / 100;
  digitalWrite(PIN_HEATER_2, (offset < h2_on_time) ? HIGH : LOW);
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
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "SF-Node1-" + String(GH_ID);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe(TOPIC_CMD.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
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
    if (doc.containsKey("vent_fan_pwm_pct")) state.vent_fan_pwm_pct = doc["vent_fan_pwm_pct"];
    if (doc.containsKey("circ_fan_1_pwm_pct")) state.circ_fan_1_pwm_pct = doc["circ_fan_1_pwm_pct"];
    if (doc.containsKey("circ_fan_2_pwm_pct")) state.circ_fan_2_pwm_pct = doc["circ_fan_2_pwm_pct"];
    if (doc.containsKey("heater_1_pwm_pct")) state.heater_1_pwm_pct = doc["heater_1_pwm_pct"];
    if (doc.containsKey("heater_2_pwm_pct")) state.heater_2_pwm_pct = doc["heater_2_pwm_pct"];
    if (doc.containsKey("pump_pwm_pct")) state.pump_pwm_pct = doc["pump_pwm_pct"];
    if (doc.containsKey("mist_on")) state.mist_on = doc["mist_on"];
    if (doc.containsKey("window_1_cmd")) state.window_1_cmd = doc["window_1_cmd"].as<String>();
    if (doc.containsKey("window_2_cmd")) state.window_2_cmd = doc["window_2_cmd"].as<String>();

    applyAllHardware();
    publishState();
  }
}

void publishState() {
  StaticJsonDocument<1024> doc;
  doc["ts"] = ""; 
  doc["source"] = "arduino_node_1";
  doc["seq"] = state.last_seq;
  doc["result"] = "ok";
  JsonObject applied = doc.createNestedObject("applied");
  applied["vent_fan_pwm_pct"] = state.vent_fan_pwm_pct;
  applied["circ_fan_1_pwm_pct"] = state.circ_fan_1_pwm_pct;
  applied["circ_fan_2_pwm_pct"] = state.circ_fan_2_pwm_pct;
  applied["heater_1_pwm_pct"] = state.heater_1_pwm_pct;
  applied["heater_2_pwm_pct"] = state.heater_2_pwm_pct;
  applied["pump_pwm_pct"] = state.pump_pwm_pct;
  applied["mist_on"] = state.mist_on;
  applied["window_1_cmd"] = state.window_1_cmd;
  applied["window_2_cmd"] = state.window_2_cmd;
  char output[1024];
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_STATE.c_str(), output);
}

void publishHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["ts"] = "";
  doc["source"] = "arduino_node_1";
  doc["uptime_ms"] = millis();
  char output[256];
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_HEARTBEAT.c_str(), output);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_MIST, OUTPUT);
  pinMode(PIN_VENT_FAN, OUTPUT);
  pinMode(PIN_HEATER_1, OUTPUT);
  pinMode(PIN_HEATER_2, OUTPUT);
  pinMode(PIN_WIN1_IN1, OUTPUT);
  pinMode(PIN_WIN1_IN2, OUTPUT);
  pinMode(PIN_CIRC_FAN_1, OUTPUT);
  pinMode(PIN_CIRC_FAN_2, OUTPUT);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_WIN2_IN1, OUTPUT);
  pinMode(PIN_WIN2_IN2, OUTPUT);

  setupPWM(pwmVent);
  setupPWM(pwmCirc1);
  setupPWM(pwmCirc2);
  setupPWM(pwmPump);

  applyAllHardware();
  WiFi.config(local_IP, gateway, subnet);
  setupWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();
  handleSlowPWM();
  unsigned long now = millis();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}
