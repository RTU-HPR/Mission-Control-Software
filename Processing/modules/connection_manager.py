import socket
import queue
import time

from config import *
from modules.mcs_logging import Logger

class ConnectionManager:
  def __init__(self, logger: Logger, MQTTPacketTxCallback) -> None:    
    # Logging
    self.logger = logger
    
    # Queues
    self.sendable_to_transceiver_messages = queue.Queue()
    self.sendable_to_yamcs_messages = queue.Queue()
    self.received_messages = queue.Queue()
    
    self.sending_to_transceiver = False
    
    # UDP sockets (TM - Telemetry, TC - Telecommand)
    # YAMCS sockets
    self.yamcs_tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.yamcs_tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.yamcs_tc_socket.settimeout(1)
    self.yamcs_tc_socket.bind(YAMCS_TC_ADDRESS)

    # Transceiver sockets
    self.transceiver_tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.transceiver_tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.transceiver_tm_socket.settimeout(3)
    self.transceiver_tm_socket.bind(TRANSCEIVER_TM_ADDRESS)
    self.transceiver_socket_connected = False
    self.transceiver_wifi_rssi = 0
    
    self.secondary_transceiver_tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.secondary_transceiver_tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.secondary_transceiver_tm_socket.settimeout(3)
    self.secondary_transceiver_tm_socket.bind(SECONDARY_TRANSCEIVER_TM_ADDRESS)
    self.secondary_transceiver_socket_connected = False # By default, should be False, set to True for testing
    self.secondary_transceiver_wifi_rssi = 0
  
  def send_heartbeat_to_transceiver(self) -> None:
    # ~ Used as sacrificial character
    self.transceiver_tc_socket.sendto("UDP Heartbeat Primary~".encode(), TRANSCEIVER_TC_ADDRESS)
    self.secondary_transceiver_tc_socket.sendto("UDP Heartbeat Secondary~".encode(), SECONDARY_TRANSCEIVER_TC_ADDRESS)
    time.sleep(1)

  def send_to_transceiver(self) -> None:    
    try:
      packet = self.sendable_to_transceiver_messages.get(timeout=1)
    except queue.Empty:
      return
    
    # If there is no WiFi connection, put the packet back in the queue
    if packet[1] == "primary" and self.transceiver_socket_connected == False:
      self.sendable_to_transceiver_messages.put(packet)
      return
    elif packet[1] == "secondary" and self.secondary_transceiver_socket_connected == False:
      self.sendable_to_transceiver_messages.put(packet)
      return
    
    self.logger.log_telecommand_data(packet[2])
    
    self.sending_to_transceiver = True
    try:
      # Check if we should wait until the next cycle time to send the packet
      if packet[0] == True:
        # Wait until the next cycle time to send the packet
        # Cycle starts when epoch time is divisible by CYCLE_TIME
        while not (int(time.mktime(time.localtime())) % CYCLE_TIME == 0):
          time.sleep(0.1)
        # Send the packet 1 seconds after the cycle time start
        time.sleep(1)
      
      if packet[1] == "primary":
        self.transceiver_tc_socket.sendto(packet[2], TRANSCEIVER_TC_ADDRESS)
      elif packet[1] == "secondary":
        self.secondary_transceiver_tc_socket.sendto(packet[2], SECONDARY_TRANSCEIVER_TC_ADDRESS)
        
      self.sending_to_transceiver = False
      self.sendable_to_transceiver_messages.task_done()
    except Exception as e:
      self.sendable_to_transceiver_messages.task_done()
      print(f"An error occurred while sending to transceiver: {e}")
  
  def receive_from_primary_transceiver(self) -> None:
    try:
      # Receive a message from the transceiver
      message, addr = self.transceiver_tm_socket.recvfrom(4096)
      
      # Try to decode the message to see if it is a heartbeat
      try:
        message = message.decode()
        if "Heartbeat" in message:
          self.transceiver_socket_connected = True
          self.transceiver_wifi_rssi = int(message.split(",")[1])
        else:
          raise Exception()
      # If the message is not a heartbeat, put it in the queue
      except:
        self.received_messages.put((False, "yamcs", message))
        MQTTPacketTxCallback(message)
    except socket.timeout:
      self.transceiver_socket_connected = False
    except Exception as e:
      print(f"An error occurred while receiving from primary transceiver: {e}")    
      
  def receive_from_secondary_transceiver(self) -> None:
    try:
      # Receive a message from the transceiver
      message, addr = self.secondary_transceiver_tm_socket.recvfrom(4096)
      
      # Try to decode the message to see if it is a heartbeat
      try:
        message = message.decode()
        if "Heartbeat" in message:
          self.secondary_transceiver_socket_connected = True
          self.secondary_transceiver_wifi_rssi = int(message.split(",")[1])
        else:
          raise Exception()
      # If the message is not a heartbeat, put it in the queue
      except:
        self.received_messages.put((False, "yamcs", message))
    except socket.timeout:
      self.secondary_transceiver_socket_connected = False
    except Exception as e:
      print(f"An error occurred while receiving from secondary transceiver: {e}")   

  def receive_sync(self, message) -> None:
    try:
      # Try to decode the message to see if it is a heartbeat
      try:
        message = message.decode()
        if "Heartbeat" in message:
          self.transceiver_socket_connected = True
          self.transceiver_wifi_rssi = int(message.split(",")[1])
        else:
          raise Exception()
      # If the message is not a heartbeat, put it in the queue
      except:
        self.received_messages.put((False, "yamcs", message))
    except socket.timeout:
      self.transceiver_socket_connected = False
    except Exception as e:
      print(f"An error occurred while receiving from primary transceiver: {e}") 
    
  def send_to_yamcs(self) -> None:
    try:
      packet = self.sendable_to_yamcs_messages.get(timeout=1)
    except:
      return
    try:
      self.yamcs_tm_socket.sendto(packet[2], YAMCS_TM_ADDRESS)
      self.logger.log_telemetry_data(packet[2])
      self.sendable_to_yamcs_messages.task_done()
    except Exception as e:
      self.sendable_to_yamcs_messages.task_done()
      print(f"An error occurred while sending to YAMCS: {e}")
      
  def receive_from_yamcs(self) -> None:
    try:
      packet, addr = self.yamcs_tc_socket.recvfrom(1024)
      self.received_messages.put((False, "transceiver", packet))
    except socket.timeout:
      pass
    except Exception as e:
      print(f"An error occurred while receiving from YAMCS: {e}")
  