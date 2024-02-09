from modules.sync import MQTTSync
import time
from config import SYNC_SERVER_URL, SYNC_SERVER_PORT, SYNC_SERVER_TOPIC

testcon = MQTTSync(SYNC_SERVER_URL, SYNC_SERVER_PORT, SYNC_SERVER_TOPIC)

while True:
    testcon.publishPacket("test packet".encode())
    time.sleep(1)