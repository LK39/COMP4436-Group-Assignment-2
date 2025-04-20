import paho.mqtt.client as paho
from paho import mqtt
import json
import threading
import time

YOUR_USERNAME = "hyuvuhjb"
YOUR_PASSWORD = "Qweasd12"
YOUR_CLUSTER_URL = "dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud"

class MQTTClient:
    def __init__(self):
        self.subscribe_channel = "COMP4436/home/RPI4/sensors"
        self.publish_channel = "COMP4436/home/lightcontrol"
        self.results = "light on"
        self.running = False
        self.client = None
        self.thread = None
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"* MQTT Client connected with code: {rc}")
        client.subscribe(self.subscribe_channel, qos=1)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print(f"Received sensor batch:")
            print(f"  Temp: {data['temperature']}°C")
            print(f"  Humi: {data['humidity']}%")
            print(f"  Sound: {data['sound']}")
            print(f"  Light: {data['light']}")
            # You can add callback to process data here if needed
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def _mqtt_loop(self):
        """Background thread function for MQTT client loop"""
        try:
            while self.running:
                self.client.loop(0.1)  # Process messages for 100ms then return
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
        except Exception as e:
            print(f"MQTT thread exception: {str(e)}")
        finally:
            print("* MQTT thread exiting")
    
    def start(self):
        """Start the MQTT client in a separate thread"""
        if self.running:
            print("* MQTT client already running")
            return
        
        # Initialize client
        self.client = paho.Client(client_id="smart_home_client", protocol=paho.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(YOUR_USERNAME, YOUR_PASSWORD)
        
        try:
            # Connect to broker
            print("* Connecting to MQTT broker...")
            self.client.connect(YOUR_CLUSTER_URL, 8883)
            
            # Set running flag
            self.running = True
            
            # Start thread
            self.thread = threading.Thread(target=self._mqtt_loop, daemon=True)
            self.thread.start()
            print("* MQTT client thread started")
            
            return True
        except Exception as e:
            print(f"* Failed to start MQTT client: {str(e)}")
            self.running = False
            return False
    
    def stop(self):
        """Safely stop the MQTT client"""
        if not self.running:
            print("* MQTT client not running")
            return
        
        print("* Stopping MQTT client...")
        self.running = False
        
        # Wait for thread to exit (with timeout)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            
        # Disconnect client
        if self.client:
            try:
                self.client.disconnect()
                print("* MQTT client disconnected")
            except:
                pass
            
        print("* MQTT client stopped")
    
    def publish(self, publish_channel, message):
        self.client.publish(publish_channel, message, qos=1)
        print(f"Trigger published: {message}\nchannels: {self.publish_channel}")
 