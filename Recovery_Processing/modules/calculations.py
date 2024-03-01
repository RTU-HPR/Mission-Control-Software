import math

def calculate_flight_computer_extra_telemetry(old_data: dict, new_data: dict, time_delta: int, structure: list):
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
    
    return calculated_data
  
  except Exception as e:
    print(f"An error occurred while calculating extra telemetry: {e}")
    return {}