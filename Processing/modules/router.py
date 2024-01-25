from time import sleep

from config import TELECOMMAND_APID, PACKETID_TO_TYPE
from modules.ccsds import convert_message_to_ccsds
from modules.processor import PacketProcessor
from modules.connection_manager import ConnectionManager
from modules.rotator import Rotator
from modules.map import Map
from modules.sondehub import SondeHubUploader
class Router:
  def __init__(self, processor: PacketProcessor, connection: ConnectionManager, rotator: Rotator, map: Map, sondehub: SondeHubUploader) -> None:
    self.processor = processor
    self.connection = connection
    self.rotator = rotator
    self.map = map
    self.sondehub = sondehub
  
  def send_data_to_map(self):
    # If the balloon has a valid position and the coordinates are not already in the list, add them
    if [self.processor.bfc_telemetry["gps_latitude"], self.processor.bfc_telemetry["gps_longitude"]] not in self.map.ballon_coordinates:
      if self.processor.bfc_telemetry["gps_latitude"] != 0 and self.processor.bfc_telemetry["gps_longitude"] != 0:
        self.map.ballon_coordinates.append([self.processor.bfc_telemetry["gps_latitude"], self.processor.bfc_telemetry["gps_longitude"]])
        self.map.map_update_required = True    

    # If the payload has a valid position and the coordinates are not already in the list, add them
    if [self.processor.pfc_telemetry["gps_latitude"], self.processor.pfc_telemetry["gps_longitude"]] not in self.map.payload_coordinates:
      if self.processor.pfc_telemetry["gps_latitude"] != 0 and self.processor.pfc_telemetry["gps_longitude"] != 0:
        self.map.payload_coordinates.append([self.processor.pfc_telemetry["gps_latitude"], self.processor.pfc_telemetry["gps_longitude"]])
        self.map.map_update_required = True    
        
    # If the rotator has a valid position and the coordinates are not the same as the last ones in the list, change them
    if [self.rotator.rotator_position["latitude"], self.rotator.rotator_position["longitude"]] not in self.map.rotator_coordinates:
      if self.rotator.rotator_position["latitude"] != 0 and self.rotator.rotator_position["longitude"] != 0:
        self.map.rotator_coordinates = [[self.rotator.rotator_position["latitude"], self.rotator.rotator_position["longitude"]]]
        self.map.map_update_required = True  
        
    sleep(0.1)  
  
  def send_processed_data(self):
    try:
      packet = self.processor.processed_packets.get()
      if packet[1] == "transceiver":
        self.connection.sendable_to_transceiver_messages.put(packet)
      elif packet[1] == "yamcs":
        self.connection.sendable_to_yamcs_messages.put(packet)
      self.processor.processed_packets.task_done()
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
      
      self.processor.processed_packets.put((False, "transceiver", ccsds))
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
  
    
  def send_data_to_logging(self):
    pass
  
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
                              
  
  def send_data_to_recovery_server(self):
    pass