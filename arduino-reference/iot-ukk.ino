/*
  Fauzan Hydroponic - ESP8266
*/

#include <ESP8266WiFi.h>
#include <WiFiManager.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "DHT.h"

// ==========================================
// PIN DEFINITIONS & SETTINGS
// ==========================================
#define OLED_SCL      D1
#define OLED_SDA      D2

#define BUTTON_PIN    D4

#define DHTPIN        D5

#define TRIG_PIN      D6
#define ECHO_PIN      D7

#define RELAY_PIN     D0 

#define DHTTYPE       DHT22
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64

// ==========================================
// GLOBAL OBJECTS
// ==========================================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==========================================
// MQTT & NETWORK CONFIGURATION
// ==========================================
const char* mqtt_server   = "103.210.35.166";
const int   mqtt_port     = 1883;
const char* mqtt_user     = "mqtt";
const char* mqtt_password = "mqtt";

const char* topic_status  = "fauzan/status";
const char* topic_mode    = "fauzan/mode";
const char* topic_relay   = "fauzan/relay";

// DECOUPLED TIMERS
unsigned long lastPublishTime = 0;
unsigned long lastDHTTime     = 0;
unsigned long lastDistTime    = 0;

const unsigned long publishInterval = 60000; 
const unsigned long dhtInterval     = 2000; 
const unsigned long distInterval    = 1000;  

// ==========================================
// SYSTEM STATE VARIABLES
// ==========================================
float currentTemp = 0.0;
float currentHum  = 0.0;
float currentDist = 0.0;

bool isAutoMode      = true;  
bool relayState      = false; 
int  displayPage     = 0;     
bool lastButtonState = LOW;

bool showNotification = false;
unsigned long notificationTime = 0;
const unsigned long notificationDuration = 2000; 
String notifLine1 = "";
String notifLine2 = "";

// ==========================================
// SETUP ROUTINES
// ==========================================
void setup() {
  Serial.begin(115200);
  
  pinMode(BUTTON_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Set relay high, so pump stays off during boot
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); 

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED failed");
    for(;;);
  }
  
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(5, 25);
  display.print("Connecting WiFi...");
  display.display();

  dht.begin();

  WiFi.mode(WIFI_STA); 

  WiFiManager wifiManager;
  wifiManager.autoConnect("Fauzan Smart Hydroponic"); 
  
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);

  Serial.println("System Boot Complete!");
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  handleButton();

  unsigned long currentMillis = millis();

  // Handle Notifications Timer
  if (showNotification && (currentMillis - notificationTime >= notificationDuration)) {
    showNotification = false;
    updateDisplay(); 
  }

  // FAST TIMER: Ultrasonic & Pump Logic
  if (currentMillis - lastDistTime >= distInterval) {
    lastDistTime = currentMillis;
    readDistance();
    runHydroponicLogic();
    updateDisplay(); 
  }

  // MEDIUM TIMER: DHT22 Sensor
  if (currentMillis - lastDHTTime >= dhtInterval) {
    lastDHTTime = currentMillis;
    readDHT();
    updateDisplay(); 
  }

  // SLOW TIMER: MQTT Publish
  if (currentMillis - lastPublishTime >= publishInterval) {
    lastPublishTime = currentMillis;
    publishMQTT();
  }
}

// ==========================================
// CORE FUNCTIONS
// ==========================================

void triggerNotification(String line1, String line2) {
  notifLine1 = line1;
  notifLine2 = line2;
  showNotification = true;
  notificationTime = millis();
  updateDisplay(); 
}

void readDHT() {
  currentHum = dht.readHumidity();
  currentTemp = dht.readTemperature();
}

void readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); 
  if (duration == 0) {
    currentDist = -1; 
  } else {
    currentDist = duration * 0.0343 / 2; 
  }
}

void runHydroponicLogic() {
  bool oldRelayState = relayState; 

  if (currentDist > 0 && currentDist <= 10.0) {
    relayState = false; // Force OFF at 10cm
  } 
  else if (isAutoMode) {
    if (currentDist >= 20.0) {
      relayState = true;  // Turn ON at 20cm
    }
  }

  digitalWrite(RELAY_PIN, relayState ? LOW : HIGH);

  if (oldRelayState != relayState) {
    triggerNotification(" PUMP CHANGED ", relayState ? "   TO ON" : "   TO OFF");
  }
}

void handleButton() {
  bool buttonState = digitalRead(BUTTON_PIN);
  if (buttonState == HIGH && lastButtonState == LOW) {
    displayPage = !displayPage; 
    updateDisplay();                  
    delay(250); 
  }
  lastButtonState = buttonState;
}

// ==========================================
// MQTT FUNCTIONS
// ==========================================

void reconnectMQTT() {
  static unsigned long lastReconnectAttempt = 0;
  if (millis() - lastReconnectAttempt > 5000) {
    lastReconnectAttempt = millis();
    Serial.print("Attempting MQTT...");
    
    String clientId = "Fauzan-Smart-Hydproponic-";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      mqttClient.subscribe(topic_mode);
      mqttClient.subscribe(topic_relay);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.toLowerCase(); 

  if (String(topic) == topic_mode) {
    bool previousMode = isAutoMode;
    if (message == "auto") isAutoMode = true;
    else if (message == "manual") isAutoMode = false;

    if (previousMode != isAutoMode) {
      triggerNotification(" MODE CHANGED ", isAutoMode ? "  TO AUTO" : " TO MANUAL");
    }
  } 
  else if (String(topic) == topic_relay && !isAutoMode) {
    bool previousRelayState = relayState; 

    if (message == "on") relayState = true;
    else if (message == "off") relayState = false;
    
    if (previousRelayState != relayState) {
      triggerNotification(" PUMP CHANGED ", relayState ? "   TO ON" : "   TO OFF");
    }
  }
  
  runHydroponicLogic();
  updateDisplay(); 
}

void publishMQTT() {
  if (!mqttClient.connected()) return;

StaticJsonDocument<200> doc;
  doc["temperature"] = isnan(currentTemp) ? 0 : currentTemp;
  doc["humidity"]    = isnan(currentHum) ? 0 : currentHum;
  doc["distance"]    = round(currentDist * 10.0) / 10.0; 
  doc["relay_state"] = relayState ? "on" : "off";
  doc["mode"]        = isAutoMode ? "auto" : "manual";

  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer);
  
  mqttClient.publish(topic_status, jsonBuffer);
}

// ==========================================
// DISPLAY FUNCTIONS
// ==========================================

void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  if (displayPage == 0) {
    // PAGE 1: SENSORS & RELAY ---
    display.setTextSize(1);
    
    display.setCursor(0, 0);
    display.print(isAutoMode ? "Mode: Auto" : "Mode: Man");
    display.setCursor(74, 0);
    display.print(relayState ? "Pump: On" : "Pump: Off");
    display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

    display.setTextSize(1);
    display.setCursor(0, 15);
    display.print("Temperature: "); display.print(currentTemp, 1); display.print("C");
    
    display.setCursor(0, 30);
    display.print("Humidity:  "); display.print(currentHum, 1); display.print("%");
    
    display.setCursor(0, 45);
    display.print("Distance: "); 
    if(currentDist == -1) display.print("ERR");
    else { display.print(currentDist, 1); display.print("cm"); }

  } else {
    // PAGE 2: NETWORK STATUS ---
    display.setTextSize(1);
    display.setCursor(15, 0);
    display.print("Network Config");
    display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

    display.setCursor(0, 15);
    display.print("WIFI: ");
    display.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Offline");

    display.setCursor(0, 30);
    display.print("MQTT: ");
    display.print(mqttClient.connected() ? "Connected" : "Offline");

    display.setCursor(0, 45);
    display.print("Interval: ");
    display.print(publishInterval / 1000);
    display.print("s");
  }

  // OVERLAY: DYNAMIC POP-UP NOTIFICATION ---
  if (showNotification) {
    display.fillRect(14, 16, 100, 32, SSD1306_BLACK);
    display.drawRect(14, 16, 100, 32, SSD1306_WHITE);
    
    display.setTextSize(1);
    display.setCursor(20, 22);
    display.print(notifLine1);
    display.setCursor(20, 36);
    display.print(notifLine2);
  }

  display.display();
}