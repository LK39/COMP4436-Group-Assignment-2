#include <WiFi.h>               // Wifi driver
#include <PubSubClient.h>       // MQTT server library
//#include <ArduinoJson.h>        // JSON library
#include <M5StickCPlus2.h>
#include<WiFiClientSecure.h>

#define DATA 0                  // DHT11
#define LED 26

// MQTT and WiFi set-up
//WiFiClient espClient;
WiFiClientSecure espClient;
PubSubClient client(espClient);

//const char *ssid = "samuelkar";              // Your SSID             
//const char *password = "91237389";             // Your Wifi password
const char *ssid = "EIA-W311MESH";              // Your SSID             
const char *password = "42004200";             // Your Wifi password
const char *mqtt_server = "dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud";
char *mqtt_topic = "COMP4436/home/lightcontrol";
const char *mqtt_username = "hyuvuhjb"; 
const char *mqtt_password = "Qweasd12"; 
const int port=8883;

char msg[100];
String macAddr;

byte reconnect_count = 0;
long currentTime = 0;
bool output = 0;

//StaticJsonDocument<100> Jsondata; // Create a JSON document of 100 characters max before void setup_wifi()

void connectToMQTTBroker(){ 

    while (!client.connected()) {
        M5.Lcd.fillScreen(GREEN); //clear the display
        M5.Lcd.setTextColor(BLACK);
        M5.Lcd.setCursor(0,0);
        M5.Lcd.println("MQTT Broker");
        M5.Lcd.setCursor(0,20);
        M5.Lcd.println("try to connect");
        String client_id = "hyuvuhjb-client-" + String(WiFi.macAddress());
        Serial.printf("Connecting to MQTT Broker as %s.....\n", client_id.c_str());
        if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            M5.Lcd.fillScreen(GREEN); //clear the display
            M5.Lcd.setTextColor(BLACK);
            M5.Lcd.setCursor(0,0);
            M5.Lcd.println("MQTT Broker");
            M5.Lcd.setCursor(0,20);
            M5.Lcd.println("connected!");
            Serial.println("Connected to MQTT broker");
            client.subscribe(mqtt_topic);
            // Publish message upon successful connection
            client.publish(mqtt_topic, "Hi EMQX I'm ESP8266 ^^");
        } else {
            M5.Lcd.fillScreen(RED); //clear the display
            M5.Lcd.setTextColor(BLACK);
            M5.Lcd.setCursor(0,0);
            M5.Lcd.println("Failed to connect to MQTT broker, rc=");
            M5.Lcd.setCursor(0,20);
            M5.Lcd.println(client.state());
            M5.Lcd.setCursor(0,40);
            M5.Lcd.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

//Set up the Wifi connection
void setup_wifi() {
  byte count = 0;
  WiFi.disconnect();
  delay(100);
  // We start by connectipinng to a WiFi network
  WiFi.begin(ssid, password); // start the Wifi connection with defined SSID and PW

  currentTime = millis();
  M5.Lcd.setCursor(0,0);
  M5.Lcd.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
    output = !output;
    digitalWrite(LED, output);
    count++;
    if (count == 6) {
      count = 0;
      M5.Lcd.fillScreen(BLACK); //clear the display
      M5.Lcd.setCursor(0,0);
      M5.Lcd.print("Connecting");
    }
    if (millis()-currentTime > 30000){
      ESP.restart();
    }
  }
  macAddr=WiFi.macAddress();
  //Show in the small TFT
  M5.Lcd.fillScreen(BLACK); //clear the screen
  M5.Lcd.setCursor(0,0);
  M5.Lcd.print("WiFi");
  M5.Lcd.setCursor(0,20);
  M5.Lcd.print("connected!");
  digitalWrite(LED, HIGH);
  delay(2000);
}

void callback(char* topic, byte* payload, unsigned int length) {

  char* message = (char*)malloc(length + 1);
  memcpy(message, payload, length);
  message[length] = '\0'; 
  
  M5.Lcd.fillScreen(GREEN); //clear the display
  M5.Lcd.setTextColor(BLACK);
  M5.Lcd.setCursor(0,0);
  M5.Lcd.println("Receive message: ");
  M5.Lcd.setCursor(0,20);
  M5.Lcd.println(message);
  
  free(message); 
}

void setup() {
  //Task do only once after power up
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  digitalWrite(LED, LOW);
  
  M5.begin();
  
  M5.Lcd.setRotation(3);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  
  setup_wifi();
  
  espClient.setInsecure();
  client.setServer(mqtt_server, port);
  client.setCallback(callback);
  // Specify the QoS to subscribe at. Only supports QoS 0 or 1:
  connectToMQTTBroker();

}

void loop() {
  if (client.connected()== false) connectToMQTTBroker();
  client.loop();
  delay(1000);
}
