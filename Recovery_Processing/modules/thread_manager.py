from threading import Thread, Event

from modules.connection_manager import ConnectionManager
from modules.processor import PacketProcessor
from modules.router import Router
from modules.map import Map
from modules.info_tables import InfoTables

class ThreadManager:
  def __init__(self, connection_manager: ConnectionManager, packet_processor: PacketProcessor, router: Router, map: Map, info_tables: InfoTables) -> None:
    self.connection_manager = connection_manager
    self.packet_processor = packet_processor
    self.router = router
    self.map = map
    self.info_tables = info_tables
    
    self.active_threads = []
    self.stop_event = Event()
    
  # THREAD STARTERS
  def start_serial_connection_handler_thread(self):
    def serial_connection_handler_thread():
      while not self.stop_event.is_set():
        self.connection_manager.handle_serial_communication()
      
    thread = Thread(target=serial_connection_handler_thread, name="Serial Receiver")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)
    
  def start_serial_connection_checker_thread(self):
    def serial_connection_checker_thread():
      while not self.stop_event.is_set():
        self.connection_manager.check_serial_connection()
      
    thread = Thread(target=serial_connection_checker_thread, name="Serial Connection Checker")
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
    
  def start_info_tables_thread(self):
    def info_tables_thread():
      while not self.stop_event.is_set():
        self.info_tables.print_info_tables()
        
    thread = Thread(target=info_tables_thread, name="Info Tables")
    thread.daemon = True
    thread.start()
    self.active_threads.append(thread)
