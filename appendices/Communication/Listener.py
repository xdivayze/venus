import paho.mqtt.client as paho
import time
import os
from dotenv import load_dotenv

load_dotenv("passes.env")

def current_time():
    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())

class Broker:
    def __init__(self, host, username, password, topicSubList, messageHandler):
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(username, password)
        self.client.on_message = messageHandler
        
        if self.client.connect(host=host) != 0:
            raise RuntimeError("Couldn't connect to the MQTT host")
        for topic in topicSubList:
            self.client.subscribe(topic)
        print(f"Listening for messages on: {topicSubList}")
        
        self.client.loop_start() 

def messageHandler(client, userdata, message):
    print(f"{current_time()}: [{message.topic}] -> {message.payload.decode('utf-8')}")


if __name__ == "__main__":
    Broker(
        host="mqtt.ics.ele.tue.nl",
        username="robot_58_1",
        password=os.getenv("pass58"),
        topicSubList=["/pynqbridge/58/recv", "/pynqbridge/58/send"],
        messageHandler=messageHandler
    )
    Broker(
        host="mqtt.ics.ele.tue.nl",
        username="robot_26_1",
        password=os.getenv("pass26"),
        topicSubList=["/pynqbridge/26/recv", "/pynqbridge/26/send"],
        messageHandler=messageHandler
    )
    
    try:
        print("Press CTRL+C to stop.\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListener stopped by user.")