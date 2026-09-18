#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h> // Đảm bảo bạn đã cài LiquidCrystal I2C by Frank de Brabander

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

// Khởi tạo đối tượng LCD: địa chỉ 0x27, 16 cột, 2 hàng
LiquidCrystal_I2C lcd(0x27, 16, 2);

bool door_open = false;
unsigned long auto_lock_at = 0;
String last_request_id;

// Hàm hỗ trợ cập nhật trạng thái LCD
void update_lcd_state(const char* status) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Door Status:");
  lcd.setCursor(0, 1);
  if (strcmp(status, "open") == 0) {
      lcd.print("   >> OPEN <<   ");
  } else if (strcmp(status, "closed") == 0) {
      lcd.print("  >> CLOSED <<  ");
  } else {
      lcd.print(status);
  }
}

// Hàm hỗ trợ in thông báo lên LCD
void print_lcd_msg(const char* line1, const char* line2 = nullptr) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  if (line2 != nullptr) {
      lcd.setCursor(0, 1);
      lcd.print(line2);
  }
}

void publish_state(const char* status) {
  JsonDocument document;
  document["status"] = status;
  document["online"] = true;
  char payload[192];
  serializeJson(document, payload, sizeof(payload));
  mqtt_client.publish(state_topic, payload, true);
  
  // Cập nhật LCD mỗi khi đổi trạng thái cửa
  update_lcd_state(status);
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
  print_lcd_msg("Connecting WiFi", ssid);
  WiFi.begin(ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf("\nWiFi connected: %s\n", WiFi.localIP().toString().c_str());
  print_lcd_msg("WiFi Connected", WiFi.localIP().toString().c_str());
  delay(1500);
}

void reconnect_mqtt() {
  print_lcd_msg("MQTT Server", "Connecting...");
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
      print_lcd_msg("MQTT Failed", "Retrying in 5s");
      delay(5000);
      print_lcd_msg("MQTT Server", "Connecting...");
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Khởi tạo LCD
  Wire.begin(21, 22); // Chân SDA=21, SCL=22 của ESP32
  lcd.init();
  lcd.backlight();
  print_lcd_msg("Smart Door Lock", "Initializing...");
  delay(1000);

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