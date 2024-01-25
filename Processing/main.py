from time import sleep

from config import *
from modules.processor import PacketProcessor
from modules.connection_manager import ConnectionManager
from modules.sondehub import SondeHubUploader
from modules.router import Router
from modules.map import Map
from modules.thread_manager import ThreadManager
from modules.rotator import Rotator

if __name__ == '__main__':
  print("RTU High Power Rocketry Team - Ground Station Data Processing Software")
  print()
  
  # Create objects
  try:
    connection_manager = ConnectionManager(YAMCS_TM_ADDRESS, YAMCS_TC_ADDRESS, TRANSCEIVER_TM_ADDRESS, TRANSCEIVER_TC_ADDRESS)
  except OSError as e:
    print(f"The following error occurred while creating the connection manager: {e}")
    print("Most likely the IP address is not valid. Please check the config.py file and try again.")
    exit(1)
  
  rotator = Rotator()
  map = Map(map_server_port=MAP_SERVER_PORT)
  sondehub_uploader = SondeHubUploader()
  
  processor = PacketProcessor(connection_manager, rotator)
  
  router = Router(processor, connection_manager, rotator, map, sondehub_uploader)
  thread_manager = ThreadManager(connection_manager, processor, router, sondehub_uploader, map, rotator)
  
  print("Setup successful!")
  print()
  
  # Start threads
  print("Starting threads...", end="")
  thread_manager.start_receive_from_transceiver_thread()
  thread_manager.start_receive_from_yamcs_thread()
  thread_manager.start_send_to_transceiver_thread()
  thread_manager.start_send_heartbeat_to_transceiver_thread()
  thread_manager.start_send_to_yamcs_thread()
  thread_manager.start_send_processed_data_thread()
  thread_manager.start_send_data_to_map_thread()
  thread_manager.start_rotator_command_to_transceiver_thread()
  thread_manager.start_rotator_data_update_thread()
  thread_manager.start_map_server_thread()
  thread_manager.start_map_update_thread()
  thread_manager.start_packet_processing_thread()
  thread_manager.start_control_rotator_thread()
  # thread_manager.start_sondehub_uploader_thread()
  
  print("All threads started!")
  print()
  print("Program is now running!")
  print()
  print("TO STOP THE PROGRAM, PLEASE PRESS CTRL+C")
  print()

  while True:
    try:
      sleep(1)
    except KeyboardInterrupt:
      print("Keyboard interrupt detected. Stopping threads... Please wait.")
      thread_manager.stop_event.set()
      for thread in thread_manager.active_threads:
        thread.join(timeout=0.1)
        print(f"Thread {thread.name} stopped.")
      print("All threads stopped. Exiting...")
      exit(0)