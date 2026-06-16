import paho.mqtt.client as paho
import os
from dotenv import load_dotenv

load_dotenv("passes.env")

HOST = "mqtt.ics.ele.tue.nl"  #or mqtt.ics.ele.tue.nl
USER = "robot_26_1" #or robot_58_1
PASS = os.getenv("pass26")
TOPIC = "/pynqbridge/26/send"  #or /pynqbridge/58/send

client = paho.Client(paho.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)

print("How many messages do you want to send?")
num_messages = int(input())
try:
    client.connect(HOST)
    for i in range(num_messages):
        msg = "Hi "+ str(i+1)
        client.publish(TOPIC, msg)
        client.publish('/pynqbridge/26/recv', msg + " Delivered to 26")
        #print("Sent!")
    client.disconnect()
except Exception as e:
    print(f"Error: {e}")