import time
import json
import socket
from pymavlink import mavutil
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv
import os
import dataclasses
import typing
import random

load_dotenv()

DEVICE_ID = 1
BASE_TOPIC = f"base_station/{DEVICE_ID}"
COMMAND_TOPIC = f"{BASE_TOPIC}/commands"
MESSAGE_TOPIC = f"{BASE_TOPIC}/messages"
STATUS_TOPIC = f"{BASE_TOPIC}/status"

# Helper function to get current UNIX timestamp in ms
def current_millis():
    return int(round(time.time() * 1000))

# Helper function to get device hostname and addresses
def get_device_info():
    hostname = socket.gethostname()
    addresses = socket.gethostbyname_ex(hostname)[2]
    return hostname, addresses

# MQTT Callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code: {rc}")
    publish_status(client, "CONNECTED")

def on_disconnect(client, userdata, rc, properties=None):
    print(f"Disconnected with result code: {rc}")
    publish_status(client, "DISCONNECTED")

def on_message(client, userdata, msg):
    print("Received command:")
    # command = json.loads(msg.payload)
    print(msg.payload)

def publish_status(client, status):
    hostname, addresses = get_device_info()
    status_message = {
        "status": status,
        "connectedAt": current_millis() if status == "CONNECTED" else None,
        "hostname": hostname,
        "addresses": addresses
    }
    client.publish(STATUS_TOPIC, json.dumps(status_message), qos=2)

def publish_data(client, message):
    data_array = []
    for byte in message:
        data_array.append(byte)
    data_message = {
        "createdAt": current_millis(),
        "message": data_array
    }
    print(f"Publishing message: {data_message}")
    client.publish(MESSAGE_TOPIC, json.dumps(data_message), qos=2)

# MQTT Client setup
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
client.will_set(STATUS_TOPIC, json.dumps({
    "status": "DISCONNECTED",
    "connectedAt": None,
    "hostname": socket.gethostname(),
    "addresses": socket.gethostbyname_ex(socket.gethostname())[2]
}), qos=2, retain=False)
client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")))
client.subscribe(COMMAND_TOPIC, qos=2)
client.loop_start()

@dataclasses.dataclass
class StreamItem:
    name: str
    fn: typing.Optional[typing.Callable]
    frequency: float
    next_send_t: typing.Optional[float] = 0
    period: typing.Optional[float] = None

    def __post_init__(self):
        self.period = 1 / self.frequency


master = mavutil.mavlink_connection("udpout:localhost:14540", source_system=255, source_component=0, dialect="custom")

heartbeat = lambda: publish_data(client, master.mav.heartbeat_encode(random.randint(0, 100)).pack(master.mav))
balloon_report = lambda: publish_data(client, master.mav.balloon_report_encode(random.randint(0, 100), 0, 0, 0, 0, 0).pack(master.mav))
streams = [
    StreamItem("heartbeat", heartbeat, 0.1),
    StreamItem("balloon_report", balloon_report, 1),
]

while True:
    t = time.time()
    for si in streams:
        if si.next_send_t < t:
            si.fn()
            si.next_send_t = t + si.period
    time.sleep(0.01)

client.loop_stop()
