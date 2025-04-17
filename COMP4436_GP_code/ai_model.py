import paho.mqtt.client as paho
from paho import mqtt
import json

YOUR_USERNAME = "hyuvuhjb"
YOUR_PASSWORD = "Qweasd12"
YOUR_CLUSTER_URL = "dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud"
subscribe_channel="COMP4436/home/RPI4/sensors"
publish_channel="COMP4436/home/lightcontrol"
results="light on"

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with code: {rc}")
    client.subscribe(subscribe_channel, qos=1)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received sensor batch:")
        print(f"  Temp: {data['temperature']}°C")
        print(f"  Humi: {data['humidity']}%")
        print(f"  Sound: {data['sound']}")
        print(f"  Light: {data['light']}")
        results="light on" if data['light'] <3000 else "light off"
            
        client.publish(publish_channel, results, qos=1)
        print(f"Trigger published: {results}\nchannels: {publish_channel}")
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")

client = paho.Client(client_id="json_subscriber", protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(YOUR_USERNAME, YOUR_PASSWORD)
client.connect(YOUR_CLUSTER_URL, 8883)

print("Listening for JSON sensor data...")
client.loop_forever()