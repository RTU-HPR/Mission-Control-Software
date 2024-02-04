from time import sleep
import queue

from modules.connection_manager import ConnectionManager
from modules.map import Map
from modules.processor import PacketProcessor
from modules.rotator import Rotator
from modules.sondehub import SondeHubUploader

from config import PACKETID_TO_TYPE, TELECOMMAND_APID
from modules.ccsds import convert_message_to_ccsds

class Router:
  def __init__(self, processor: PacketProcessor, connection: ConnectionManager, rotator: Rotator, map: Map, sondehub: SondeHubUploader) -> None:
    self.processor = processor
    self.connection = connection
    self.rotator = rotator
    self.map = map
    self.sondehub = sondehub
  
  def send_data_to_map(self):
    def add_coordinates(coordinates, latitude, longitude):
      if latitude != 0 and longitude != 0:
        if [latitude, longitude] not in coordinates:
          coordinates.append([latitude, longitude])
          self.map.map_update_required = True

    add_coordinates(self.map.ballon_coordinates, self.processor.bfc_telemetry["gps_latitude"], self.processor.bfc_telemetry["gps_longitude"])
    add_coordinates(self.map.payload_coordinates, self.processor.pfc_telemetry["gps_latitude"], self.processor.pfc_telemetry["gps_longitude"])
    add_coordinates(self.map.rotator_coordinates, self.rotator.rotator_position["latitude"], self.rotator.rotator_position["longitude"])

    sleep(0.1)
  
  def send_processed_data(self):
    try:
      packet = self.processor.processed_packets.get(timeout=1)
      if packet[1] == "primary" or packet[1] == "secondary":
        self.connection.sendable_to_transceiver_messages.put(packet)
      elif packet[1] == "yamcs":
        self.connection.sendable_to_yamcs_messages.put(packet)
      self.processor.processed_packets.task_done()
    except queue.Empty:
      pass
    except Exception as e:
      print(f"An error occurred while sending processed data: {e}")
    
  def send_rotator_command_to_transceiver(self):
    if self.rotator.rotator_last_command != self.rotator.rotator_command:
      apid = TELECOMMAND_APID["rotator"]
      
      # As this is a command, we need to add packet id
      data_str = str([key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_angles_request"][0])      
      data_str += "," + self.rotator.rotator_command      
      
      ccsds = convert_message_to_ccsds(apid, self.rotator.rotator_command_index, data_str, True) 
      if ccsds is None:
        return
      
      self.processor.processed_packets.put((False, "primary", ccsds))
      self.rotator.rotator_command_index += 1
      self.rotator.rotator_last_command = self.rotator.rotator_command
      
      print(f"Rotator command sent: Azimuth: {float(self.rotator.rotator_command.split(',')[0])} | Elevation: {float(self.rotator.rotator_command.split(',')[1])}")
      
    sleep(0.1)
    
  def update_rotator_data(self):
    # Update the rotator position
    self.rotator.set_auto_rotator_position(self.processor.rotator_telemetry["latitude"],
                                            self.processor.rotator_telemetry["longitude"],
                                            self.processor.rotator_telemetry["altitude"])

    # If the rotator is in auto tracking mode, update the rotator target position
    if self.rotator.rotator_target == "pfc":
      self.rotator.set_auto_target_position(self.processor.pfc_telemetry["gps_latitude"],
                                              self.processor.pfc_telemetry["gps_longitude"],
                                              self.processor.pfc_telemetry["gps_altitude"])
        
    elif self.rotator.rotator_target == "bfc":
      self.rotator.set_auto_target_position(self.processor.bfc_telemetry["gps_latitude"],
                                              self.processor.bfc_telemetry["gps_longitude"],
                                              self.processor.bfc_telemetry["gps_altitude"])
    sleep(0.1)
  
  def send_data_to_sondehub(self):
    self.sondehub.upload_balloon_data(self.processor.last_bfc_telemetry_epoch_seconds,
                                      self.processor.bfc_telemetry["gps_latitude"],
                                      self.processor.bfc_telemetry["gps_longitude"],
                                      self.processor.bfc_telemetry["gps_altitude"])
    
    self.sondehub.upload_payload_data(self.processor.last_pfc_telemetry_epoch_seconds,
                                      self.processor.pfc_telemetry["gps_latitude"],
                                      self.processor.pfc_telemetry["gps_longitude"],
                                      self.processor.pfc_telemetry["gps_altitude"])
    sleep(1)
                              