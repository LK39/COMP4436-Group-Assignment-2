#include <WiFi.h>
#include <HTTPClient.h>
#include <UrlEncode.h>  // Install this library from Arduino Library Manager

// Replace with your network credentials
const char* ssid = "EIA-W311MESH";
const char* password = "42004200";

// Your phone number with country code, e.g., +1234567890
const String phoneNumber = "phone_number";

// Your API key received from CallMeBot
const String apiKey = "api";

// Function to send WhatsApp message
void sendMessage(String message) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // URL encode the message
    String encodedMessage = urlEncode(message);

    // Construct the API URL
    String url = "https://api.callmebot.com/whatsapp.php?phone=" + phoneNumber + "&text=" + encodedMessage + "&apikey=" + apiKey;

    http.begin(url);
    int httpResponseCode = http.GET();

    if (httpResponseCode == 200) {
      Serial.println("Message sent successfully");
    } else {
      Serial.print("Error sending message. HTTP code: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Enter your WhatsApp message: ");

  // Connect to WiFi
  WiFi.disconnect();
  delay(100);  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected to WiFi with ssid=");
  Serial.println(ssid);

  // Send a test message
  sendMessage("Hello from ESP32 Fire-Beetle via CallMeBot!");
}

void loop() {
  // Your code here, e.g., send messages on events or sensor triggers
  if (Serial.available()) {
    // Read the incoming string until newline character
    String input_message = Serial.readStringUntil('\n');
    input_message.trim();   // Remove any leading/trailing whitespace/newlines

    if (input_message.length() > 0 ) {
      Serial.print("Sending message: ");
      Serial.println(input_message);
      sendMessage(input_message);
    }
  }	
}
