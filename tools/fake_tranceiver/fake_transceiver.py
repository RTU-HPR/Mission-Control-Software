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

start_time = time.time_ns()

# Helper function to get current UNIX timestamp in ms
def current_millis():
    return int(round(time.time() * 1000))

# Helper function to get device hostname and addresses
def get_device_info():
    hostname = socket.gethostname()
    addresses = socket.gethostbyname_ex(hostname)[2]
    return hostname, addresses

def get_time_since_start():
    return round((time.time_ns() - start_time) / 1e3)  # Convert to usec

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
        "timestamp": current_millis(),
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

heartbeat = lambda: publish_data(client, master.mav.heartbeat_encode(random.randint(8000, 10000)).pack(master.mav))
balloon_report = lambda: publish_data(client, master.mav.balloon_report_encode(
    get_time_since_start(),
    mavutil.mavlink.BALLOON_STATE_INIT, # state
    0, # last command id
    0, # last command time usec
    random.randint(6000, 8400), # voltage
    random.randint(30, 100) # rssi
).pack(master.mav))
payload_report = lambda: publish_data(client, master.mav.payload_report_encode(
    get_time_since_start(),
    mavutil.mavlink.PAYLOAD_STATE_INIT, # state
    0, # last command id
    0, # last command time usec
    random.randint(6000, 8400), # voltage
    random.randint(30, 100) # rssi
).pack(master.mav))
balloon_position_report = lambda: publish_data(client, master.mav.position_report_encode(
    get_time_since_start(),
    mavutil.mavlink.VEHICLE_TYPE_BALLOON, # vehicle type
    random.randint(5, 32), # satellites used
    random.randint(0, 8), # fix type
    random.uniform(55, 57), # latitude
    random.uniform(24, 25), # longitude
    random.uniform(10, 32000), # altitude
    random.randint(-32768, 32767), # horizontal speed
    random.randint(-32768, 32767), # vertical speed
    random.randint(0, round(2 * 3.14 * 1000)), # cog
    random.randint(round(-3.14 / 2 * 1000), round(3.14 / 2 * 1000)), # inclination
    random.uniform(10, 32000), # altitude
).pack(master.mav))
payload_position_report = lambda: publish_data(client, master.mav.position_report_encode(
    get_time_since_start(),
    mavutil.mavlink.VEHICLE_TYPE_PAYLOAD, # vehicle type
    random.randint(5, 32), # satellites used
    random.randint(0, 8), # fix type
    random.uniform(55, 57), # latitude
    random.uniform(24, 25), # longitude
    random.uniform(10, 32000), # altitude
    random.randint(-32768, 32767), # horizontal speed
    random.randint(-32768, 32767), # vertical speed
    random.randint(0, round(2 * 3.14 * 1000)), # cog
    random.randint(round(-3.14 / 2 * 1000), round(3.14 / 2 * 1000)), # inclination
    random.uniform(10, 32000), # altitude
).pack(master.mav))
rwc_report = lambda: publish_data(client, master.mav.rwc_report_encode(
    get_time_since_start(),
    mavutil.mavlink.RWC_STATE_INIT, # state
    random.randint(6000, 8400),  # voltage
    random.randint(0, round(2 * 3.14 * 1000)), # cog
    [random.randint(-32768, 32767) for i in range(3)], # ang velocities
    random.randint(0, 32767), # motor rpm
    random.randint(-128, 127), # temperature
).pack(master.mav))
heated_container_report = lambda: publish_data(client, master.mav.heated_container_report_encode(
    get_time_since_start(),
    mavutil.mavlink.HEATED_CONTAINER_STATE_INIT, # state
    random.randint(-32768, 32767),  # air temp
    random.randint(-32768, 32767),  # baro air temp
    random.randint(-32768, 32767),  # heatsink temp
    random.randint(0, 1300), # pressure
    random.randint(0, 32767), # k term
    random.randint(0, 32767), # i term
    random.randint(0, 32767), # duty cycle
).pack(master.mav))
ranging_report = lambda: publish_data(client, master.mav.ranging_report_encode(
    get_time_since_start(),
    mavutil.mavlink.RANGING_STATE_INIT, # state
    random.uniform(54, 57), # latitude
    random.uniform(23, 25), # longitude
    random.uniform(10, 32000), # altitude
    [random.uniform(0, 100000) for i in range(3)], # distances
    [random.randint(0, 100000) for i in range(3)], # time since last ranging
).pack(master.mav))

streams = [
    StreamItem("heartbeat", heartbeat, 1),
    StreamItem("balloon_report", balloon_report, 1),
    StreamItem("payload_report", payload_report, 1),
    StreamItem("balloon_position_report", balloon_position_report, 1),
    StreamItem("payload_position_report", payload_position_report, 1),
    StreamItem("rwc_report", rwc_report, 1),
    StreamItem("heated_container_report", heated_container_report, 1),
    StreamItem("ranging_report", ranging_report, 1),
]

while True:
    t = time.time()
    for si in streams:
        if si.next_send_t < t:
            si.fn()
            si.next_send_t = t + si.period + random.uniform(-0.1, 0.1)  # Add some jitter to the send time
    time.sleep(0.0001)

client.loop_stop()
