import os
from time import sleep

from config import *
from modules.connection_manager import ConnectionManager
from modules.logging import Logger
from modules.map import Map
from modules.processor import PacketProcessor
from modules.rotator import Rotator
from modules.router import Router
from modules.sondehub import SondeHubUploader
from modules.thread_manager import ThreadManager

def main():
  print("RTU High Power Rocketry Team - Ground Station Data Processing Software")
  print()
  
  # Create objects
  try:
    logger = Logger()
    connection_manager = ConnectionManager(logger)
  except OSError as e:
    print(f"The following error occurred while creating the connection manager: {e}")
    print("Most likely, one of the ports are already in use. Check if no other Python programs are running and try again.")
    os.system('pause')
    print("Exiting...")
    exit(1)
  
  rotator = Rotator()
  sondehub_uploader = SondeHubUploader()
  map = Map(map_server_port=MAP_SERVER_PORT)
  processor = PacketProcessor(connection_manager, rotator)
  router = Router(processor, connection_manager, rotator, map, sondehub_uploader)
  thread_manager = ThreadManager(connection_manager, processor, router, sondehub_uploader, map, rotator)
  
  print("Setup successful!")
  print()
  
  # Start threads
  print("Starting threads...", end="")
  # Receive threads
  thread_manager.start_receive_from_transceiver_thread()
  thread_manager.start_receive_from_yamcs_thread()
  # Send threads
  thread_manager.start_send_to_transceiver_thread()
  thread_manager.start_send_heartbeat_to_transceiver_thread()
  thread_manager.start_send_to_yamcs_thread()
  thread_manager.start_send_processed_data_thread()
  thread_manager.start_send_data_to_map_thread()
  # Processing thread
  thread_manager.start_packet_processing_thread()
  # SondeHub thread
  # thread_manager.start_sondehub_uploader_thread()
  # Rotator threads
  thread_manager.start_rotator_command_to_transceiver_thread()
  thread_manager.start_rotator_data_update_thread()
  # Map thread
  thread_manager.start_map_server_thread()
  thread_manager.start_map_update_thread()
  # Control rotator thread
  thread_manager.start_control_rotator_thread()
  
  print("All threads started!")
  print()
  print("TO STOP THE PROGRAM, PRESS CTRL+C OR CLOSE THE CONSOLE!")
  print()

  while True:
    try:
      sleep(1)
    except KeyboardInterrupt:
      print("Keyboard interrupt detected. Stopping threads... Please wait.")
      thread_manager.stop_event.set()
      for thread in thread_manager.active_threads:
        if thread.name == "Map Server":
          pass
        else:
          while thread.is_alive():
            # Give the thread a chance to stop.
            thread.join(timeout=0.1)
        print(f"Thread {thread.name} stopped.")
      print("All threads stopped. Exiting...")
      os.system('pause')
      os._exit(0)
      
if __name__ == "__main__":
  main()