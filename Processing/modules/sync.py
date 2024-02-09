import paho.mqtt.client as paho
import os
import random
from config import SYNC_SERVER_URL, SYNC_SERVER_PORT, SYNC_SERVER_TOPIC

class MQTTSync:
    def __init__(self) -> None:
        self._mqttServer = SYNC_SERVER_URL
        self._mqttPort = SYNC_SERVER_PORT
        if "MQTT_USERNAME" in os.environ and "MQTT_PASSWORD":
            self._mqttUsername = os.environ["MQTT_USERNAME"]
            self._mqttPassword = os.environ["MQTT_PASSWORD"]
        else:
            raise Exception()

        self._clientID = random.randint(100000, 999999)
        self._mqttClient = paho.Client(client_id = str(self._clientID))

        def onMessage(client, userdata, msg):
            pass
        self._mqttClient.on_message = onMessage

        self._mqttClient.username_pw_set(self._mqttUsername, self._mqttPassword)