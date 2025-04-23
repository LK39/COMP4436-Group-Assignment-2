from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from AI_Prediction import AI_Prediction
from MQTTClient import MQTTClient
import pandas as pd
import threading
import torch
import atexit
import os
import sys
import signal
import time  # Add time import for timestamp
from IsolationForest import RealTimeIsolationForest

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    print("\nSignal received, shutting down...")
    shutdown_mqtt()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Create Flask app
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize your AI model
input_size = 3
hidden_size = 10
num_layers = 10
output_size = 3
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_path = './10_10/lstm_model_10_10.pth'
prediction_model = AI_Prediction(input_size, hidden_size, num_layers, output_size, device, model_path)

mqtt_client = MQTTClient()

# Current state
system_on = False
anomaly_detected = False
thresholds = {
    "Temperature": 25.0,
    "Humidity": 60.0,
    "Light": 500.0
}
forecast_minutes = 30
forecast_interval = 3
channel_id = "2920657"
read_api_key = "7CPWCMSCRC5FSLZU"

# Initialize device status
device_status = {
    "air_conditioner": "OFF",
    "lights": "OFF",
    "moisture_absorber": "OFF"
}

# Register clean shutdown handler
def shutdown_mqtt():
    print("Shutting down MQTT client...")
    if mqtt_client:
        mqtt_client.stop()

atexit.register(shutdown_mqtt)

# Route definitions
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/system_health', methods=['GET'])
def system_health():
    mqtt_connected = False
    if mqtt_client and mqtt_client.client:
        try:
            mqtt_connected = mqtt_client.client.is_connected()
        except:
            mqtt_connected = False
    
    return jsonify({
        "status": "online",
        "mqtt_connected": mqtt_connected,
        "system_on": system_on,
        "timestamp": time.time()
    })

@app.route('/mqtt_status', methods=['GET'])
def mqtt_status():
    if mqtt_client and mqtt_client.running and hasattr(mqtt_client.client, 'is_connected'):
        try:
            if mqtt_client.client.is_connected():
                return jsonify({"status": "connected"})
        except:
            pass
    return jsonify({"status": "disconnected"})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "online"})

@app.route('/anomaly_status', methods=['GET'])
def get_anomaly_status():
    return jsonify({"anomaly_detected": anomaly_detected})

@app.route('/reset_anomaly', methods=['POST'])
def reset_anomaly():
    global anomaly_detected
    anomaly_detected = False
    return jsonify({"success": True, "message": "Anomaly status reset."})

@app.route('/settings', methods=['POST'])
def update_settings():
    global thresholds, forecast_minutes, forecast_interval
    data = request.json
    
    if 'thresholds' in data:
        thresholds = data['thresholds']
    
    if 'forecast_minutes' in data:
        forecast_minutes = data['forecast_minutes']
    
    if 'forecast_interval' in data:
        forecast_interval = data['forecast_interval']
    
    return jsonify({"success": True})

def turn_off_all_appliances():
    global device_status
    
    appliance_states = {
        "air_conditioner": "OFF",
        "lights": "OFF",
        "moisture_absorber": "OFF"
    }
    
    device_status = appliance_states
    print("All appliances turned off due to system shutdown")

    mqtt_client.publish(mqtt_client.publish_channel_light, "lights off", qos=1)
    mqtt_client.publish(mqtt_client.publish_channel_air_conditioner, "air_conditioner off", qos=1)
    mqtt_client.publish(mqtt_client.publish_channel_humidity, "moisture_absorber off", qos=1)
    
    return appliance_states

@app.route('/system_status', methods=['POST'])
def update_system_status():
    global system_on
    data = request.json
    
    print(f"System status update received: {data}")
    
    if 'system_on' in data:
        system_on = data.get('system_on')
        print(f"System status set to: {system_on}")
    else:
        return jsonify({"error": "Invalid data format, expected {'system_on': true|false}"}), 400
    
    if not system_on and data.get('turn_off_all_appliances', False):
        appliance_states = turn_off_all_appliances()
        
        return jsonify({
            "success": True, 
            "message": "System turned off and all appliances deactivated",
            "device_status": appliance_states
        })
    
    return jsonify({"success": True, "message": "System status updated"})

@app.route('/forecast', methods=['GET'])
def get_forecast():
    minutes = int(request.args.get('minutes', 30))
    
    if not system_on:
        return jsonify({"error": "System is off"}), 400
    
    # Get forecast from AI_Prediction
    forecasts_df = prediction_model.run(channel_id, read_api_key, True, thresholds)
    
    if forecasts_df is None:
        return jsonify({"error": "Failed to generate forecast"}), 500
    
    # Limit to requested minutes
    forecasts_df = forecasts_df.iloc[:minutes]
    
    # Convert to format for UI
    timestamps = forecasts_df.index.strftime('%Y-%m-%dT%H:%M:%S').tolist()
    temperature = forecasts_df['Temperature'].tolist()
    humidity = forecasts_df['Humidity'].tolist()
    light = forecasts_df['Light'].tolist()
    
    # Determine device status based on the predicted values
    # We'll use the final prediction point for decision making
    final_temp = temperature[-1]  # Last predicted temperature
    final_humidity = humidity[-1]
    final_light = light[-1]
    
    global device_status
    
    # Only update device statuses if system is on
    if system_on:
        # Check temperature threshold
        if final_temp > thresholds["Temperature"]:
            device_status["air_conditioner"] = "ON"
        elif final_temp - 3 < thresholds["Temperature"]:
            device_status["air_conditioner"] = "OFF"
        
        # Check light threshold
        if final_light < thresholds["Light"]:
            device_status["lights"] = "ON"
        elif final_light - 100 > thresholds["Light"]:
            device_status["lights"] = "OFF"

        # Check humidity threshold
        if final_humidity > thresholds["Humidity"]:
            device_status["moisture_absorber"] = "ON"
        elif final_humidity - 10 < thresholds["Humidity"]:
            device_status["moisture_absorber"] = "OFF"
        
        # Send MQTT commands if needed
        if device_status["lights"] == "ON":
            mqtt_client.publish(mqtt_client.publish_channel_light, "lights on", qos=1)
        else:
            mqtt_client.publish(mqtt_client.publish_channel_light, "lights off", qos=1)
        
        if device_status["air_conditioner"] == "ON":
            mqtt_client.publish(mqtt_client.publish_channel_air_conditioner, "air_conditioner on", qos=1)
        else:
            mqtt_client.publish(mqtt_client.publish_channel_air_conditioner, "air_conditioner off", qos=1)
        
        if device_status["moisture_absorber"] == "ON":
            mqtt_client.publish(mqtt_client.publish_channel_humidity, "moisture_absorber on", qos=1)
        else:
            mqtt_client.publish(mqtt_client.publish_channel_humidity, "moisture_absorber off", qos=1)
    
    # Create human-readable messages
    status_messages = []
    
    if device_status["air_conditioner"] == "ON":
        status_messages.append("Air conditioner ON")
    else:
        status_messages.append("Air conditioner OFF")
    
    if device_status["lights"] == "ON":
        status_messages.append("Lights ON")
    else:
        status_messages.append("Lights OFF")
    
    if device_status["moisture_absorber"] == "ON":
        status_messages.append("Moisture absorber ON")
    else:
        status_messages.append("Moisture absorber OFF")
    if not status_messages:
        status_messages.append("All devices OFF")
    
    return jsonify({
        "timestamps": timestamps,
        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "device_status": device_status,
        "status_messages": status_messages
    })

# Main execution
if __name__ == '__main__':
    try:
        # Create static folder if it doesn't exist
        if not os.path.exists('static'):
            os.makedirs('static')
    
        # Start Isolation Forest
        api_url = "https://api.thingspeak.com/channels/2920657/feeds.json?api_key=GTDM3TTFE1THM92Z"
        mqtt_broker = "dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud"
        mqtt_port = 1883
        mqtt_topic = "COMP4436/home/control/anomalies"

        real_time_if = RealTimeIsolationForest(api_url, mqtt_broker, mqtt_port, mqtt_topic)
        real_time_if.run()
        
        # Initialize MQTT client and start listening for messages
        print("Starting MQTT client...")
        success = mqtt_client.start()
        if not success:
            print("Warning: MQTT client failed to start, continuing without MQTT")
        
        # Start Flask app
        print("Starting Flask server...")
        app.run(host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        shutdown_mqtt()
        sys.exit(0)
    except Exception as e:
        print(f"\nError occurred: {e}")
        shutdown_mqtt()
        sys.exit(1)