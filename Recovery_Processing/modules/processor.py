import queue

from config import *
from modules.calculations import *
from modules.ccsds import *
from modules.connection_manager import ConnectionManager 

class PacketProcessor:
  def __init__(self, 
         connection_manager: ConnectionManager) -> None:
    # Objects
    self.connection_manager = connection_manager
    
    # Telemetry
    self.pfc_telemetry = {value: 0.0 for type, value in TELEMETRY_MESSAGE_STRUCTURE["pfc"]}
    self.bfc_telemetry = {value: 0.0 for type, value in TELEMETRY_MESSAGE_STRUCTURE["bfc"]}
    
    # Timing
    self.last_pfc_telemetry_epoch_seconds = 0
    self.last_bfc_telemetry_epoch_seconds = 0
    self.last_pfc_telemetry_epoch_subseconds = 0
    self.last_bfc_telemetry_epoch_subseconds = 0
    
    self.pfc_packet_received_time = 0
    self.bfc_packet_received_time = 0
    
    # Calculations
    self.pfc_calculations = dict.fromkeys(CALCULATION_MESSAGE_STRUCTURE["pfc"], 0.0)
    self.bfc_calculations = dict.fromkeys(CALCULATION_MESSAGE_STRUCTURE["bfc"], 0.0)
    self.pfc_calculations_index = 0
    self.bfc_calculations_index = 0
    
    # Queues
    self.processed_packets = queue.Queue()
  
  def process_packet(self) -> None:
    try:
      packet = self.connection_manager.received_messages.get(timeout=1)
    except queue.Empty:
      return
    
    try:
      parsed = parse_ccsds_packet(packet[2])
      if parsed is None:
        raise Exception("Invalid ccsds packet")
      
      apid, epoch_seconds, epoch_subseconds, packet_data = parsed
      # If the packet is a telecommand
      if apid in TELECOMMAND_APID.values():
        # Get packet id, which is the first 16 bits of the packet data
        packet_id = int(packet_data[:16], 2)
        packet_data = packet_data[16:]
        
        if apid == TELECOMMAND_APID["pfc"]:
          self.processed_packets.put((True, "primary", packet[2]))
        elif apid == TELECOMMAND_APID["bfc"]:
          self.processed_packets.put((True, "secondary", packet[2]))

          self.connection_manager.received_messages.task_done()
          return

      # Update telemetry from essential packets
      elif apid in [key for key, value in APID_TO_TYPE.items() if value == "pfc_essential"]:
        self.pfc_packet_received_time = time.time()
        self.__update_pfc_telemetry(packet_data, epoch_seconds, epoch_subseconds)
      elif apid in [key for key, value in APID_TO_TYPE.items() if value == "bfc_essential"]:
        self.bfc_packet_received_time = time.time()
        self.__update_bfc_telemetry(packet_data, epoch_seconds, epoch_subseconds)
        
      self.processed_packets.put((False, "yamcs", packet[2]))
            
      # Complete the task
      self.connection_manager.received_messages.task_done()
                    
    except Exception as e:
      self.connection_manager.received_messages.task_done()
      print(f"An error occurred while processing packet: {e}")
  
  def __convert_binary_to_telemetry(self, packet_data, telemetry_type: str):
    """
    Converts binary packet data to telemetry data.
    """
    new_telemetry = {}
    start = 0
    for data_type, data_value in TELEMETRY_MESSAGE_STRUCTURE[telemetry_type]:
        if data_type == "float":
            end = start + 32
            new_telemetry[data_value] = binary_to_float(packet_data[start:end])
            start = end
        elif data_type == "int":
            end = start + 32
            new_telemetry[data_value] = binary_to_int(packet_data[start:end])
            start = end
        else:
            raise Exception(f"Invalid data type: {data_type} and {data_value}")
    return new_telemetry
  
  def __update_pfc_telemetry(self, packet_data, epoch_seconds, epoch_subseconds) -> None:
    """
    Updates the PFC telemetry data.
    """
    try:
        new_telemetry = self.__convert_binary_to_telemetry(packet_data, "pfc")
        
        # PFC essential telemetry
        old_pfc_telemetry_epoch_seconds = self.last_pfc_telemetry_epoch_seconds
        old_pfc_telemetry_epoch_subseconds = self.last_pfc_telemetry_epoch_subseconds
        self.last_pfc_telemetry_epoch_seconds = epoch_seconds
        self.last_pfc_telemetry_epoch_subseconds = epoch_subseconds

        # Calculate time delta from seconds and subseconds
        time_delta = (self.last_pfc_telemetry_epoch_seconds - old_pfc_telemetry_epoch_seconds) + (self.last_pfc_telemetry_epoch_subseconds - old_pfc_telemetry_epoch_subseconds) / 65536

        # Calculate extra telemetry if position is valid
        if self.pfc_telemetry["gps_latitude"] != 0 and self.pfc_telemetry["gps_latitude"] != 0:
            self.pfc_calculations = calculate_flight_computer_extra_telemetry(self.pfc_telemetry, new_telemetry, time_delta, CALCULATION_MESSAGE_STRUCTURE["pfc"])
        
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
      new_telemetry = self.__convert_binary_to_telemetry(packet_data, "bfc")
        
      # BFC essential telemetry
      old_bfc_telemetry_epoch_seconds = self.last_bfc_telemetry_epoch_seconds
      old_bfc_telemetry_epoch_subseconds = self.last_bfc_telemetry_epoch_subseconds
      self.last_bfc_telemetry_epoch_seconds = epoch_seconds
      self.last_bfc_telemetry_epoch_subseconds = epoch_subseconds
      
      # Calculate time delta from seconds and subseconds
      time_delta = (self.last_bfc_telemetry_epoch_seconds - old_bfc_telemetry_epoch_seconds) + (self.last_bfc_telemetry_epoch_subseconds - old_bfc_telemetry_epoch_subseconds) / 65536

      # Calculate extra telemetry if position is valid
      if self.bfc_telemetry["gps_latitude"] != 0 and self.bfc_telemetry["gps_latitude"] != 0:
        self.bfc_calculations = calculate_flight_computer_extra_telemetry(self.bfc_telemetry, new_telemetry, time_delta, CALCULATION_MESSAGE_STRUCTURE["bfc"])
        
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