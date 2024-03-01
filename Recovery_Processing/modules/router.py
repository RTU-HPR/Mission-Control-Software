from time import sleep
import queue

from modules.connection_manager import ConnectionManager
from modules.map import Map
from modules.processor import PacketProcessor

class Router:
  def __init__(self, processor: PacketProcessor, connection: ConnectionManager, map: Map) -> None:
    self.processor = processor
    self.connection = connection
    self.map = map
  
  def send_data_to_map(self):
    def add_coordinates(coordinates, latitude, longitude):
      if latitude != 0 and longitude != 0:
        if [latitude, longitude] not in coordinates:
          coordinates.append([latitude, longitude])
          self.map.map_update_required = True

    add_coordinates(self.map.ballon_coordinates, self.processor.bfc_telemetry["gps_latitude"], self.processor.bfc_telemetry["gps_longitude"])
    add_coordinates(self.map.payload_coordinates, self.processor.pfc_telemetry["gps_latitude"], self.processor.pfc_telemetry["gps_longitude"])

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