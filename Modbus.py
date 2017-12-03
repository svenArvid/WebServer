import serial
import time
import threading
import ctypes

SLAVE_ID_INDX = 0
FUNCTION_CODE_INDX = 1

crc16_lookup = [ 
  0, 49345, 49537, 320, 49921, 960, 640, 49729, 50689, 1728,1920,51009,1280,50625,50305,1088,
  52225,3264,3456,52545,3840,53185,52865,3648, 2560,51905, 52097,2880,51457,2496,2176,51265,
  55297,6336,6528,55617,6912,56257,55937,6720, 7680,57025,57217,8000,56577,7616,7296,56385,
  5120,54465,54657,5440,55041,6080,5760,54849, 53761,4800,4992,54081,4352,53697,53377,4160,
  61441,12480,12672,61761,13056,62401,62081,12864, 13824,63169,63361,14144,62721,13760,13440,62529,
  15360,64705,64897,15680,65281,16320,16000,65089, 64001,15040,15232,64321,14592,63937,63617,14400,
  10240,59585,59777,10560,60161,11200,10880,59969, 60929,11968,12160,61249,11520,60865,60545,11328,
  58369,9408,9600,58689,9984,59329,59009,9792, 8704,58049,58241,9024,57601,8640,8320,57409,
  40961,24768,24960,41281,25344,41921,41601,25152, 26112,42689,42881,26432,42241,26048,25728,42049,
  27648,44225,44417,27968,44801,28608,28288,44609, 43521,27328,27520,43841,26880,43457,43137,26688,
  30720,47297,47489,31040,47873,31680,31360,47681, 48641,32448,32640,48961,32000,48577,48257,31808,
  46081,29888,30080,46401,30464,47041,46721,30272, 29184,45761,45953,29504,45313,29120,28800,45121,
  20480,37057,37249,20800,37633,21440,21120,37441, 38401,22208,22400,38721,21760,38337,38017,21568,
  39937,23744,23936,40257,24320,40897,40577,24128, 23040,39617,39809,23360,39169,22976,22656,38977,
  34817,18624,18816,35137,19200,35777,35457,19008, 19968,36545,36737,20288,36097,19904,19584,35905,
  17408,33985,34177,17728,34561,18368,18048,34369, 33281,17088,17280,33601,16640,33217,32897,16448
]
  
param_names = [ 
  "E2P_ECR_PITCH_LEVER_AHEAD_A",
  "E2P_ECR_PITCH_LEVER_ZERO_A",
  "E2P_ECR_PITCH_LEVER_ASTERN_A",
  "E2P_ECR_RPM_LEVER_MAX_A", 
  "E2P_ECR_RPM_LEVER_MIN_A",
  "E2P_CLUTCH_SPRING_PRESSURE",
  "E2P_CLUTCH_IN_PRE_PRESSURE",
  "E2P_NEO_PIXEL_APP"
]
 
signal_names = [
  "RoomTempSnsr.Temperature",
  "RoomTempSnsr.ADCVal",
  "SensorIG53A_Rpm",
  "SensorIG53B_Rpm",
  "SensorIG53A_RpmFild",
  "SensorIG53B_RpmFild"
]


def calc_crc(buffer):
  Crc = 0xFFFF

  for byte in buffer:
    Crc = (Crc >> 8) ^ crc16_lookup[(byte ^ Crc) & 0xFF]
  return Crc
    
    
def open_port(port_name):

  serial_port = serial.Serial(port_name)
  serial_port.baudrate = 9600
  serial_port.bytesize = 8
  serial_port.parity = 'N'
  serial_port.stopbits = 1
  serial_port.timeout = 0.0

  serial_port.flushInput()

  print(serial_port.name + " opened")
  return serial_port

    
class ModbusMessage:
  def __init__(self, id=0, fc=4, first_reg=0, num_reg=1, payload=[]):
    self.slave_id = id
    self.function_code = fc
    self.first_reg = first_reg    
    self.num_reg = num_reg
    self.payload = payload
      
  
# Take an instance of a Modbus message and create annd return the byte array of the Modbus request
# If function code is not supported, return None
  def CreateRequest(self):
    buff = bytearray()
    buff.append(self.slave_id)
    buff.append(self.function_code)
    
    buff.append((self.first_reg >> 8) & 0xFF)  # Data Address of the first register
    buff.append(self.first_reg & 0xFF)
    
    if self.function_code == 4:
      buff.append((self.num_reg >> 8) & 0xFF)  # Total number of registers requested
      buff.append(self.num_reg & 0xFF)   
    
    elif self.function_code == 6:
      buff.append((self.payload[0] >> 8) & 0xFF)
      buff.append(self.payload[0] & 0xFF)        # The value to write 
      
    elif self.function_code == 16:
       pass
       
    else:  # Function code not supported
      return None
     
    # Append Crc
    Crc = calc_crc(buff)
    
    buff.append(Crc & 0xFF)         # Note: The high and low byte of CRC shall be swapped in Modbus protocol
    buff.append((Crc >> 8) & 0xFF)

    return buff
        
        
class ModbusMaster(threading.Thread):

  def __init__(self,port_name):
    self.params = dict()
    self.signals = dict()
    self.slave_id = 0
    self.pending_requests = []
    
    for p in param_names:
      self.params[p] = 0
    
    for s in signal_names:
      self.signals[s] = 0
      
    threading.Thread.__init__(self)
    self.com_port = open_port(port_name)
    self.timeout = 0.2
    print "Init"
        
  
  def set_slave_id(self, new_id):
    self.slave_id = new_id
  
  
  def read_signal(self, sigName):
    return self.signals[sigName]

  
  def read_param(self, paramName):
    return self.params[paramName]
    
    
  # External Request to write parameter.
  # Create a Modbus function code 6 request and put in queue, i.e. request will be sent to slave node when it it the first message in the queue
  def write_param(self, paramStr, val):
    indx = param_names.index(paramStr) + 0X1000  # Add Offset 0x1000 to register to access E2p array
    new_message = ModbusMessage(id=self.slave_id, fc=6, first_reg=indx, num_reg=1, payload=[int(val)])
    self.pending_requests.append(new_message)
    
    
  # Read Modbus slave response      
  def read_response(self, data):
    if data[SLAVE_ID_INDX] == self.slave_id:
      if calc_crc(data) == 0:    # Note: In modbus if we include message crc in calculation the expected result is 0
              
        if data[FUNCTION_CODE_INDX] == 4:             # Function code 4
          num_reg = data[2]/2
          offset = 3
          for i in range(0,num_reg):
            self.signals[signal_names[i]] = int(data[offset] << 8) + int(data[offset + 1])
            offset += 2
        
        elif data[FUNCTION_CODE_INDX] == 6:          # Function code 6
          data_address = int(data[2] << 8) + int(data[3]) - 0x1000       # Remove Offset 0x1000 to access lists here
          print data_address
          print param_names[data_address]
          self.params[param_names[data_address]] = int(data[4] << 8) + int(data[5])
      
      
  def write_next_request(self):
    if len(self.pending_requests) > 0:
      next_request = self.pending_requests.pop(0)
    
    else:  # send default request 
      next_request = ModbusMessage(id=self.slave_id, fc=4, first_reg=0, num_reg=6, payload=[])          
      
    tx_buff = next_request.CreateRequest()
    if tx_buff is not None:
      print(' '.join('{:02X}'.format(b) for b in tx_buff))
      self.com_port.write(tx_buff)
  
  
  def run(self):
    while True:
      rx_num_bytes = self.com_port.inWaiting()
      print(rx_num_bytes)
      rx_buff = bytearray(self.com_port.read(rx_num_bytes))    # response from previous request
      
      print(' '.join('{:02X}'.format(b) for b in rx_buff))
      if len(rx_buff) > 4:
        self.read_response(rx_buff)
      # flush      
       
      #self.com_port.write(bytearray([0x0A, 0x04, 0x00, 0x00, 0x00, 0x06, 0x71, 0x73]))  # send new request
      self.write_next_request()
      
      time.sleep(self.timeout)


if __name__ == "__main__":
      
  modbus_thread = ModbusMaster("COM5")
  modbus_thread.start()
  
  while True:
    print "In main"
    time.sleep(1.0)
    print modbus_thread.signals["RoomTempSnsr.Temperature"]
    print modbus_thread.signals["RoomTempSnsr.ADCVal"]
    print modbus_thread.signals["SensorIG53A_Rpm"]
    print modbus_thread.signals["SensorIG53B_Rpm"]
    print modbus_thread.signals["SensorIG53A_RpmFild"]
    print modbus_thread.signals["SensorIG53B_RpmFild"]

    
# .write
# inWaiting
# flush
# bytearray(.read
# response 0A 04 04 01 F5 01 F9 91 58