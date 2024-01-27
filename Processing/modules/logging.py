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
    
    # Create log files with date and time as name and type
    telemetry_log_file = os.path.join(current_date_dir, f"telemetry.csv")
    telecommand_log_file = os.path.join(current_date_dir, f"telecommand.csv")
    rotator_log_file = os.path.join(current_date_dir, f"rotator.csv")
    
    self.telemetry_log_file = open(telemetry_log_file, "a")
    self.telecommand_log_file = open(telecommand_log_file, "a")
    self.rotator_log_file = open(rotator_log_file, "a")
    
    self.telemetry_log_writer = csv.writer(self.telemetry_log_file)
    self.telecommand_log_writer = csv.writer(self.telecommand_log_file)
    self.rotator_log_writer = csv.writer(self.rotator_log_file)
    
    # Write headers
    header = ["Time", "Packet data"]
    self.telemetry_log_writer.writerow(header)
    self.telecommand_log_writer.writerow(header)
    self.rotator_log_writer.writerow(header)
  
  def log_telecommand_data(self, packet_data):
    hex_data = binascii.hexlify(packet_data).decode("utf-8")
    self.telecommand_log_writer.writerow([datetime.now().strftime("%H:%M:%S"), hex_data])
  
  def log_rotator_data(self, packet_data):
    hex_data = binascii.hexlify(packet_data).decode("utf-8")
    self.rotator_log_writer.writerow([datetime.now().strftime("%H:%M:%S"), hex_data])
  
  def log_telemetry_data(self, packet_data):
    hex_data = binascii.hexlify(packet_data).decode("utf-8")
    self.telemetry_log_writer.writerow([datetime.now().strftime("%H:%M:%S"), hex_data])
    