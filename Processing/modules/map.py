import folium
import pandas as pd
import flask
from time import sleep
import os
from bs4 import BeautifulSoup

class Map:
  def __init__(self, map_server_port: int) -> None:
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
      return flask.render_template("map.html")
  
  def run_server(self) -> None:
    self.app.run(port=self.port, host="0.0.0.0", debug=False, use_reloader=False)
    
  def update_map(self) -> None:
    if self.map_update_required:
      self.create_map()
    sleep(0.1)
  
  def create_map(self) -> None:
    """    
    Generates a map with the all the given coordinates.
    """
    
    # Check if at least one list is given
    if self.ballon_coordinates == [] and self.payload_coordinates == [] and self.prediction_coordinates == [] and self.rotator_coordinates == []:
      print("No coordinates given.")
      return
    
    # Init map with first coordinate as center
    try:
      m = folium.Map([0, 0])
    except Exception as e:
      print(f"Error creating map: {e}")
      return
    
    # Add balloon position
    if self.ballon_coordinates:
      try:
        # Start position
        folium.Marker(
            location=self.ballon_coordinates[0],
            popup=f"{self.ballon_coordinates[0][0]}, {self.ballon_coordinates[0][11]}",
            tooltip="Balloon starting position",
            icon=folium.Icon(color="darkred"),
        ).add_to(m)

        # Last position
        folium.Marker(
            location=self.ballon_coordinates[-1],
            popup=f"{self.ballon_coordinates[-1][0]}, {self.ballon_coordinates[-1][1]}",
            tooltip="Balloon last position",
            icon=folium.Icon(color="red"),
        ).add_to(m)
      
        # Trajectory
        folium.PolyLine(
            locations=self.ballon_coordinates,
            color="red",
            weight=5,
            tooltip="Balloon trajectory",
        ).add_to(m)
        
      except Exception as e:
        self.ballon_coordinates = []
        print(f"Error adding balloon coordinates to map: {e}")
    
    # Add payload position
    if self.payload_coordinates:
      try:
        # Start position
        folium.Marker(
            location=self.payload_coordinates[0],
            popup=f"{self.payload_coordinates[0][0], self.payload_coordinates[0][1]}",
            tooltip="Payload starting position",
            icon=folium.Icon(color="darkblue"),
        ).add_to(m)

        # Last position
        folium.Marker(
            location=self.payload_coordinates[-1],
            popup=f"{self.payload_coordinates[-1][0], self.payload_coordinates[-1][1]}",
            tooltip="Payload last position",
            icon=folium.Icon(color="blue"),
        ).add_to(m)
      
        # Trajectory
        folium.PolyLine(
            locations=self.payload_coordinates,
            color="blue",
            weight=5,
            tooltip="Payload trajectory",
        ).add_to(m)
        
      except Exception as e:
        self.payload_coordinates = []
        print(f"Error adding payload coordinates to map: {e}")
    
    # Add predicion position
    if self.prediction_coordinates:
      try:
        # Start position
        folium.Marker(
            location=self.prediction_coordinates[0],
            popup=f"{self.prediction_coordinates[0][0], self.prediction_coordinates[0][1]}",
            tooltip="Prediction starting point",
            icon=folium.Icon(color="darkpurple"),
        ).add_to(m)

        # Last position
        folium.Marker(
            location=self.prediction_coordinates[-1],
            popup=f"{self.prediction_coordinates[-1][1], self.prediction_coordinates[-1][1]}",
            tooltip="Prediction landing point",
            icon=folium.Icon(color="purple"),
        ).add_to(m)
      
        # Trajectory
        folium.PolyLine(
            locations=self.prediction_coordinates,
            color="cyan",
            weight=5,
            tooltip="Prediction trajectory",
        ).add_to(m)
        
      except Exception as e:
        self.prediction_coordinates = []
        print(f"Error adding prediction coordinates to map: {e}")
        
    # Add rotator position
    if self.rotator_coordinates:
      try:
        folium.Marker(
          location=self.rotator_coordinates[0],
          popup=f"{self.rotator_coordinates[0][0], self.rotator_coordinates[0][1]}",
          tooltip="Rotator position",
          icon=folium.Icon(color="green"),
        ).add_to(m)
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
      m.fit_bounds([sw, ne])
    except Exception as e:
      print(f"Error fitting map to bounds: {e}")
      return
    
    # Save the map
    path = os.path.join(os.path.dirname(__file__), "../templates/map.html")
    m.save(path)
    
    soup = BeautifulSoup(open(path), 'html.parser')
    head = soup.find('head')
    if head:
      head.append(BeautifulSoup("""<meta http-equiv="refresh" content="30">""", 'html.parser'))  # Needs to be parsed as html by BeautifulSoup to work.
    with open(path, 'w') as html_file:
      html_file.write(str(soup))
    
    self.map_update_required = False  
  
  def clear_ballon_coordinates(self) -> None:
    self.ballon_coordinates = []
    self.map_update_required = True
    
  def clear_payload_coordinates(self) -> None:
    self.payload_coordinates = []
    self.map_update_required = True
      
  def clear_prediction_coordinates(self) -> None:
    self.prediction_coordinates = []
    self.map_update_required = True
    
  def clear_rotator_coordinates(self) -> None:
    self.rotator_coordinates = []
    self.map_update_required = True