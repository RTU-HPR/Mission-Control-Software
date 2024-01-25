import time
from struct import pack, unpack

def convert_message_to_ccsds(apid: int, sequence_count: int, data_str: str, telecommand: bool = False):
  """
  Refrences: https://public.ccsds.org/Pubs/133x0b2c1.pdf 
  Most of the useful information about packet structure starts from page 31
  """
  # Convert each value string to corresponding data type and convert to bytearray
  packet_data = bytearray()
  
  # If creating a telecommand, the first value in data str is the packet id and it is a 16-bit integer
  if telecommand:
    try:
      packet_data += bytearray(pack("H", int(data_str.split(",")[0]) & 0xFFFF))
      data_str = ",".join(data_str.split(",")[1:])
    except Exception as e:
      print(f"Error converting packet id to bytearray: {e}. Full message: {data_str}")
      return None
    
  for value in data_str.split(","):
    try:
      # Integer
      if value.isdigit():    
        byte = bytearray(pack("i", int(value) & 0xFFFFFFFF))
        byte.reverse() # Reverse the byte order as msbf is required, but pack returns lsbf
        packet_data += byte
      # Float
      elif isfloat(value):
        byte = bytearray(pack("f", float(value)))
        byte.reverse() # Reverse the byte order as msbf is required, but pack returns lsbf
        packet_data += byte
      else:
        raise Exception(f"Invalid data type: {value}")
    except Exception as e:
      print(f"Error converting value {value} to bytearray: {e}. Full message: {data_str}")
      return None
    
  # Create full packet
  try:
    packet = create_primary_header(apid, sequence_count, len(packet_data), not telecommand)
    # Only telemetry packets have a secondary header
    if not telecommand:
      packet += create_secondary_header()
    packet += packet_data
    
  except Exception as e:
    print(f"Error creating primary header: {e}. Full message: {data_str}")
    return None
  
  return packet


def parse_ccsds_packet(packet: bytearray):
  try:
    # Convert packet from bytes to hexadecimal string
    packet_hex = packet.hex()
    
    # Get the binary array
    ccsds_binary = bin(int(packet_hex, 16))[2:].zfill(len(packet_hex) * 4)
    packet_version_number = ccsds_binary[:3]      
  
    packet_identification_field = ccsds_binary[3:16]
    packet_type = packet_identification_field[0]
    secondary_header_flag = packet_identification_field[1:2]
    apid = packet_identification_field[2:]

    packet_sequence_control = ccsds_binary[16:32]
    sequence_flags = packet_sequence_control[:2]
    packet_sequence_count = packet_sequence_control[2:]
    
    packet_data_length = ccsds_binary[32:48]
    
    # Telemetry packets have a secondary header
    if int(packet_type, 2) == 0:
      # Secondary header field
      secondary_header = ccsds_binary[48:96]
      epoch_seconds = secondary_header[:32]
      epoch_subseconds = secondary_header[32:]

      # User data field
      packet_data = ccsds_binary[96:]
      
    # Telecommand packets do not have a secondary header
    else:
      epoch_seconds = b"0"
      epoch_subseconds = b"0"
      
      # User data field
      packet_data = ccsds_binary[48:]
    
    # Convert to usable data types
    apid = int(apid, 2)
    epoch_seconds = int(epoch_seconds, 2)
    epoch_subseconds = int(epoch_subseconds, 2)

    return (apid, epoch_seconds, epoch_subseconds, packet_data)
        
  except Exception as e:
    print(f"Error converting packet to message: {e}. Full packet: {packet}")
    return None
  

def create_primary_header(apid: int, sequence_count: int, data_length: int, secondary_header: bool = True) -> bytearray:
  """
  Creates the primary header of a CCSDS packet.
  """
  ## Packet version number - 3 bits total
  PACKET_VERSION_NUMBER = b"000"
  
  ## Packet identification field - 13 bits total
  # Packet type (0 is telemetry, 1 is telecommand)- 1 bit
  # Secondary header flag - 1 bit
  # APID (Application Process Identifier) - 11 bits
  PACKET_TYPE = b"0"
  if secondary_header:
    SECONDARY_HEADER_FLAG = b"1"
  else:
    SECONDARY_HEADER_FLAG = b"0"
  apid_binary = bin(apid)[2:].zfill(11).encode()
  packet_identification_field = PACKET_TYPE + SECONDARY_HEADER_FLAG + apid_binary
  
  ## Packet Sequence Control - 16 bits total
  # Sequence flags (Always 11, as we are sending a single undivided packet) - 2 bits
  # Packet Sequence Count (Packet index)- 14 bits
  PACKET_SEQUENCE_FLAG = b"11"
  packet_sequence_count = bin(sequence_count)[2:].zfill(14).encode()
  packet_sequence_control = PACKET_SEQUENCE_FLAG + packet_sequence_count
  
  ## Packet data length - 16 bits total
  # 16-bit field contains a length count that equals one fewer than the length of the data field
  packet_data_length = bin(data_length - 1)[2:].zfill(16).encode()
  
  # Create the primary header
  primary_header = PACKET_VERSION_NUMBER + packet_identification_field + packet_sequence_control + packet_data_length
  primary_header = bytearray(int(primary_header[i:i+8], 2) for i in range(0, len(primary_header), 8))

  return primary_header
  
def create_secondary_header() -> bytearray:
  # Get the current time in seconds and subseconds
  epoch_seconds = int(time.time())
  epoch_subseconds = int((time.time() - epoch_seconds) * 65536)
  
  # Convert to binary
  epoch_seconds = bin(epoch_seconds)[2:].zfill(32).encode()
  epoch_subseconds = bin(epoch_subseconds)[2:].zfill(16).encode()
  
  # Create the secondary header
  secondary_header = epoch_seconds + epoch_subseconds
  secondary_header = bytearray(int(secondary_header[i:i+8], 2) for i in range(0, len(secondary_header), 8))
  
  return secondary_header 

def isfloat(value: str) -> bool:
  """
  Checks if a string is a float.
  """
  try:
    float(value)
    return True
  except ValueError:
    return False

def binary_to_float(binary):
  return unpack('!f',pack('!I', int(binary, 2)))[0]

def binary_to_int(binary):
  return int(binary, 2)
  