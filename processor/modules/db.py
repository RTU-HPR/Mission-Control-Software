import sqlite3
import json
import logging
from pymavlink.dialects.v20 import custom as mavlink
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = self.create_connection()
        self.logger = logging.getLogger("Database")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        # self.logger.setLevel(logging.DEBUG)
        self.app = FastAPI()
        self.setup_routes()

    def create_connection(self):
        return sqlite3.connect(self.db_path)

    def create_mavlink_table(self, msg_type):
        self.logger.info(f"Creating table for message type: {msg_type}")
        cursor = self.conn.cursor()
        mavlink_message_class = getattr(mavlink, f"MAVLink_{msg_type.lower()}_message")
        fields = mavlink_message_class.fieldnames
        field_types = mavlink_message_class.fieldtypes
        columns = ", ".join(
            [
                f"{field} {self.get_sqlite_type(field_type)}"
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
        self.conn.commit()

    def get_sqlite_type(self, mavlink_type):
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

    def insert_parsed_data(self, msg_type, timestamp, data):
        cursor = self.conn.cursor()
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data.values()])

        # Convert list to JSON string if 'binary' field or any list field exists
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = json.dumps(value)

        self.logger.debug(f"Inserting {msg_type} data: {data}")

        cursor.execute(
            f"""
            INSERT INTO {msg_type} (timestamp, {fields})
            VALUES (?, {placeholders})
        """,
            (timestamp, *data.values()),
        )
        self.conn.commit()

    def insert_message(self, message):
        self.logger.debug(f"Inserting message into database: {message}")
        created_at = message["timestamp"]
        mavlink_message = message["message"]
        msg_type = mavlink_message["mavpackettype"]
        try:
            timestamp = mavlink_message["time_usec"]
        except KeyError:
            timestamp = 0
        data = {k: v for k, v in mavlink_message.items() if k not in ["mavpackettype"]}
        self.logger.debug(f"Created at: {created_at}, Message type: {msg_type}, Timestamp: {timestamp}, Data: {data}")

        # Check if the table exists, and create it if it doesn't
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{msg_type}'"
        )
        if not cursor.fetchone():
            self.logger.debug(f"Creating table for message type: {msg_type}")
            self.create_mavlink_table(msg_type)

        # Check if all fields exist in the table, and add them if they don't
        cursor.execute(f"PRAGMA table_info({msg_type})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        new_columns = set(data.keys())
        for column in new_columns - existing_columns:
            self.logger.debug(f"Adding column {column} to table {msg_type}")
            column_type = "list" if isinstance(data[column], list) else type(data[column]).__name__
            cursor.execute(
                f"ALTER TABLE {msg_type} ADD COLUMN {column} {self.get_sqlite_type(column_type)}"
            )
        self.conn.commit()

        self.insert_parsed_data(msg_type, created_at, data)

    def setup_routes(self):
        @self.app.get("/data/{msg_type}")
        def get_data(
            msg_type: str,
            start_time: int,
            end_time: int,
            columns: Optional[List[str]] = Query(None),
            include_binary: bool = False
        ):
            conn = self.create_connection()
            cursor = conn.cursor()

            # Validate columns
            cursor.execute(f"PRAGMA table_info({msg_type})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if columns:
                for column in columns:
                    if column not in existing_columns:
                        raise HTTPException(status_code=400, detail=f"Column {column} does not exist in table {msg_type}")

            # Build query
            selected_columns = columns if columns else existing_columns - {"binary"}
            if include_binary:
                selected_columns.add("binary")
            selected_columns_str = ", ".join(selected_columns)

            query = f"""
                SELECT {selected_columns_str}
                FROM {msg_type}
                WHERE timestamp BETWEEN ? AND ?
            """
            cursor.execute(query, (start_time, end_time))
            rows = cursor.fetchall()

            # Convert rows to list of dicts
            result = [dict(zip(selected_columns, row)) for row in rows]
            return result
