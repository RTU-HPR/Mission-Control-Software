from tabulate import tabulate
import time
import os

from modules.connection_manager import ConnectionManager
from modules.processor import PacketProcessor

from config import *

class InfoTables:
  def __init__(self, connection_manager: ConnectionManager, packet_processor: PacketProcessor):
    self.connection_manager = connection_manager
    self.packet_processor = packet_processor
    
    self.TABLE_UPDATE_INTERVAl = 0.01
    self.last_print_time = 0
    
    self.TABLE_HARD_REFRESH_INTERVAL = 10
    self.last_hard_refresh_time = 0
    
  def print_info_tables(self):
    # If a second has passed since the last print, print the tables
    if time.time() - self.last_print_time < self.TABLE_UPDATE_INTERVAl:
      time.sleep(self.TABLE_UPDATE_INTERVAl - (time.time() - self.last_print_time))
      return
    
    # Clear the console needed when rescales cmd
    if time.time() - self.last_hard_refresh_time > self.TABLE_HARD_REFRESH_INTERVAL:
        os.system("cls")
        self.last_hard_refresh_time = time.time()
        
      
    print("\033[1;1H", end="")
    print("RTU High Power Rocketry Team - Ground Station Data Processing Software")
    print("\033[K")  # Clear the line
  
    # Connection Manager
    headers = ["Connected to transceiver", "Next Communication Cycle Start (s)", "Command To Send"]
    
    connected = self.connection_manager.connected_to_transceiver
    cycle_start = round(CYCLE_TIME - (time.time() % CYCLE_TIME), 1)
    command_to_send = self.connection_manager.sending_to_transceiver
    
    table = [[connected, cycle_start, command_to_send]]
    print("Connections")
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="center", disable_numparse=True))
    print("\033[K")  # Clear the line
        
    # Packet Processor
    headers = ["Vehicle", "Time", "Latitude", "Longitude", "GPS Alt (m)", "Baro Alt (m)", "Satellites", "Info/Error", "RSSI (dBm)", "SNR", "Since last packet (s)"]
    
    table = [[], []]

    table[0].append("Balloon")
    if self.packet_processor.bfc_packet_received_time == 0:
      table[0] += ["N/A"]
    else:
      table[0] += [time.strftime("%H:%M:%S", time.localtime(self.packet_processor.bfc_packet_received_time))]
    for key in self.packet_processor.bfc_telemetry.keys():
      if key == "info_error_in_queue":
        table[0] += ["True" if self.packet_processor.bfc_telemetry[key] == 1 else "False"]  
      elif key == "rssi" or key == "gps_satellites":
        table[0] += [int(self.packet_processor.bfc_telemetry[key])]
      elif key == "gps_altitude" or key == "baro_altitude" or key == "snr":
        table[0] += [round(self.packet_processor.bfc_telemetry[key], 2)]
      else:
        table[0] += [round(self.packet_processor.bfc_telemetry[key], 6)]
    
    if self.packet_processor.bfc_packet_received_time == 0:
      table[0] += ["N/A"]
    else:
      table[0] += [round(time.time() - self.packet_processor.bfc_packet_received_time, 1)]
    
    table[1].append("Payload")
    if self.packet_processor.pfc_packet_received_time == 0:
      table[1] += ["N/A"]
    else:
      table[1] += [time.strftime("%H:%M:%S", time.localtime(self.packet_processor.pfc_packet_received_time))]
    for key in self.packet_processor.pfc_telemetry.keys():
      if key == "info_error_in_queue":
        table[1] += ["True" if self.packet_processor.pfc_telemetry[key] == 1 else "False"]        
      elif key == "rssi" or key == "gps_satellites":
        table[1] += [int(self.packet_processor.pfc_telemetry[key])]
      elif key == "gps_altitude" or key == "baro_altitude" or key == "snr":
        table[1] += [round(self.packet_processor.pfc_telemetry[key], 2)]
      else:
        table[1] += [round(self.packet_processor.pfc_telemetry[key], 6)]
    
    if self.packet_processor.pfc_packet_received_time == 0:
      table[1] += ["N/A"]
    else:
      table[1] += [round(time.time() - self.packet_processor.pfc_packet_received_time, 1)]
        
    print("Essential Telemetry")
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="center", disable_numparse=True))
    print("\033[K")  # Clear the line
    
    # Calculations
    headers = ["Vehicle", "GPS ↑↓ Speed (m/s)", "Baro ↑↓ Speed (m/s)", "GPS ←→ Speed (m/s)", "GPS Speed (m/s)"]
    
    table = [[], []]
    table[0].append("Balloon")
    for key in self.packet_processor.bfc_calculations.keys():
      if "speed" in key:
        table[0].append(round(self.packet_processor.bfc_calculations[key], 2))
    
    table[1].append("Payload")
    for key in self.packet_processor.pfc_calculations.keys():
      if "speed" in key:
        table[1].append(round(self.packet_processor.pfc_calculations[key], 2))
    print("Calculations")
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="center", disable_numparse=True))
    print("\033[K")  # Clear the line

    self.last_print_time = time.time()
