from time import sleep
from astropy.coordinates import EarthLocation
import numpy as np

class Rotator:
  def __init__(self):
    # Control
    self.rotator_target = "pfc"
    self.rotator_control_mode = "auto"
    self.rotator_position_mode = "auto"
    
    # Position
    self.rotator_position = {"latitude": 0.0, "longitude": 0.0, "altitude": 0.0}
    self.target_position = {"latitude": 0.0, "longitude": 0.0, "altitude": 0.0}
    
    # Angles
    self.rotator_angles = {"azimuth": 0.0, "elevation": 0.0}
    self.new_angles_required = False
    
    # Commands
    self.rotator_command = ""
    self.rotator_last_command = ""
    self.rotator_command_index = 1
    
  def control_rotator(self) -> None:
    # Check if new angles are required
    if self.new_angles_required:
      self.calculate_rotator_angles()
      self.create_rotator_command()
      self.new_angles_required = False
    sleep(0.1)

  def calculate_rotator_angles(self) -> None:
    # Refrences: 
    # * https://gis.stackexchange.com/questions/58923/calculating-view-angle
    # * https://stackoverflow.com/questions/60515719/are-there-functions-for-converting-earth-coordinate-systems-within-the-standard
    
    # Don't continue if any coordinates are 0
    if any(value == 0.0 for value in self.rotator_position.values()) or any(value == 0.0 for value in self.target_position.values()):
      return
    
    # Convert rotator position to ECEF
    rotator_ecef = EarthLocation.from_geodetic(lat=self.rotator_position["latitude"], 
                                lon=self.rotator_position["longitude"], 
                                height=self.rotator_position["altitude"]).geocentric
    rotator_ecef = (rotator_ecef[0].value, rotator_ecef[1].value, rotator_ecef[2].value)
    
    # Convert target position to ECEF
    target_ecef = EarthLocation.from_geodetic(lat=self.target_position["latitude"],
                                lon=self.target_position["longitude"],
                                height=self.target_position["altitude"]).geocentric
    target_ecef = (target_ecef[0].value, target_ecef[1].value, target_ecef[2].value)
    
    # Calculate the vector between the rotator and the target
    vector = (target_ecef[0] - rotator_ecef[0], target_ecef[1] - rotator_ecef[1], target_ecef[2] - rotator_ecef[2])
    
    # Calculate the elevation cosine
    # Cos(elevation) = (x*dx + y*dy + z*dz) / Sqrt((x^2+y^2+z^2)*(dx^2+dy^2+dz^2))
    elevation_cosine = rotator_ecef[0] * vector[0] + rotator_ecef[1] * vector[1]  + rotator_ecef[2] * vector[2]
    elevation_cosine /= ((rotator_ecef[0]**2 + rotator_ecef[1]**2 + rotator_ecef[2]**2) * (vector[0]**2 + vector[1]**2 + vector[2]**2))**0.5

    # Calculate the azimuth cosine
    # Cos(azimuth) = (-z*x*dx - z*y*dy + (x^2+y^2)*dz) / Sqrt((x^2+y^2)(x^2+y^2+z^2)(dx^2+dy^2+dz^2))
    azimuth_cosine = (-rotator_ecef[2] * rotator_ecef[0] * vector[0]) - (rotator_ecef[2] * rotator_ecef[1] * vector[1]) + ((rotator_ecef[0]**2 + rotator_ecef[1]**2) * vector[2])
    azimuth_cosine /= ((rotator_ecef[0]**2 + rotator_ecef[1]**2) * (rotator_ecef[0]**2 + rotator_ecef[1]**2 + rotator_ecef[2]**2) * (vector[0]**2 + vector[1]**2 + vector[2]**2))**0.5

    # Calculate the azimuth sine
    # Sin(azimuth) = (-y*dx + x*dy) / Sqrt((x^2+y^2)(dx^2+dy^2+dz^2))
    azimuth_sine = (-rotator_ecef[1] * vector[0] + rotator_ecef[0] * vector[1])
    azimuth_sine /= ((rotator_ecef[0]**2 + rotator_ecef[1]**2) * (vector[0]**2 + vector[1]**2 + vector[2]**2))**0.5
    
    # Get elevation and azimuth angles in radians
    elevation = np.arccos(elevation_cosine)
    azimuth = np.arctan2(azimuth_sine, azimuth_cosine)
    
    # Convert angles to degrees
    elevation = 90 - np.rad2deg(elevation)
    if elevation < 0:
      elevation = 0
    azimuth = np.rad2deg(azimuth)
    if azimuth < 0:
      azimuth += 360
      
    # Round the angles
    elevation = round(elevation, 2)
    azimuth = round(azimuth, 2)
        
    # Set angles
    self.rotator_angles = {"azimuth": azimuth, "elevation": elevation}
    
  def create_rotator_command(self) -> None:
    self.rotator_last_command = self.rotator_command
    self.rotator_command = f"{self.rotator_angles['azimuth']},{self.rotator_angles['elevation']}"
    
  def set_target(self, target) -> None:
    print(f"Setting rotator target from {self.rotator_target} to {target}")
    self.rotator_target = target
    
  def set_control_mode(self, mode) -> None:
    print(f"Setting rotator control from {self.rotator_control_mode} to {mode}")
    self.rotator_control_mode = mode
    
  def set_rotator_position_mode(self, mode) -> None:
    print(f"Setting rotator position mode from {self.rotator_position_mode} to {mode}")
    self.rotator_position_mode = mode
  
  def set_auto_rotator_position(self, latitude, longitude, altitude) -> None:
    # Check if in auto mode
    if self.rotator_position_mode == "auto":
      # Check if passed values are floats
      if isinstance(latitude, float) and isinstance(longitude, float) and isinstance(altitude, float):
        # Check if the rotator position is not already the same as the passed in values
        if self.rotator_position["latitude"] != latitude and self.rotator_position["longitude"] != longitude and self.rotator_position["altitude"] != altitude:
          self.rotator_position = {"latitude": latitude, "longitude": longitude, "altitude": altitude}
          self.new_angles_required = True
    sleep(0.1)
  
  def set_auto_target_position(self, latitude, longitude, altitude) -> None:
    # Check if in auto mode
    if self.rotator_control_mode == "auto":
      # Check if passed values are floats
      if isinstance(latitude, float) and isinstance(longitude, float) and isinstance(altitude, float):
        # Check if the rotator target position is not already the same as the passed in values
        if self.target_position["latitude"] != latitude and self.target_position["longitude"] != longitude and self.target_position["altitude"] != altitude:
          self.target_position = {"latitude": latitude, "longitude": longitude, "altitude": altitude}
          self.new_angles_required = True
    
  def set_manual_rotator_position(self, latitude, longitude, altitude) -> None:
    if self.rotator_position_mode == "auto":
      self.set_rotator_position_mode("manual")
      print(f"Rototor is now in manual position mode")
    print(f"Rotator position is manually set to {latitude}, {longitude}, {altitude}")
    self.rotator_position = {"latitude": latitude, "longitude": longitude, "altitude": altitude}
    self.new_angles_required = True
  
  def set_manual_target_position(self, latitude, longitude, altitude) -> None:
    if self.rotator_control_mode == "auto":
      self.set_control_mode("manual")
      print(f"Rototor is now in manual control mode")
    print(f"Setting rotator target position to {latitude}, {longitude}, {altitude}")
    self.target_position = {"latitude": latitude, "longitude": longitude, "altitude": altitude}
    self.new_angles_required = True
    
  def set_manual_angles(self, azimuth, elevation):
    if self.rotator_control_mode == "auto":
      self.set_control_mode("manual")
      print(f"Rototor is now in manual control mode")
      
    self.rotator_angles = {"azimuth": azimuth, "elevation": elevation}
    self.new_angles_required = False
    self.rotator_command = f"{self.rotator_angles['azimuth']},{self.rotator_angles['elevation']}"
    
    # Set the last command to empty so that the custom angles are sent right away
    self.rotator_last_command = ""