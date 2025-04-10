import cv2
import numpy as np
from ultralytics import YOLO
from database import insert_prediction

class YOLOProcessor:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.class_names = self.model.names  # Fetch class names for YOLO
        self.predictions = []

    def process_frame(self, frame):
        # Predictions on the current frame
        results = self.model(frame)
        result = results[0]
        bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
        classes = np.array(result.boxes.cls.cpu(), dtype="int")
        confidences = np.array(result.boxes.conf.cpu())

        current_predictions = []

        # Draw bounding boxes and class labels on the frame
        for cls, bbox, conf in zip(classes, bboxes, confidences):
            (x, y, x2, y2) = bbox
            label = f"{self.class_names[cls]}: {conf:.2f}"
            current_predictions.append((self.class_names[cls], conf))

            # Insert prediction into database
            insert_prediction(self.class_names[cls], conf)  # Save to DB

            # Box color
            color = (255, 0, 255) if cls == 0 else (0, 0, 255)  # purple for person, red for others
            
            # Add rectangle and label
            cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)

        self.predictions = current_predictions  # Store predictions for future use

        return frame

    def get_predictions(self):
        return self.predictions

    def generate_frames(self):
        cap = cv2.VideoCapture(0)  # Open webcam
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = self.process_frame(frame)  # Process the current frame

            # Encode frame to JPEG format for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        cap.release()