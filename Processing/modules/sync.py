import paho.mqtt.client as paho
from paho import mqtt
import os
import random

class MQTTSync:
    def __init__(self, SYNC_SERVER_URL, SYNC_SERVER_PORT, SYNC_SERVER_TOPIC) -> None:
        self._mqttServer = SYNC_SERVER_URL
        self._mqttPort = SYNC_SERVER_PORT
        if "MQTT_USERNAME" in os.environ and "MQTT_PASSWORD" in os.environ:
            self._mqttUsername = os.environ["MQTT_USERNAME"]
            self._mqttPassword = os.environ["MQTT_PASSWORD"]
        else:
            print("MQTT Credentials could not be loaded from the ENV!")
            raise Exception("MQTT Credentials not found in environment variables")

        self._clientID = random.randint(100000, 999999)
        self._mqttClient = paho.Client(client_id=str(self._clientID))

        def onMessage(client, userdata, msg):
            if msg.topic == SYNC_SERVER_TOPIC:
                self.packetReceived(msg)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self._mqttClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self._mqttClient.username_pw_set(self._mqttUsername, self._mqttPassword)

        self._mqttClient.on_message = onMessage
        self._mqttClient.on_connect = on_connect

        self._mqttClient.connect(self._mqttServer, self._mqttPort)
        self._mqttClient.subscribe("packets")
        self._mqttClient.loop_forever()

    def publishPacket(self):
        pass

    def packetReceived(self, message):
        pass