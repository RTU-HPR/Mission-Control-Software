from threading import Thread, Event

from modules.connection_manager import ConnectionManager
from modules.processor import PacketProcessor
from modules.router import Router
from modules.sondehub import SondeHubUploader
from modules.map import Map
from modules.rotator import Rotator
from modules.info_tables import InfoTables

class ThreadManager:
  def __init__(self, connection_manager: ConnectionManager, packet_processor: PacketProcessor, router: Router, sondehub_uploader: SondeHubUploader, map: Map, rotator: Rotator, info_tables: InfoTables, user_interface: UserInterface) -> None:
    self.connection_manager = connection_manager
    self.packet_processor = packet_processor
    self.router = router
    self.sondehub = sondehub_uploader
    self.map = map
    self.rotator = rotator
    self.info_tables = info_tables
    self.user_interface = user_interface

    self.active_threads = []
    self.stop_event = Event()

  # THREAD STARTERS
  def start_receive_from_primary_transceiver_thread(self):
    def receive_from_primary_transceiver_thread():
      while not self.stop_event.is_set():
        self.connection_manager.receive_from_primary_transceiver()

    thread = Thread(target=receive_from_primary_transceiver_thread, name="Primary Transceiver Receiver")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_receive_from_secondary_transceiver_thread(self):
    def receive_from_secondary_transceiver_thread():
      while not self.stop_event.is_set():
        self.connection_manager.receive_from_secondary_transceiver()

    thread = Thread(target=receive_from_secondary_transceiver_thread, name="Secondary Transceiver Receiver")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_receive_from_yamcs_thread(self):
    def receive_from_yamcs_thread():
      while not self.stop_event.is_set():
        self.connection_manager.receive_from_yamcs()

    thread = Thread(target=receive_from_yamcs_thread, name="YAMCS Receiver")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_send_to_transceiver_thread(self):
    def send_to_transceiver_thread():
      while not self.stop_event.is_set():
        self.connection_manager.send_to_transceiver()

    thread = Thread(target=send_to_transceiver_thread, name="Transceiver Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_send_to_yamcs_thread(self):
    def send_to_yamcs_thread():
      while not self.stop_event.is_set():
        self.connection_manager.send_to_yamcs()

    thread = Thread(target=send_to_yamcs_thread, name="YAMCS Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_packet_processing_thread(self):
    def packet_processing_thread():
      while not self.stop_event.is_set():
        self.packet_processor.process_packet()

    thread = Thread(target=packet_processing_thread, name="Packet Processor")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_send_processed_data_thread(self):
    def send_processed_data_thread():
      while not self.stop_event.is_set():
        self.router.send_processed_data()

    thread = Thread(target=send_processed_data_thread, name="Processed Data Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_map_server_thread(self):
    def map_server_thread():
      while not self.stop_event.is_set():
        self.map.run_server()

    thread = Thread(target=map_server_thread, name="Map Server")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_map_update_thread(self):
    def map_update_thread():
      while not self.stop_event.is_set():
        self.map.update_map()

    thread = Thread(target=map_update_thread, name="Map Updater")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_send_data_to_map_thread(self):
    def send_data_to_map_thread():
      while not self.stop_event.is_set():
        self.router.send_data_to_map()

    thread = Thread(target=send_data_to_map_thread, name="Map Data Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_rotator_command_to_transceiver_thread(self):
    def rotator_command_to_transceiver_thread():
      while not self.stop_event.is_set():
        self.router.send_rotator_command_to_transceiver()

    thread = Thread(target=rotator_command_to_transceiver_thread, name="Rotator Command Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_rotator_data_update_thread(self):
    def rotator_data_update_thread():
      while not self.stop_event.is_set():
        self.router.update_rotator_data()

    thread = Thread(target=rotator_data_update_thread, name="Rotator Data Updater")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_send_heartbeat_to_transceiver_thread(self):
    def send_heartbeat_to_transceiver_thread():
      while not self.stop_event.is_set():
        self.connection_manager.send_heartbeat_to_transceiver()

    thread = Thread(target=send_heartbeat_to_transceiver_thread, name="Heartbeat Sender")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_control_rotator_thread(self):
    def control_rotator_thread():
      while not self.stop_event.is_set():
        self.rotator.control_rotator()

    thread = Thread(target=control_rotator_thread, name="Rotator Controller")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_sondehub_uploader_thread(self):
    def sondehub_uploader_thread():
      while not self.stop_event.is_set():
        self.router.send_data_to_sondehub()
      self.sondehub.close_uploader()

    thread = Thread(target=sondehub_uploader_thread, name="SondeHub Uploader")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_info_tables_thread(self):
    def info_tables_thread():
      while not self.stop_event.is_set():
        self.info_tables.print_info_tables()

    thread = Thread(target=info_tables_thread, name="Info Tables")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)

  def start_user_interface_thread(self):
    def user_interface_thread():
      while not self.stop_event.is_set():
        self.user_interface.create_gui()

    thread = Thread(target=info_tables_thread, name="User Interface")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)
