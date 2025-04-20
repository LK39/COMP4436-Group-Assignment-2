# server.py on client machine
from flask import Flask, request, jsonify
from flask_cors import CORS
from AI_Prediction import AI_Prediction
from MQTTClient import MQTTClient
import pandas as pd
import threading
import torch
import atexit

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Initialize your AI model
input_size = 3
hidden_size = 10
num_layers = 10
output_size = 3
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_path = './10_10/lstm_model_10_10.pth'
prediction_model = AI_Prediction(input_size, hidden_size, num_layers, output_size, device, model_path)

mqtt_client = MQTTClient()
# Initialize MQTT client and start listening for messages
mqtt_client.start()

# Current state
system_on = False
thresholds = {
    "Temperature": 25.0,
    "Humidity": 60.0,
    "Light": 500.0
}
forecast_minutes = 30
channel_id = "2924396"
read_api_key = "XJXTKLW6V1LNWDQ6"

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

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "online"})

@app.route('/settings', methods=['POST'])
def update_settings():
    global thresholds, forecast_minutes
    data = request.json
    
    if 'thresholds' in data:
        thresholds = data['thresholds']
    
    if 'forecast_minutes' in data:
        forecast_minutes = data['forecast_minutes']
    
    return jsonify({"success": True})

# On your server - add a function to turn off all appliances
def turn_off_all_appliances():
    """Turn off all connected appliances"""
    # Assuming you have a dictionary or database of appliance states
    global device_status
    
    appliance_states = {
        "air_conditioner": "OFF",
        "lights": "OFF",
        "moisture_absorber": "OFF"
    }
    
    # Update the device status
    device_status = appliance_states
    
    # Actual code to send signals to physical devices would go here
    # For example: send MQTT messages, call IoT APIs, etc.
    
    # Log the action
    print("All appliances turned off due to system shutdown")

    mqtt_client.publish(mqtt_client.publish_channel, "lights off", qos=1)
    
    return appliance_states

@app.route('/system_status', methods=['POST'])
def update_system_status():
    global system_on
    data = request.json
    
    # Debug logging
    print(f"System status update received: {data}")
    
    # Get system_on status
    if 'system_on' in data:
        system_on = data.get('system_on')
        print(f"System status set to: {system_on}")
    else:
        return jsonify({"error": "Invalid data format, expected {'system_on': true|false}"}), 400
    
    # Handle turning off all appliances when system is turned off
    if not system_on and data.get('turn_off_all_appliances', False):
        # Turn off all appliances
        appliance_states = turn_off_all_appliances()
        
        return jsonify({
            "success": True, 
            "message": "System turned off and all appliances deactivated",
            "device_status": appliance_states
        })
    
    # Handle regular system status updates
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
        
        MQTTClient.publish(MQTTClient.publish_channel, "lights on" if device_status["lights"] == "ON" else "lights off", qos=1)
    
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

if __name__ == '__main__':
    try:
        # Start Flask app
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("\nReceived keyboard interrupt. Shutting down...")
    finally:
        # Always ensure MQTT client is stopped
        shutdown_mqtt()