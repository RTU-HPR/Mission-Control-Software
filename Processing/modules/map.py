import datetime
from flask import jsonify
from bs4 import BeautifulSoup
import flask
import folium
import os
import pandas as pd
from time import sleep
import requests
from config import *
from modules.processor import PacketProcessor

class Map:
  def __init__(self, processor: PacketProcessor, map_server_port: int) -> None:
    self.processor = processor
     
    # Map
    self.ballon_coordinates = []
    self.payload_coordinates = []
    self.prediction_coordinates = []
    self.rotator_coordinates = []
    self.map_update_required = False
        
    # Server
    self.app = flask.Flask(__name__, template_folder="../templates")
    self.app.config["TEMPLATES_AUTO_RELOAD"] = True
    self.port = map_server_port
    
    # Routes
    @self.app.route("/")
    def index():
      return flask.render_template("base.html")
    
    @self.app.route("/prediction/<vehicle>", methods=["POST"])
    def prediction(vehicle) -> flask.Response:
      if vehicle == "balloon":
        if self.processor.bfc_telemetry["gps_latitude"] != 0 and self.processor.bfc_telemetry["gps_longitude"] != 0:
          if self.get_landing_prediction(ASCENT_RATE,
                        self.processor.bfc_telemetry["gps_altitude"],
                        DESCENT_RATE,
                        self.processor.bfc_telemetry["gps_latitude"],
                        self.processor.bfc_telemetry["gps_longitude"]) is not None:
            return jsonify({"status": "error", "message": "API request failed."})
          self.map_update_required = True
          return jsonify({"status": "ok"})
        else:
          return jsonify({"status": "error", "message": "No GPS coordinates available."})
      elif vehicle == "payload":
        if self.processor.pfc_telemetry["gps_latitude"] != 0 and self.processor.pfc_telemetry["gps_longitude"] != 0:
          if self.get_landing_prediction(ASCENT_RATE,
                        self.processor.pfc_telemetry["gps_altitude"],
                        DESCENT_RATE,
                        self.processor.pfc_telemetry["gps_latitude"],
                        self.processor.pfc_telemetry["gps_longitude"]) is not None:
            return jsonify({"status": "error", "message": "API request failed."})
          self.map_update_required = True
          return jsonify({"status": "ok"})
        else:
          return jsonify({"status": "error", "message": "No GPS coordinates available."})
      else:
        return jsonify({"status": "error", "message": "Invalid vehicle."})
    
    
  def run_server(self) -> None:
    self.app.run(port=self.port, host="0.0.0.0", debug=False, use_reloader=False)
    
  def update_map(self) -> None:
    if self.map_update_required:
      self.create_map()
    sleep(0.1)
  
  def add_coordinates_to_map(self, coordinates, start_color, end_color, line_color, tooltip):
    if coordinates:
      try:
        # Start position
        folium.Marker(
            location=coordinates[0],
            popup=f"{coordinates[0][0]}, {coordinates[0][1]}",
            tooltip=f"{tooltip} starting position",
            icon=folium.Icon(color=start_color),
        ).add_to(self.m)

        # Last position
        folium.Marker(
            location=coordinates[-1],
            popup=f"{coordinates[-1][0]}, {coordinates[-1][1]}",
            tooltip=f"{tooltip} last position",
            icon=folium.Icon(color=end_color),
        ).add_to(self.m)
      
        # Trajectory
        folium.PolyLine(
            locations=coordinates,
            color=line_color,
            weight=5,
            tooltip=f"{tooltip} trajectory",
        ).add_to(self.m)
        
      except Exception as e:
        print(f"Error adding {tooltip} coordinates to map: {e}")
        coordinates = []
  
  def get_landing_prediction(self, ascent_rate, burst_altitude, descent_rate, launch_latitude, launch_longitude):
    url = "https://api.v2.sondehub.org/tawhiri"
    payload = {
        "launch_latitude": launch_latitude,
        "launch_longitude": launch_longitude,
        "launch_datetime": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        "launch_altitude": burst_altitude - 10,
        "ascent_rate": ascent_rate,
        "burst_altitude": burst_altitude,
        "descent_rate": descent_rate,
    }
    
    try:
      response = requests.post(url, json=payload)
      data = response.json()
      if "prediction" not in data:
        raise Exception("API request failed")
      self.prediction_coordinates.clear()
            
      for stage in data["prediction"]:
        if stage["stage"] == "descent":
          trajectory = stage["trajectory"]
          for point in trajectory:
            latitude = point["latitude"]
            longitude = point["longitude"]
            print(latitude, longitude)
            self.prediction_coordinates.append((latitude, longitude))
            
    except Exception as e:
      return e
  
  def create_map(self) -> None:
    # Check if at least one list is given
    if self.ballon_coordinates == [] and self.payload_coordinates == [] and self.prediction_coordinates == [] and self.rotator_coordinates == []:
      print("No coordinates given.")
      return
    
    # Create map    
    try:
      self.m = folium.Map([0, 0])
    except Exception as e:
      print(f"Error creating map: {e}")
      return
    
    # Add balloon position
    if self.ballon_coordinates:
      self.add_coordinates_to_map(self.ballon_coordinates, "darkred", "red", "red", "Balloon")
        
    # Add payload position
    if self.payload_coordinates:
      self.add_coordinates_to_map(self.payload_coordinates, "darkblue", "blue", "blue", "Payload")

    # Add predicion position
    if self.prediction_coordinates:
      self.add_coordinates_to_map(self.prediction_coordinates, "darkpurple", "purple", "cyan", "Prediction")
        
    # Add rotator position
    if self.rotator_coordinates:
      try:
        folium.Marker(
          location=self.rotator_coordinates[0],
          popup=f"{self.rotator_coordinates[0][0], self.rotator_coordinates[0][1]}",
          tooltip="Rotator position",
          icon=folium.Icon(color="green"),
        ).add_to(self.m)
      except Exception as e:
        self.rotator_coordinates = []
        print(f"Error adding rotator coordinates to map: {e}")
    
    try:
      # Calculate most extreme south west and north east coordinates
      all_coordinates = self.ballon_coordinates + self.payload_coordinates + self.prediction_coordinates + self.rotator_coordinates
      df = pd.DataFrame(all_coordinates, columns=["Lat", "Lng"])
      sw = df[["Lat", "Lng"]].min().values.tolist()
      ne = df[["Lat", "Lng"]].max().values.tolist()

      # Fit map to bounds
      self.m.fit_bounds([sw, ne])
    except Exception as e:
      print(f"Error fitting map to bounds: {e}")
      return
    
    # Save the map
    path = os.path.join(os.path.dirname(__file__), "../templates/map.html")
    self.m.save(path)
    
    # soup = BeautifulSoup(open(path), 'html.parser')
    # head = soup.find('head')
    # if head:
    #   head.append(BeautifulSoup("""<meta http-equiv="refresh" content="30">""", 'html.parser'))
    # with open(path, 'w') as html_file:
    #   html_file.write(str(soup))
    
    self.map_update_required = False  
    