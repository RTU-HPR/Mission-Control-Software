import sqlite3
import json
import os
import logging
from pymavlink.dialects.v20 import custom as mavlink

# Database setup
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(PROJECT_DIR, "..", "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "database.db")

logger = logging.getLogger(__name__)


def create_connection(db_path):
    conn = sqlite3.connect(db_path)
    return conn


def create_mavlink_table(conn, msg_type):
    cursor = conn.cursor()
    mavlink_message_class = getattr(mavlink, f"MAVLink_{msg_type.lower()}_message")
    fields = mavlink_message_class.fieldnames
    field_types = mavlink_message_class.fieldtypes
    columns = ", ".join(
        [
            f"{field} {get_sqlite_type(field_type)}"
            for field, field_type in zip(fields, field_types)
        ]
    )
    columns += ", binary BLOB"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {msg_type} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            {columns}
        )
    """)
    conn.commit()


def get_sqlite_type(mavlink_type):
    if mavlink_type in [
        "uint8_t",
        "int8_t",
        "uint16_t",
        "int16_t",
        "uint32_t",
        "int32_t",
        "uint64_t",
        "int64_t",
    ]:
        return "INTEGER"
    elif mavlink_type in ["char", "uint8_t_mavlink_version"]:
        return "TEXT"
    elif mavlink_type in ["float", "double"]:
        return "REAL"
    elif mavlink_type == "list":
        return "TEXT"
    else:
        return "BLOB"


def insert_message(conn, message):
    logger.debug(f"Inserting message into database: {message}")
    timestamp = message["timestamp"]
    mavlink_message = message["message"]
    msg_type = mavlink_message["mavpackettype"]
    data = {k: v for k, v in mavlink_message.items() if k not in ["mavpackettype"]}
    logger.debug(f"Timestamp: {timestamp}, Message type: {msg_type}, Data: {data}")

    # Check if the table exists, and create it if it doesn't
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{msg_type}'"
    )
    if not cursor.fetchone():
        logger.debug(f"Creating table for message type: {msg_type}")
        create_mavlink_table(conn, msg_type)

    # Check if all fields exist in the table, and add them if they don't
    cursor.execute(f"PRAGMA table_info({msg_type})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    new_columns = set(data.keys())
    for column in new_columns - existing_columns:
        logger.debug(f"Adding column {column} to table {msg_type}")
        column_type = (
            "list" if isinstance(data[column], list) else type(data[column]).__name__
        )
        cursor.execute(
            f"ALTER TABLE {msg_type} ADD COLUMN {column} {get_sqlite_type(column_type)}"
        )
    conn.commit()

    fields = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data.values()])

    # Convert list to JSON string if 'binary' field or any list field exists
    for key, value in data.items():
        if isinstance(value, list):
            data[key] = json.dumps(value)

    logger.debug(f"Inserting {msg_type} data: {data}")

    cursor.execute(
        f"""
            INSERT INTO {msg_type} (timestamp, {fields})
            VALUES (?, {placeholders})
        """,
        (timestamp, *data.values()),
    )
    conn.commit()
