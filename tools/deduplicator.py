import hashlib
import json
import paho.mqtt.client as paho
from collections import deque
from dotenv import load_dotenv
import os
from pymavlink import mavutil
from pymavlink.dialects.v20 import custom as mavlink

load_dotenv()

# Constants
BASE_TOPIC = "base_station/+/messages"
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

parser = mavlink.MAVLink(None, srcSystem=255, srcComponent=1)

# Deque to store the last 100 message hashes
recent_hashes = deque(maxlen=100)

# Helper function to compute the hash of a message
def compute_hash(message):
    message_str = json.dumps(message, sort_keys=True)
    return hashlib.sha256(message_str.encode('utf-8')).hexdigest()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code: {rc}")
    client.subscribe(BASE_TOPIC, qos=2)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    message = payload.get("message")
    if message:
        message_hash = compute_hash(message)
        if message_hash in recent_hashes:
            print("Duplicate message detected")
        else:
            recent_hashes.append(message_hash)
            print("New message received and stored")
            mav_bin_msg = bytes(message)
            try:
                msg = parser.parse_buffer(mav_bin_msg)[0]
                print(msg.to_dict())
            except Exception as e:
                print(f"Error parsing message: {e}")

# MQTT Client setup
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT)

client.loop_forever()
