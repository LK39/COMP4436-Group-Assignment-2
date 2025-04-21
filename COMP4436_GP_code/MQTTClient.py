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
        self.publish_channel_light = "COMP4436/home/control/light"
        self.publish_channel_humidity = "COMP4436/home/control/humidity"
        self.publish_channel_air_conditioner = "COMP4436/home/control/air_conditioner"
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
            # print(f"Received sensor batch:")
            # print(f"  Temp: {data['temperature']}°C")
            # print(f"  Humi: {data['humidity']}%")
            # print(f"  Sound: {data['sound']}")
            # print(f"  Light: {data['light']}")
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
        """Start the MQTT client using a more robust approach"""
        if self.running:
            print("* MQTT client already running")
            return True
        
        # Initialize the client
        client_id = f"smart_home_client_{int(time.time())}"  # Unique client ID
        self.client = paho.Client(client_id=client_id, protocol=paho.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Add disconnect handler
        self.client.on_disconnect = self.on_disconnect
        
        # Configure reconnect behavior
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        
        # Configure TLS - try with the default settings first
        try:
            print("* Configuring MQTT client with TLS...")
            self.client.tls_set()  # Use default TLS settings
            self.client.username_pw_set(YOUR_USERNAME, YOUR_PASSWORD)
            
            print("* Connecting to MQTT broker...")
            self.client.connect_async(YOUR_CLUSTER_URL, 8883, keepalive=60)
            
            # Start the background thread
            self.client.loop_start()
            self.running = True
            
            print("* MQTT client started and attempting connection")
            return True
            
        except Exception as e:
            print(f"* Failed to start MQTT client: {str(e)}")
            return False
    
    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback for handling disconnects"""
        if rc != 0:
            print(f"* MQTT disconnected unexpectedly with code {rc}")
            # The loop_start method will automatically try to reconnect
        else:
            print("* MQTT disconnected normally")
        
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
    
    def publish(self,publish_channel, message,qos):
        self.client.publish(publish_channel, message, qos)
        print(f"Trigger published: {message}\nchannels: {publish_channel}")
 