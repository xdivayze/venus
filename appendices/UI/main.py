import asyncio
import websockets
import json
import paho.mqtt.client as paho
import time

connected_clients = set()
loop = None

KNOWN_EVENTS = ["positions", "cliff", "hill", "sample"]

def current_time():
    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())

async def broadcast(message_str):
    """Send the JSON message to all connected browsers."""
    if connected_clients:
        await asyncio.gather(*(client.send(message_str) for client in connected_clients), return_exceptions=True)

def parse_send_message(raw: str):
    """
    Parse 'event: {json}' from a /send topic message.
    Returns (event, payload_dict) or (None, None) on failure.
    """
    raw = raw.strip()
    for event in KNOWN_EVENTS:
        if raw.lower().startswith(f"{event}:"):
            json_part = raw[len(event) + 1:].strip()
            json_part = json_part.replace('\\"', '"')
            try:
                return event, json.loads(json_part)
            except json.JSONDecodeError as e:
                print(f"  [WARN] Failed to parse JSON for event '{event}': {e}")
                return None, None
    print(f"  [WARN] Unrecognised command: {raw!r}")
    return None, None

def messageHandler(client, userdata, message):
    decoded_payload = message.payload.decode('utf-8')
    topic = message.topic
    parts = topic.split('/')
    robot_id = parts[2] if len(parts) >= 3 else "unknown"
    event_segment = parts[3] if len(parts) >= 4 else ""

    print(f"{current_time()}: [{topic}] -> {decoded_payload}")

    if event_segment == 'send':
        # New format: "event: {json}" — parse and remap to virtual event topic
        event, data = parse_send_message(decoded_payload)
        if event is None:
            return
        virtual_topic = f"/pynqbridge/{robot_id}/{event}"
        envelope = {"topic": virtual_topic, "data": data}
        print(f"  → Mapped to {virtual_topic!r}: {data}")

    elif event_segment in KNOWN_EVENTS:
        # Old format: published directly to /positions, /cliff, /hill, /sample
        try:
            data = json.loads(decoded_payload)
        except json.JSONDecodeError:
            data = {"raw_text": decoded_payload}
        envelope = {"topic": topic, "data": data}

    else:
        # recv or anything else — just forward as raw
        try:
            data = json.loads(decoded_payload)
        except json.JSONDecodeError:
            data = {"raw_text": decoded_payload}
        envelope = {"topic": topic, "data": data}

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
        topicSubList=[
            "/pynqbridge/58/send",
            "/pynqbridge/58/recv",
            "/pynqbridge/58/positions",
            "/pynqbridge/58/cliff",
            "/pynqbridge/58/hill",
            "/pynqbridge/58/sample",
        ],
        messageHandler=messageHandler
    )
    Broker(
        host="mqtt.ics.ele.tue.nl",
        username="robot_26_1",
        password="L9bkrgZz",
        topicSubList=[
            "/pynqbridge/26/send",
            "/pynqbridge/26/recv",
            "/pynqbridge/26/positions",
            "/pynqbridge/26/cliff",
            "/pynqbridge/26/hill",
            "/pynqbridge/26/sample",
        ],
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