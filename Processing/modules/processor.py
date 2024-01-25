import queue

from modules.connection_manager import ConnectionManager 
from modules.rotator import Rotator
from modules.calculations import *
from modules.ccsds import *
from config import *

class PacketProcessor:
  def __init__(self, 
         connection_manager: ConnectionManager,
         rotator: Rotator) -> None:
    # Objects
    self.connection_manager = connection_manager
    self.rotator = rotator
    
    # Telemetry
    self.pfc_telemetry = {value: 0.0 for type, value in TELEMETRY_MESSAGE_STRUCTURE["pfc"]}
    self.bfc_telemetry = {value: 0.0 for type, value in TELEMETRY_MESSAGE_STRUCTURE["bfc"]}
    self.rotator_telemetry = {value: 0.0 for type, value in TELEMETRY_MESSAGE_STRUCTURE["rotator"]}
    
    # Timing
    self.last_pfc_telemetry_epoch_seconds = 0
    self.last_bfc_telemetry_epoch_seconds = 0
    self.last_pfc_telemetry_epoch_subseconds = 0
    self.last_bfc_telemetry_epoch_subseconds = 0
    
    # Calculations
    self.pfc_calculations = dict.fromkeys(TELEMETRY_MESSAGE_STRUCTURE["pfc"], 0.0)
    self.bfc_calculations = dict.fromkeys(TELEMETRY_MESSAGE_STRUCTURE["bfc"], 0.0)
    self.rotator_calculations = dict.fromkeys(TELEMETRY_MESSAGE_STRUCTURE["rotator"], 0.0)
    self.pfc_calculations_index = 0
    self.bfc_calculations_index = 0
    self.rotator_calculations_index = 0
    
    # Queues
    self.processed_packets = queue.Queue()
  
  def process_packet(self) -> None:
    # Get a packet from connection manager
    packet = self.connection_manager.received_messages.get()
    
    try:
      # Parse the packet      
      parsed = parse_ccsds_packet(packet[2])
      if parsed is None:
        raise Exception("Invalid ccsds packet")
      
      apid, epoch_seconds, epoch_subseconds, packet_data = parsed
      
      # If the packet is a telecommand
      if apid in TELECOMMAND_APID.values():
        # Get packet id, which is the first 16 bits of the packet data
        packet_id = int(packet_data[:16], 2)
        packet_data = packet_data[16:]
        
        # If the packet is meant for the rotator, process it, else put it in the processed packets queue
        if not self.__process_rotator_command(packet_id, packet_data):
          self.processed_packets.put((True, "transceiver", packet[2]))
          # Complete the task
          self.connection_manager.received_messages.task_done()
          return

      # Update telemetry from essential packets
      elif apid in [key for key, value in APID_TO_TYPE.items() if value == "pfc_essential"]:
        self.__update_pfc_telemetry(packet_data, epoch_seconds, epoch_subseconds)
      elif apid in [key for key, value in APID_TO_TYPE.items() if value == "bfc_essential"]:
        self.__update_bfc_telemetry(packet_data, epoch_seconds, epoch_subseconds)
      elif apid in [key for key, value in APID_TO_TYPE.items() if value == "rotator_position"]:
        self.__update_rotator_telemetry(packet_data)
        
      self.processed_packets.put((False, "yamcs", packet[2]))
            
      # Complete the task
      self.connection_manager.received_messages.task_done()
                    
    except Exception as e:
      self.connection_manager.received_messages.task_done()
      print(f"An error occurred while processing packet: {e}")
  
  def __process_rotator_command(self, packet_id: int, packet_data) -> bool:
    try:
      # Set target PFC
      if packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_set_target_request"][0]:
        target = binary_to_int(packet_data[:8])
        if target == 0:
          self.rotator.set_target("pfc")
        elif target == 1:
          self.rotator.set_target("bfc")
        return True
            
      # Set rotator to auto tracking mode
      elif packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_auto_tracking_request"][0]:
        self.rotator.set_control_mode("auto")
        return True
        
      # Set rotator to auto rotator position mode
      elif packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_auto_rotator_position_request"][0]:
        self.rotator.set_rotator_position_mode("auto")
        return True
      
      # Set rotator to manual rotator position mode
      elif packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_manual_rotator_position_request"][0]:
        latitude = binary_to_float(packet_data[:32])
        longitude = binary_to_float(packet_data[32:64])
        altitude = binary_to_float(packet_data[64:96])
        self.rotator.set_manual_rotator_position(latitude, longitude, altitude)
        return True
      
      # Set rotator to manual angles mode
      elif packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_manual_angles_request"][0]:
        azimuth = binary_to_float(packet_data[:32])
        elevation = binary_to_float(packet_data[32:64])
        self.rotator.set_manual_angles(azimuth, elevation)
        return True
        
      # Set rotator to manual target coordinates mode
      elif packet_id == [key for key, value in PACKETID_TO_TYPE.items() if value == "rotator_manual_target_coordinates_request"][0]: 
        latitude = binary_to_float(packet_data[:32])
        longitude = binary_to_float(packet_data[32:64])
        altitude = binary_to_float(packet_data[64:96])
        self.rotator.set_manual_target_position(latitude, longitude, altitude)
        return True

      return False
      
    except Exception as e:
      print(f"Error processing rotator command: {e}")
      return False  
  
  def __update_pfc_telemetry(self, packet_data, epoch_seconds, epoch_subseconds) -> None:
    try:
      new_telemetry = {}
      
      # Convert packet data from binary to usable data values
      start = 0
      for type, value in TELEMETRY_MESSAGE_STRUCTURE["pfc"]:
        if type == "float":
          end = start + 32
          new_telemetry[value] = binary_to_float(packet_data[start:end])
          start = end
        elif type == "int":
          end = start + 32
          new_telemetry[value] = binary_to_int(packet_data[start:end])
          start = end
        else:
          raise Exception(f"Invalid data type: {type} and {value}")
        
      # PFC essential telemetry
      old_pfc_telemetry_epoch_seconds = self.last_pfc_telemetry_epoch_seconds
      old_pfc_telemetry_epoch_subseconds = self.last_pfc_telemetry_epoch_subseconds
      self.last_pfc_telemetry_epoch_seconds = epoch_seconds
      self.last_pfc_telemetry_epoch_subseconds = epoch_subseconds

      # Calculate time delta from seconds and subseconds
      time_delta = (self.last_pfc_telemetry_epoch_seconds - old_pfc_telemetry_epoch_seconds) + (self.last_pfc_telemetry_epoch_subseconds - old_pfc_telemetry_epoch_subseconds) / 65536

      # Calculate extra telemetry if position is valid
      if self.pfc_telemetry["gps_latitude"] != 0 and self.pfc_telemetry["gps_latitude"] != 0:
        self.pfc_calculations = calculate_flight_computer_extra_telemetry(self.pfc_telemetry, new_telemetry, self.rotator_telemetry, time_delta, CALCULATION_MESSAGE_STRUCTURE["pfc"])
        
      # Create a ccsds packet from the calculations
      apid = [key for key, value in APID_TO_TYPE.items() if value == "pfc_calculations"][0]
      message = ",".join([str(x) for x in self.pfc_calculations.values()]) 
      ccsds = convert_message_to_ccsds(apid, self.pfc_calculations_index, message)
          
      if ccsds is None:
        raise Exception("Invalid ccsds packet created")
          
      self.processed_packets.put((False, "yamcs", ccsds))
      self.pfc_calculations_index += 1
      self.pfc_telemetry = new_telemetry
        
    except Exception as e:
      print(f"Error updating PFC telemetry: {e}")
      
  def __update_bfc_telemetry(self, packet_data, epoch_seconds, epoch_subseconds) -> None:
    try:
      new_telemetry = {}
      
      # Convert packet data from binary to usable data types
      start = 0
      for type, value in TELEMETRY_MESSAGE_STRUCTURE["bfc"]:
        if type == "float":
          end = start + 32
          new_telemetry[value] = binary_to_float(packet_data[start:end])
          start = end
        elif type == "int":
          end = start + 32
          new_telemetry[value] = binary_to_int(packet_data[start:end])
          start = end
        else:
          raise Exception(f"Invalid data type: {type} and {value}")
        
      # BFC essential telemetry
      old_bfc_telemetry_epoch_seconds = self.last_bfc_telemetry_epoch_seconds
      old_bfc_telemetry_epoch_subseconds = self.last_bfc_telemetry_epoch_subseconds
      self.last_bfc_telemetry_epoch_seconds = epoch_seconds
      self.last_bfc_telemetry_epoch_subseconds = epoch_subseconds
      
      # Calculate time delta from seconds and subseconds
      time_delta = (self.last_bfc_telemetry_epoch_seconds - old_bfc_telemetry_epoch_seconds) + (self.last_bfc_telemetry_epoch_subseconds - old_bfc_telemetry_epoch_subseconds) / 65536

      # Calculate extra telemetry if position is valid
      if self.bfc_telemetry["gps_latitude"] != 0 and self.bfc_telemetry["gps_latitude"] != 0:
        self.bfc_calculations = calculate_flight_computer_extra_telemetry(self.bfc_telemetry, new_telemetry, self.rotator_telemetry, time_delta, CALCULATION_MESSAGE_STRUCTURE["bfc"])
        
        # Create a ccsds packet from the calculations
        apid = [key for key, value in APID_TO_TYPE.items() if value == "bfc_calculations"][0]
        message = ",".join([str(x) for x in self.bfc_calculations.values()]) 
        ccsds = convert_message_to_ccsds(apid, self.bfc_calculations_index, message)
        
        if ccsds is None:
          raise Exception("Invalid ccsds packet created")
        
        self.processed_packets.put((False, "yamcs", ccsds))
        self.bfc_calculations_index += 1
        self.bfc_telemetry = new_telemetry
        
    except Exception as e:
      print(f"Error updating BFC telemetry: {e}")
      

  def __update_rotator_telemetry(self, packet_data) -> None:
    try:
      new_telemetry = {}
      
      # Convert packet data from binary to usable data types
      start = 0
      for type, value in TELEMETRY_MESSAGE_STRUCTURE["rotator"]:
        if type == "float":
          end = start + 32
          new_telemetry[value] = binary_to_float(packet_data[start:end])
          start = end
        elif type == "int":
          end = start + 32
          new_telemetry[value] = binary_to_int(packet_data[start:end])
          start = end
        else:
          raise Exception(f"Invalid data type: {type} and {value}")
        
      # Create a ccsds packet from the rotator position
      apid = [key for key, value in APID_TO_TYPE.items() if value == "rotator_position"][0]
      message = ",".join([str(x) for x in new_telemetry.values()])
      ccsds = convert_message_to_ccsds(apid, self.rotator_calculations_index, message)
      
      if ccsds is None:
        raise Exception("Invalid ccsds packet created")
      
      self.processed_packets.put((False, "yamcs", ccsds))
      self.rotator_calculations_index += 1        
      self.rotator_telemetry = new_telemetry
      
    except Exception as e:
      print(f"Error updating rotator telemetry: {e}")
    