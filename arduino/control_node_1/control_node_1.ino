#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <pwm.h>

// ==========================================
// Network settings
// ⚠️ 실제 배포 시 WiFi 비밀번호를 직접 코드에 넣지 마세요.
//    레포를 public으로 전환할 경우 반드시 변경하세요.
//    참고: .env.example
// ==========================================
const char* WIFI_SSID = "iptime_2G";
const char* WIFI_PASS = "45612352";
const char* MQTT_BROKER = "192.168.5.22";
const int MQTT_PORT = 1883;

const char* GH_ID = "gh1";

IPAddress local_IP(192, 168, 5, 91);
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

// ==========================================
// PWM
// ==========================================
PwmOut pwmVent(PIN_VENT_FAN);
PwmOut pwmCirc1(PIN_CIRC_FAN_1);
PwmOut pwmCirc2(PIN_CIRC_FAN_2);
PwmOut pwmPump(PIN_PUMP);

// ==========================================
// State
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
};

ActuatorState state;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;
const unsigned long HEATER_WINDOW_MS = 5000;

// ==========================================
// Hardware helpers
// ==========================================
void setupPwmChannel(PwmOut& pwm, const char* name) {
  Serial.print(name);
  Serial.println(" PWM begin");

  pwm.begin();
  pwm.period_us(50);
  pwm.pulse_perc(0.0);

  Serial.print(name);
  Serial.println(" PWM ready");
}

void setPwmPct(PwmOut& pwm, int percentage) {
  percentage = constrain(percentage, 0, 100);

  // Keep the same duty mapping used in the previous actuator test files.
  float maxDuty = 200.0 / 2400.0;
  float dutyCycle = (percentage / 100.0) * maxDuty;
  pwm.pulse_perc(dutyCycle * 100.0);
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

void applyAllHardware() {
  digitalWrite(PIN_MIST, state.mist_on ? HIGH : LOW);

  setPwmPct(pwmVent, state.vent_fan_pwm_pct);
  setPwmPct(pwmCirc1, state.circ_fan_1_pwm_pct);
  setPwmPct(pwmCirc2, state.circ_fan_2_pwm_pct);
  setPwmPct(pwmPump, state.pump_pwm_pct);

  setWindow(PIN_WIN1_IN1, PIN_WIN1_IN2, state.window_1_cmd);
  setWindow(PIN_WIN2_IN1, PIN_WIN2_IN2, state.window_2_cmd);
}

void handleSlowPWM() {
  unsigned long now = millis();
  unsigned long offset = now % HEATER_WINDOW_MS;

  unsigned long heater1OnMs = (HEATER_WINDOW_MS * state.heater_1_pwm_pct) / 100;
  unsigned long heater2OnMs = (HEATER_WINDOW_MS * state.heater_2_pwm_pct) / 100;

  digitalWrite(PIN_HEATER_1, offset < heater1OnMs ? HIGH : LOW);
  digitalWrite(PIN_HEATER_2, offset < heater2OnMs ? HIGH : LOW);
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
  doc["source"] = "arduino_node_1";
  doc["uptime_ms"] = millis();

  char output[192];
  size_t len = serializeJson(doc, output, sizeof(output));

  bool ok = mqttClient.publish(TOPIC_HEARTBEAT.c_str(), output, len);
  if (!ok) {
    Serial.println("heartbeat publish failed");
  }
}

void publishState() {
  StaticJsonDocument<768> doc;
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

  char output[768];
  size_t len = serializeJson(doc, output, sizeof(output));

  bool ok = mqttClient.publish(TOPIC_STATE.c_str(), output, len);
  if (!ok) {
    Serial.println("state publish failed");
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("MQTT message: ");
  Serial.println(topic);

  if (String(topic) != TOPIC_CMD) {
    return;
  }

  StaticJsonDocument<768> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc.containsKey("seq")) state.last_seq = doc["seq"];
  if (doc.containsKey("vent_fan_pwm_pct")) state.vent_fan_pwm_pct = constrain((int)doc["vent_fan_pwm_pct"], 0, 100);
  if (doc.containsKey("circ_fan_1_pwm_pct")) state.circ_fan_1_pwm_pct = constrain((int)doc["circ_fan_1_pwm_pct"], 0, 100);
  if (doc.containsKey("circ_fan_2_pwm_pct")) state.circ_fan_2_pwm_pct = constrain((int)doc["circ_fan_2_pwm_pct"], 0, 100);
  if (doc.containsKey("heater_1_pwm_pct")) state.heater_1_pwm_pct = constrain((int)doc["heater_1_pwm_pct"], 0, 100);
  if (doc.containsKey("heater_2_pwm_pct")) state.heater_2_pwm_pct = constrain((int)doc["heater_2_pwm_pct"], 0, 100);
  if (doc.containsKey("pump_pwm_pct")) state.pump_pwm_pct = constrain((int)doc["pump_pwm_pct"], 0, 100);
  if (doc.containsKey("mist_on")) state.mist_on = doc["mist_on"];

  if (doc.containsKey("window_1_cmd")) {
    String cmd = doc["window_1_cmd"].as<String>();
    state.window_1_cmd = (cmd == "open" || cmd == "close" || cmd == "stop") ? cmd : "stop";
  }

  if (doc.containsKey("window_2_cmd")) {
    String cmd = doc["window_2_cmd"].as<String>();
    state.window_2_cmd = (cmd == "open" || cmd == "close" || cmd == "stop") ? cmd : "stop";
  }

  applyAllHardware();
  publishState();

  Serial.println("command applied");
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting MQTT...");

    String clientId = "SF-Node1-" + String(GH_ID);

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
  Serial.println("control_node_1 boot");

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
  Serial.println("pinMode ready");

  setupPwmChannel(pwmVent, "vent");
  setupPwmChannel(pwmCirc1, "circ1");
  setupPwmChannel(pwmCirc2, "circ2");
  setupPwmChannel(pwmPump, "pump");

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
  handleSlowPWM();

  unsigned long now = millis();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}
