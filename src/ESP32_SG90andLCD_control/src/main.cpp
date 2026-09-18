#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

const char* ssid = "Penrose";
const char* wifi_password = "until2365";
// Raspberry Pi LAN address running Mosquitto. Update if the Pi's DHCP address changes.
const char* mqtt_server = "10.195.134.44";
const int mqtt_port = 1883;
const char* mqtt_user = "esp32";
const char* mqtt_password = "sg90esp32";

const char* command_topic = "smartlock/front-door/command";
const char* state_topic = "smartlock/front-door/state";

const int servo_pin = 18;
const int locked_angle = 0;
const int open_angle = 180;

WiFiClient wifi_client;
PubSubClient mqtt_client(wifi_client);
Servo door_servo;
bool door_open = false;
unsigned long auto_lock_at = 0;
String last_request_id;

void publish_state(const char* status) {
  JsonDocument document;
  document["status"] = status;
  document["online"] = true;
  char payload[192];
  serializeJson(document, payload, sizeof(payload));
  mqtt_client.publish(state_topic, payload, true);
}

void handle_command(const byte* payload, unsigned int length) {
  JsonDocument document;
  DeserializationError error = deserializeJson(document, payload, length);
  if (error) {
    Serial.printf("Invalid MQTT JSON: %s\n", error.c_str());
    return;
  }

  const char* action = document["action"] | "";
  const char* request_id = document["request_id"] | "";
  if ((strcmp(action, "open") != 0 && strcmp(action, "lock") != 0) ||
      request_id[0] == '\0') {
    Serial.println("Invalid MQTT command");
    return;
  }
  if (last_request_id == request_id) {
    Serial.println("Duplicate request_id ignored");
    return;
  }
  last_request_id = request_id;

  if (strcmp(action, "open") == 0) {
    int open_seconds = document["open_seconds"] | 5;
    open_seconds = constrain(open_seconds, 1, 60);
    door_servo.write(open_angle);
    door_open = true;
    auto_lock_at = millis() + static_cast<unsigned long>(open_seconds) * 1000UL;
    publish_state("open");
    return;
  }

  door_servo.write(locked_angle);
  door_open = false;
  auto_lock_at = 0;
  publish_state("closed");
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, command_topic) == 0) {
    handle_command(payload, length);
  }
}

void connect_wifi() {
  WiFi.begin(ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf("\nWiFi connected: %s\n", WiFi.localIP().toString().c_str());
}

void reconnect_mqtt() {
  while (!mqtt_client.connected()) {
    String client_id = "esp32-front-door-" + String(static_cast<uint32_t>(ESP.getEfuseMac()), HEX);
    const char* last_will = "{\"status\":\"unknown\",\"online\":false}";
    if (mqtt_client.connect(client_id.c_str(), mqtt_user, mqtt_password,
                            state_topic, 1, true, last_will)) {
      Serial.println("MQTT connected");
      mqtt_client.subscribe(command_topic, 1);
      publish_state(door_open ? "open" : "closed");
    } else {
      Serial.printf("MQTT connection failed, rc=%d\n", mqtt_client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  door_servo.setPeriodHertz(50);
  door_servo.attach(servo_pin, 500, 2400);
  door_servo.write(locked_angle);
  connect_wifi();
  mqtt_client.setServer(mqtt_server, mqtt_port);
  mqtt_client.setCallback(mqtt_callback);
}

void loop() {
  if (!mqtt_client.connected()) {
    reconnect_mqtt();
  }
  mqtt_client.loop();

  if (door_open && auto_lock_at != 0 &&
      static_cast<long>(millis() - auto_lock_at) >= 0) {
    door_servo.write(locked_angle);
    door_open = false;
    auto_lock_at = 0;
    publish_state("closed");
  }
}