import logging
import os
import time
from logging.handlers import RotatingFileHandler
import modules.mqtt as mqtt
import modules.db as db
from datetime import datetime

if __name__ == "__main__":
    # Configure the logger
    log_dir = os.path.join("logs", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                log_file, maxBytes=1024 * 1024 * 5, backupCount=5
            ),  # 5 MB per file, keep 5 backups
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    # Create/start the MQTT client
    mqtt_client = mqtt.MqttClient()

    # Database setup
    conn = db.create_connection(db.DB_PATH)
    db.create_tables(conn)

    # Main loop
    while True:
        # Process messages from the db_queue
        while not mqtt_client.db_queue.empty():
            message = mqtt_client.db_queue.get()
            db.insert_message(conn, message)
        time.sleep(1)
