from flask import Flask, render_template, Response, jsonify
from database import fetch_predictions  
from YOLO import YOLOProcessor 
app = Flask(__name__)
yolo_processor = YOLOProcessor(model_path="yolov8n.pt")  #model


@app.route('/')
def index():
    return render_template('index.html')

# Route to return video feed
@app.route('/video_feed')
def video_feed():
    return Response(yolo_processor.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to fetch predictions from the database
@app.route('/predictions')
def get_predictions():
    predictions = fetch_predictions()  # Retrieve predictions from the database
    # The predictions are already formatted as needed. Just return them.
    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
