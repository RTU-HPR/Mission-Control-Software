from binascii import hexlify
import socket
import queue
import time
import serial

from config import *
from modules.logging import Logger

class ConnectionManager:
  def __init__(self, logger: Logger) -> None:    
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
    
    # Open the serial port
    self.ser = serial.Serial(None, 115200, timeout=0.2)
    self.ser.port = SERIAL_PORT
    if self.ser.is_open:
      self.ser.close()
    self.ser.open()

  def handle_serial_communication(self):    
    if not self.sendable_to_transceiver_messages.empty():
      if (int(time.mktime(time.localtime())) % CYCLE_TIME == 0):
        packet = self.sendable_to_transceiver_messages.get(timeout=1)
        if packet is not None:
          self.ser.write(packet[2].encode())
        self.sendable_to_transceiver_messages.task_done()
    
    # Read data from the serial port
    # print(f"Bytes in waiting: {self.ser.in_waiting}")
    if self.ser.in_waiting > 0:
      read_data = self.ser.read(self.ser.in_waiting)
      # If the message is not a heartbeat, put it in the queue
      # print(f"Received from transceiver: {read_data}")
      self.received_messages.put((False, "yamcs", read_data))
    
  def send_to_yamcs(self) -> None:
    try:
      packet = self.sendable_to_yamcs_messages.get(timeout=1)
    except:
      return
    try:
      print(f"Sending to YAMCS: {packet[2]}")
      self.yamcs_tm_socket.sendto(packet[2], YAMCS_TM_ADDRESS)
      self.logger.log_telemetry_data(packet[2])
      self.sendable_to_yamcs_messages.task_done()
    except Exception as e:
      self.sendable_to_yamcs_messages.task_done()
      print(f"An error occurred while sending to YAMCS: {e}")
      
  def receive_from_yamcs(self) -> None:
    try:
      packet, addr = self.yamcs_tc_socket.recvfrom(1024)
      print(f"Received from YAMCS: {packet}")
      self.received_messages.put((False, "transceiver", packet))
    except socket.timeout:
      pass
    except Exception as e:
      print(f"An error occurred while receiving from YAMCS: {e}")
  