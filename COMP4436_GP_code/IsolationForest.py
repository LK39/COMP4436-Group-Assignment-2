import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
import paho.mqtt.client as mqtt
import time
from YOLO import YOLOProcessor
import threading

class RealTimeIsolationForest:
    def __init__(self, api_url, mqtt_broker, mqtt_port, mqtt_topic):
        self.api_url = api_url
        self.model = IsolationForest()
        self.data = pd.DataFrame()
        self.fetch_all_data()
        self.previous_anomaly_count = 0 
        self.anomalies_recorded = []
        self.yolo_processor = YOLOProcessor()  # Create YOLO instance
        self.yolo_active = False  # Track if YOLO is running

        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to MQTT broker asynchronously
        try:
            self.mqtt_client.connect_async(mqtt_broker, mqtt_port, 60)
            self.mqtt_client.loop_start()
            print("Connecting to MQTT broker asynchronously...")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")

        self.mqtt_topic = mqtt_topic

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")

    def fetch_all_data(self):
        try:
            response = requests.get(self.api_url)
            json_data = response.json()
            feeds = json_data.get("feeds", [])
            
            if feeds:
                self.data = pd.DataFrame(feeds)
                self.preprocess_data(self.data)
                self.train_model()
            else:
                print("No new data received from API")
        except Exception as e:
            print(f"Error fetching data: {e}")


    def preprocess_data(self, df):
        print("Preprocessing data...")
        df['field1'] = pd.to_numeric(df['field1'], errors='coerce')  # Temperature
        df['field2'] = pd.to_numeric(df['field2'], errors='coerce')  # Humidity
        df['field3'] = pd.to_numeric(df['field3'], errors='coerce')  # Sound
        df['field4'] = pd.to_numeric(df['field4'], errors='coerce')  # Light
        
        # Drop NaN values
        self.data = df[['field1', 'field2', 'field3', 'field4']].dropna()

    def train_model(self):
        if not self.data.empty:
            print("Training Isolation Forest model...")
            self.model.fit(self.data)
            print("Model trained successfully.")
        else:
            print("No data available for training.")
    
    def detect_anomalies(self):
        if not self.data.empty:
            predictions = self.model.predict(self.data)
            anomalies = self.data[predictions == -1]
            current_anomaly_count = len(anomalies)

            # Check for new anomalies and manage YOLO accordingly
            if current_anomaly_count > self.previous_anomaly_count:
                print("More anomalies found!")
                if not self.yolo_active:
                    self.start_yolo()
            else:
                print("No new anomalies detected.")
                if self.yolo_active:
                    self.stop_yolo()

            self.publish_anomaly_status(current_anomaly_count)
            self.previous_anomaly_count = current_anomaly_count

            if not anomalies.empty:
                self.anomalies_recorded.append(anomalies)
            time.sleep(1)  # Check predictions every second

    def monitor_yolo_predictions(self):
        """Continuously monitor and print YOLO predictions"""
        while self.yolo_active:
            predictions = self.yolo_processor.get_class_count()
            if predictions:
                print("\nYOLO Detections:")
                for class_name, count in predictions.items():
                    print(f"{class_name}: {count}")
                
                # Publish YOLO predictions to MQTT
                prediction_message = ", ".join([f"{class_name}: {count}" 
                                             for class_name, count in predictions.items()])
                self.mqtt_client.publish(f"{self.mqtt_topic}/yolo", prediction_message)
            
            time.sleep(1)  # Check predictions every second

    def start_yolo(self):
        """Start YOLO processing and prediction monitoring in separate threads"""
        self.yolo_active = True
        
        # Start YOLO processing thread
        self.yolo_thread = threading.Thread(target=self.yolo_processor.start_processing)
        self.yolo_thread.daemon = True
        self.yolo_thread.start()
        
        # Start prediction monitoring thread
        self.prediction_check_thread = threading.Thread(target=self.monitor_yolo_predictions)
        self.prediction_check_thread.daemon = True
        self.prediction_check_thread.start()
        
        print("YOLO processing and monitoring started")

    def stop_yolo(self):
        """Stop YOLO processing and prediction monitoring"""
        if self.yolo_active:
            self.yolo_active = False
            self.yolo_processor.stop_processing()
            if self.prediction_check_thread:
                self.prediction_check_thread.join(timeout=1)
            print("YOLO processing and monitoring stopped")

    def publish_anomaly_status(self, count):
        message = "Anomaly Found" if count > 0 else "Anomaly Not Found"
        self.mqtt_client.publish(self.mqtt_topic, message)
        print(f"Anomaly status: {message} (Count: {count})")

    def run(self):
        try:
            print("Starting anomaly detection...")
            while True:
                self.fetch_all_data()
                self.detect_anomalies()
                time.sleep(20)
        except KeyboardInterrupt:
            print("Stopping anomaly detection.")
            if self.yolo_active:
                self.stop_yolo()
