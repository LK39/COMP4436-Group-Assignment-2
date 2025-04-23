import paho.mqtt.client as paho
import json
import threading
import time
from YOLO import YOLOProcessor
from IsolationForest import RealTimeIsolationForest

API_URL = "https://api.thingspeak.com/channels/2920657/feeds.json?api_key=GTDM3TTFE1THM92Z&results=100000"
YOUR_USERNAME = "hyuvuhjb"
YOUR_PASSWORD = "Qweasd12"
YOUR_CLUSTER_URL = "dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud"

class MQTTClient:
    def __init__(self):
        self.subscribe_channel = "COMP4436/home/RPI4/sensors"
        self.publish_channel_light = "COMP4436/home/control/light"
        self.publish_channel_humidity = "COMP4436/home/control/humidity"
        self.publish_channel_air_conditioner = "COMP4436/home/control/air_conditioner"
        self.publish_channel_anomalies = "COMP4436/home/control/anomalies"
        self.publish_channel_computer_vision = "COMP4436/home/control/computer_vision"
        self.results = "light on"
        self.running = False
        self.client = None
        self.thread = None
        self.yolo_processor = YOLOProcessor()  # Instantiate Model Here
        self.isolation_forest = RealTimeIsolationForest(API_URL,YOUR_CLUSTER_URL,1883,"COMP4436/home/control/anomalies")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"* MQTT Client connected with code: {rc}")
        client.subscribe(self.subscribe_channel, qos=1)
        client.subscribe(self.publish_channel_anomalies, qos=1)  # Check for Anomalies

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            topic = msg.topic
            
            if topic == self.subscribe_channel:
                # Process sensor data
                print(f"Sensor data received: {data}")
            
            elif topic == self.publish_channel_anomalies:
                # Check if anomalies were found
                if data.get("status") == "Anomalies Found":
                    print("Anomalies detected! Activating YOLO model...")
                    self.trigger_anomaly_procedures()

            elif topic == self.publish_channel_computer_vision:
                # Process computer vision data
                print(f"Computer vision data received: {data}")

        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def trigger_anomaly_procedures(self):
        global anomaly_detected  
        anomaly_detected = True
        print("Anomaly detected! Triggering procedures...")
        self.activate_yolo_model()

    def activate_yolo_model(self):
        """Activate the YOLO model and publish predictions."""
        print("Starting YOLO model...")
        self.yolo_processor.start_processing()
        
        # SURVEILLANCE TIME
        time.sleep(15)
        
        predictions = self.yolo_processor.get_predictions()
        if predictions:
            predictions_json = json.dumps(predictions)
            self.publish(self.publish_channel_computer_vision, predictions_json, qos=1)
        else:
            print("No predictions to publish.")
        
        # Stop the YOLO model after publishing
        self.yolo_processor.stop_processing()
        print("YOLO model stopped, waiting for new anomalies...")

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
        
        # Isolation Forest Run
        self.isolation_forest.run()

        # Add disconnect handler
        self.client.on_disconnect = self.on_disconnect
        
        # Configure reconnect behavior
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        
        # Configure TLS
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
        else:
            print("* MQTT disconnected normally")
    
    def stop(self):
        """Safely stop the MQTT client"""
        if not self.running:
            print("* MQTT client not running")
            return
        
        print("* Stopping MQTT client...")
        self.running = False
        
        # Disconnect client
        if self.client:
            try:
                self.client.disconnect()
                print("* MQTT client disconnected")
            except:
                pass
            
        print("* MQTT client stopped")
    
    def publish(self, publish_channel, message, qos):
        self.client.publish(publish_channel, message, qos)
        print(f"Trigger published: {message}\nchannels: {publish_channel}")

if __name__ == "__main__":
    mqtt_client = MQTTClient()
    mqtt_client.start()
