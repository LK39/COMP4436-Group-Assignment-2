import cv2
import numpy as np
from ultralytics import YOLO
import time

class YOLOProcessor:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.class_names = self.model.names  
        self.predictions = []
        self.active = False  # Flag to indicate if processing is active

    def start_processing(self):
        self.active = True
        cap = cv2.VideoCapture(1)  

        while self.active:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            frame, class_count = self.process_frame(frame)  
            print(class_count)

            # Display the frame
            cv2.imshow("YOLO Detection", frame)

            # Stop processing if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def process_frame(self, frame):
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

        self.predictions = current_predictions  # Store predictions
        return frame, class_count

    def stop_processing(self):
        self.active = False  # Method to externally stop processing

    def get_predictions(self):
        return self.predictions  # Return the predictions

    def get_class_count(self):
        # Return counts of each class as a dictionary
        counts = {}
        for pred in self.predictions:
            class_name, conf = pred
            counts[class_name] = counts.get(class_name, 0) + 1
        return counts

if __name__ == "__main__":
    processor = YOLOProcessor()
    print("Starting YOLO detection...")
    processor.start_processing()
