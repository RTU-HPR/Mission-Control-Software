import csv
from datetime import datetime
import os
import binascii

class Logger:
  def __init__(self) -> None:
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create logs folder if it doesn't exist
    logs_dir = os.path.join(script_dir, "..", "logs")
    
    # Create a folder for the current date if it doesn't exist
    time_now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    current_date_dir = os.path.join(logs_dir, time_now)
    
    # os.makedirs creates all intermediate-level directories needed to create the leaf directory
    os.makedirs(current_date_dir, exist_ok=True)
    
    # Create log files
    self.telemetry_log_file = os.path.join(current_date_dir, f"telemetry.csv")
    self.telecommand_log_file = os.path.join(current_date_dir, f"telecommand.csv")

    header = ["Time", "Packet data"]
    with open(self.telemetry_log_file, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
    with open(self.telecommand_log_file, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)


  def log_telecommand_data(self, packet_data):
    hex_data = binascii.hexlify(packet_data).decode("utf-8")
    with open(self.telecommand_log_file, "a", newline='') as file:
      writer = csv.writer(file)
      writer.writerow([datetime.now().strftime("%H:%M:%S.%f")[:-3], hex_data])
  
  def log_telemetry_data(self, packet_data):
    hex_data = binascii.hexlify(packet_data).decode("utf-8")
    with open(self.telemetry_log_file, "a", newline='') as file:
      writer = csv.writer(file)
      writer.writerow([datetime.now().strftime("%H:%M:%S.%f")[:-3], hex_data])
    