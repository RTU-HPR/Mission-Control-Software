import logging
import os
import time
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
import modules.mqtt as mqtt
from datetime import datetime
from modules.db import Database
from multiprocessing import Process, Queue
import uvicorn

def start_mqtt_client(db):
    mqtt_client = mqtt.MqttClient()
    while True:
        while not mqtt_client.db_queue.empty():
            message = mqtt_client.db_queue.get()
            db.insert_message(message)
        time.sleep(1)

def init_logging():
    # Configure the logger
    log_dir = os.path.join("logs", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "app.log")
    log_queue = Queue()
    queue_handler = QueueHandler(log_queue)
    queue_listener = QueueListener(log_queue, *logging.getLogger().handlers)
    queue_listener.start()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                log_file, maxBytes=1024 * 1024 * 5, backupCount=5
            ),
            logging.StreamHandler(),
            queue_handler,
        ],
    )

if __name__ == "__main__":
    init_logging()
    logger = logging.getLogger("Main")

    # Database setup
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_DIR = os.path.join(PROJECT_DIR, "database")
    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_DIR, "database.db")

    db_instance = Database(DB_PATH)
    conn = db_instance.create_connection()

    app = db_instance.app

    # Start MQTT client process
    mqtt_process = Process(target=start_mqtt_client, args=(db_instance,))
    mqtt_process.start()

    # Start FastAPI server directly
    uvicorn.run(app, host="localhost", port=8000, reload=False)

    # Wait for processes to complete
    mqtt_process.join()

