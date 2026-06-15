import asyncio
import websockets
import json
import paho.mqtt.client as paho
import time

connected_clients = set()
loop = None 

def current_time():
    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())

async def broadcast(message_str):
    """Send the JSON message to all connected browsers."""
    if connected_clients:
        await asyncio.gather(*(client.send(message_str) for client in connected_clients), return_exceptions=True)

def messageHandler(client, userdata, message):
    decoded_payload = message.payload.decode('utf-8')
    print(f"{current_time()}: [{message.topic}] -> {decoded_payload}")
    
    try:
        data = json.loads(decoded_payload)
    except json.JSONDecodeError:
        data = {"raw_text": decoded_payload}
        
    envelope = {
        "topic": message.topic,
        "data": data
    }
    
    if loop is not None:
        asyncio.run_coroutine_threadsafe(broadcast(json.dumps(envelope)), loop)

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

def choose_robot(robot_number):
    if robot_number == 58:
        Broker(
            host="mqtt.ics.ele.tue.nl",
            username="robot_58_1",
            password="jydFjze6",
            topicSubList=["/pynqbridge/58/recv", "/pynqbridge/58/send"],
            messageHandler=messageHandler
        )
    elif robot_number == 26:
        Broker(
            host="mqtt.ics.ele.tue.nl",
            username="robot_26_1",
            password="L9bkrgZz",
            topicSubList=["/pynqbridge/26/recv", "/pynqbridge/26/send"],
            messageHandler=messageHandler
        )

async def ws_handler(websocket):
    """Handles new WebSocket connections from the frontend."""
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def main():
    global loop
    loop = asyncio.get_running_loop()
    
    Broker(
            host="mqtt.ics.ele.tue.nl",
            username="robot_58_1",
            password="jydFjze6",
            topicSubList=["/pynqbridge/58/recv", "/pynqbridge/58/send", "/pynqbridge/58/cliff", "/pynqbridge/58/hill", "/pynqbridge/58/sample", "/pynqbridge/58/positions"],
            messageHandler=messageHandler
        )
    Broker(
            host="mqtt.ics.ele.tue.nl",
            username="robot_26_1",
            password="L9bkrgZz",
            topicSubList=["/pynqbridge/26/recv", "/pynqbridge/26/send", "/pynqbridge/26/cliff", "/pynqbridge/26/hill", "/pynqbridge/26/sample", "/pynqbridge/26/positions"],
            messageHandler=messageHandler
        )
    
    print("\nStarting WebSocket server on ws://localhost:8765...")
    async with websockets.serve(ws_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nListener stopped by user.")
