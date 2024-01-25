import math

def calculate_flight_computer_extra_telemetry(old_data: dict, new_data: dict, rotator_data: dict, time_delta: int, structure: list):
  try:
    calculated_data = dict.fromkeys(structure, 0.0)
    
    # Calculate vertical speed
    try:
      calculated_data["gps_vertical_speed"] = round((new_data["gps_altitude"] - old_data["gps_altitude"]) / time_delta, 2)
      calculated_data["baro_vertical_speed"] = round((new_data["baro_altitude"] - old_data["baro_altitude"]) / time_delta, 2)
    except:
      pass
    
    try:
      # Calculate horizontal speed
      calculated_data["horizontal_speed"] = round(((new_data["gps_latitude"] - old_data["gps_latitude"])**2 + (new_data["gps_longitude"] - old_data["gps_longitude"])**2)**0.5 / time_delta, 2)
    except:
      pass
    
    try:
      # Calculate total speed
      calculated_data["gps_total_speed"] = round((calculated_data["horizontal_speed"]**2 + calculated_data["gps_vertical_speed"]**2)**0.5, 2)
    except:
      pass
      
    try:
      # Calculate ground distance from rotator to flight computer (haversine formula)
      # Convert degrees to radians
      lat1_rad = math.radians(rotator_data["latitude"])
      lon1_rad = math.radians(rotator_data["longitude"])
      lat2_rad = math.radians(new_data["gps_latitude"])
      lon2_rad = math.radians(new_data["gps_longitude"])

      # Differences in coordinates
      dlon = lon2_rad - lon1_rad
      dlat = lat2_rad - lat1_rad

      # Haversine formula
      a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
      c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  
      distance = 6371.0 * c

      calculated_data["ground_distance_to_rotator"] = round(distance, 2)
    except:
      pass
    
    try:
      # Calculate straight line distance from rotator to flight computer (Pythagorean theorem)
      calculated_data["straight_line_distance_to_rotator"] = round((((new_data["gps_latitude"] - rotator_data["latitude"])**2 + (new_data["gps_longitude"] - rotator_data["longitude"])**2 + (new_data["gps_altitude"] - rotator_data["altitude"])**2)**0.5) / 1000, ndigits=2)
    except:
      pass
    
    return calculated_data
  
  except Exception as e:
    print(f"An error occurred while calculating extra telemetry: {e}")
    return {}