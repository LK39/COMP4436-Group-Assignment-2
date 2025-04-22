import cv2
import numpy as np
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import json

class YOLOProcessor:
    def __init__(self, model_path="yolov8n.pt", mqtt_broker="dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud", mqtt_port=1883):
        self.model = YOLO(model_path)
        self.class_names = self.model.names  
        self.predictions = []

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

        # Subscribe to the desired topic
        self.mqtt_client.subscribe("COMP4436/home/RPI4/sensors") 

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")

    def process_frame(self, frame):
        # Predictions on the current frame
        results = self.model(frame)
        result = results[0]
        bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
        classes = np.array(result.boxes.cls.cpu(), dtype="int")
        confidences = np.array(result.boxes.conf.cpu())

        current_predictions = []
        class_count = {}

        # Draw bounding boxes and class labels on frame
        for cls, bbox, conf in zip(classes, bboxes, confidences):
            (x, y, x2, y2) = bbox
            label = f"{self.class_names[cls]}: {conf:.2f}"
            current_predictions.append((self.class_names[cls], conf))

            # Count occurrences of each class
            class_name = self.class_names[cls]
            class_count[class_name] = class_count.get(class_name, 0) + 1
            
            # Box color
            color = (255, 0, 255) if cls == 0 else (0, 0, 255)  # purple for person, red for others
            
            # Add rectangle and label
            cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)

        self.predictions = current_predictions # Store
        
        # Publish predictions to the new MQTT topic
        self.publish_predictions(current_predictions)

        return frame, class_count

    def publish_predictions(self, predictions):
        # Convert predictions to JSON-serializable format
        predictions_serializable = [(str(cls), float(conf)) for cls, conf in predictions]
        predictions_json = json.dumps(predictions_serializable)
        
        # Publish to the new topic
        self.mqtt_client.publish("COMP4436/home/control/computer_vision", predictions_json)
        print("Published predictions to COMP4436/home/control/computer_vision:", predictions_json)

    def get_predictions(self):
        return self.predictions

    def generate_frames(self):
        cap = cv2.VideoCapture(1)  
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame, class_count = self.process_frame(frame)  
            
            print(class_count)

            # Encode frame to JPEG format for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        cap.release()

if __name__ == "__main__":
    processor = YOLOProcessor()
    for frame in processor.generate_frames():
        pass