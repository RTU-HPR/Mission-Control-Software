from sondehub.amateur import Uploader
from datetime import datetime

from config import *

class SondeHubUploader:
  # Refrence: https://github.com/projecthorus/pysondehub/wiki/SondeHub-Amateur-Uploader-Class-Usage
  def __init__(self) -> None:
    self.uploader = Uploader("RTU HPR Team", developer_mode=DEVELOPER_MODE)
    
    self.last_balloon_data = {"epoch_time": 0, "latitude": 0, "longitude": 0, "altitude": 0}
    self.last_payload_data = {"epoch_time": 0, "latitude": 0, "longitude": 0, "altitude": 0}
    
  def upload_balloon_data(self, epoch_time, latitude, longitude, altitude) -> None:
    # Check if the balloon data has changed
    if self.last_balloon_data["epoch_time"] == epoch_time and self.last_balloon_data["latitude"] == latitude and self.last_balloon_data["longitude"] == longitude and self.last_balloon_data["altitude"] == altitude:
      return
    
    # Update last data
    self.last_balloon_data["epoch_time"] = epoch_time
    self.last_balloon_data["latitude"] = latitude
    self.last_balloon_data["longitude"] = longitude
    self.last_balloon_data["altitude"] = altitude
    
    # Upload data to SondeHub
    self.uploader.add_telemetry(
      BALLOON_CALLSIGN, # Your payload callsign
      datetime.fromtimestamp(epoch_time).isoformat(), # Convert time from epoch to ISO 8601 format
      latitude, # Latitude
      longitude, # Longitude
      altitude # Altitude
    )
    print("Balloon data uploaded to SondeHub")
    
  def upload_payload_data(self, epoch_time, latitude, longitude, altitude) -> None:
    # Check if the payload data has changed
    if self.last_payload_data["epoch_time"] == epoch_time and self.last_payload_data["latitude"] == latitude and self.last_payload_data["longitude"] == longitude and self.last_payload_data["altitude"] == altitude:
      return
    
    # Update last data
    self.last_payload_data["epoch_time"] = epoch_time
    self.last_payload_data["latitude"] = latitude
    self.last_payload_data["longitude"] = longitude
    self.last_payload_data["altitude"] = altitude
    
    # Upload data to SondeHub
    self.uploader.add_telemetry(
      PAYLOAD_CALLSIGN, # Your balloon callsign
      datetime.fromtimestamp(epoch_time).isoformat(), # Convert time from epoch to ISO 8601 format
      latitude, # Latitude
      longitude, # Longitude
      altitude # Altitude
    )
    print("Payload data uploaded to SondeHub")
    
  def close_uploader(self) -> None:
    self.uploader.close()