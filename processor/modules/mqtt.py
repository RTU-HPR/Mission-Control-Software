import hashlib
import json
import os
import threading
import time
import queue
import dataclasses
import logging
import paho.mqtt.client as paho
from collections import deque
from dotenv import load_dotenv
from pymavlink.dialects.v20 import custom as mavlink

load_dotenv()

ALL_TOPICS = "#"

BASE_STATION_TX_TOPIC = "base_station/+/commands"
BASE_STATION_RX_TOPIC = "base_station/+/messages"
BASE_STATION_STATUS_TOPIC = "base_station/+/status"

PROCESSED_MESSAGES_TOPIC = "processed/"

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


@dataclasses.dataclass
class MqttMessage:
    topic: str
    payload: dict


class MqttClient:
    def __init__(self):
        self.logger = logging.getLogger("MQTTClient")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        # logger.setLevel(logging.DEBUG)

        self.logger.info("Initializing MQTT client")
        self.start_time = time.time()
        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(MQTT_BROKER, MQTT_PORT)

        self.recent_hashes = deque(maxlen=1000)
        self.incoming_queue = queue.Queue()
        self.outgoing_queue = queue.Queue()
        self.db_queue = queue.Queue()

        self.received_count = 0
        self.sent_count = 0
        self.processed_count = 0
        self.mavlink_message_count = {}

        self.parser = mavlink.MAVLink(
            None, srcSystem=255, srcComponent=1
        )  # Only used for parsing
        logging.info("Mavlink parser initialized")

        self.sender_thread = threading.Thread(
            target=self._publish_processed_messages, daemon=True
        )
        self.receiver_thread = threading.Thread(
            target=self._process_incoming_messages, daemon=True
        )
        self.stats_thread = threading.Thread(target=self._print_stats, daemon=True)
        self.sender_thread.start()
        self.receiver_thread.start()
        self.stats_thread.start()
        self.logger.info("Threads started")

        self.client.loop_start()
        self.logger.info("MQTT client loop started")

    @staticmethod
    def _compute_hash(message) -> str:
        message_str = json.dumps(message, sort_keys=True)
        return hashlib.sha256(message_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _current_millis() -> int:
        return int(round(time.time() * 1000))

    def _print_stats(self) -> None:
        while True:
            info_str = f"\nOn time: {time.time() - self.start_time:.1f} seconds\n"
            info_str += f"Queue sizes: Incoming: {self.incoming_queue.qsize()}, Outgoing: {self.outgoing_queue.qsize()}, DB: {self.db_queue.qsize()}\n"
            info_str += f"Received: {self.received_count}, Sent: {self.sent_count}, Processed: {self.processed_count}\n"
            for msg_type, count in self.mavlink_message_count.items():
                info_str += f"{msg_type}: {count}\n"
            self.logger.info(info_str)
            time.sleep(5)

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        self.logger.info(f"Connected with result code: {rc}")
        client.subscribe(ALL_TOPICS, qos=2)
        logging.debug("Subscribed to all topics")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            self.incoming_queue.put_nowait(msg)
            self.received_count += 1
        except queue.Full:
            self.logger.warning("Queue full, ignoring message")
            return
        except Exception as e:
            self.logger.error(e)
            return

    def _process_incoming_messages(self) -> None:
        while True:
            try:
                msg = self.incoming_queue.get()
                self._process_message(msg)
            except Exception as e:
                self.logger.error(e)
            time.sleep(0.01)

    def _process_message(self, msg) -> None:
        try:
            mqtt_message = MqttMessage(topic=msg.topic, payload=json.loads(msg.payload))
            # Deduplicate mavlink messages
            if "base_station" in msg.topic and "message" in msg.topic:
                self._process_mavlink_message(mqtt_message)
        except Exception as e:
            self.logger.error(e)
            return

    def _process_mavlink_message(self, mqtt_message: MqttMessage) -> None:
        mavlink_message = mqtt_message.payload["message"]
        self.logger.debug(f"Processing MAVLink message: {mavlink_message}")
        # Check if message is a MAVLink message by checking for the magic number
        if mavlink_message[0] != 253:
            self.logger.warning(f"MAVLink message invalid: {mavlink_message}")
            return

        # Check if already processed
        message_hash = self._compute_hash(mavlink_message)
        if message_hash in self.recent_hashes:
            self.logger.debug("Message already processed")
            return
        self.recent_hashes.append(message_hash)

        # Convert the message to bytes
        mav_bin_msg = bytes(mavlink_message)

        # Then parse the message and put it in the processed messages topic
        msg = self.parser.parse_buffer(mav_bin_msg)[0]
        if msg:
            self.logger.debug(f"Parsed MAVLink message: {msg}")
            msg_type = msg.get_type()
            if msg_type in self.mavlink_message_count:
                self.mavlink_message_count[msg_type] += 1
            else:
                self.mavlink_message_count[msg_type] = 1
            self.processed_count += 1
            msg_dict = msg.to_dict()
            msg_dict["binary"] = list(mav_bin_msg)
            self.outgoing_queue.put(msg_dict)

    def _publish_processed_messages(self) -> None:
        while True:
            try:
                msg = self.outgoing_queue.get()
                data = {"timestamp": self._current_millis(), "message": msg}
                self.db_queue.put(data)
                self.client.publish(PROCESSED_MESSAGES_TOPIC, json.dumps(data), qos=2)
                self.logger.debug(f"Published processed message: {data}")
                self.sent_count += 1
            except Exception as e:
                self.logger.error(e)
            time.sleep(0.01)


if __name__ == "__main__":
    mqtt_client = MqttClient()
    while True:
        time.sleep(1)

