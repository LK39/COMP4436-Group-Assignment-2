import Adafruit_DHT
import requests
import time
from time import sleep
import RPi.GPIO as GPIO
import Adafruit_ADS1x15 as ADS
import paho.mqtt.client as paho
from paho import mqtt
import json

YOUR_USERNAME="hyuvuhjb"
YOUR_PASSWORD="Qweasd12"
YOUR_CLUSTER_URL="dd28cecf47f84578948ef8d895d0d2cb.s1.eu.hivemq.cloud"
write_api_key = 'GTDM3TTFE1THM92Z'
channel_id = '2920657'

adc = ADS.ADS1115()
sensor = Adafruit_DHT.DHT11
pin = 4 # GPIO pin number for Data
values = [0]*4
        
# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(YOUR_USERNAME, YOUR_PASSWORD)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect(YOUR_CLUSTER_URL, 8883)
#qos=min(pub_qos,sub_qos)
client.subscribe("COMP4436/home/RPI4/#", qos=1)

client.loop_start()

while True:
    for i in range(4):
        #values[1]=controller,values[2]=sound sensor,values[3]=light sensor
        values[i] = adc.read_adc(i, gain=1)
    sound, light=values[2],values[3]
    print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin) 
    if humidity is not None and temperature is not None and sound is not None and light is not None: 
        print(f'Temperature: {temperature:.1f}°C Humidity: {humidity:.1f}% Sound: {sound} Light: {light}')
    # Send data to ThingSpeak  
        requests.post(f'https://api.thingspeak.com/update?api_key={write_api_key}&field1={temperature}&field2={humidity}&field3={sound}&field4={light}')
        payload = json.dumps({
            "temperature": temperature,
            "humidity": humidity,
            "sound": sound,
            "light": light
        })
        
        client.publish("COMP4436/home/RPI4/sensors", payload, qos=1)
        print(f"Published combined data: {payload}")
    else: 
        print('Failed to get reading. Try again!')
    
    time.sleep(15)  # Send data every 15 seconds
    
client.loop_stop()
client.disconnect()
