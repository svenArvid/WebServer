import os
from flask import Flask, render_template
from random import randint
from flask import jsonify
import datetime
import Modbus
import WebServer

app = Flask(__name__)
pwd = ""


@app.route('/GetSignals/<signalStr>')
def get_signals(signalStr):
  now = datetime.datetime.utcnow()
  total_time_ms = (now - datetime.datetime(1970, 1, 1)).total_seconds()*1000
  
  signalStr  = signalStr.rstrip(',')
  signalList = signalStr.split(',')
  signalVals = []
  
  for sigName in signalList:
    signalVals.append(modbus.read_signal(sigName))
    
  return jsonify({"time": int(total_time_ms), "signal": signalVals})

    
@app.route('/SetParam/<paramStr>/<val>')
def SetParam(paramStr,val):
  modbus.write_param(paramStr, val)
  return ""

    
@app.route('/SetParamCallback/<paramStr>/<val>')
def SetParamCallback(paramStr, val):
  del val                            # val not used 
  new_val = modbus.read_param(paramStr)
  return jsonify({"param": new_val})    
    
    
@app.route('/ParamList')
def ParamList():
  return render_template('ParamList.html')

    
@app.route('/Test')
def test_view():
  return render_template('TwoGraphsServer.html')


@app.route('/')
def sensor_view():
  template_data = {'sensor': {"temperature": [[999100000, 5], [999111000, 7], [999113000, 10], [999114000, 11]], "relative_humidity": [15, 19, 17, 16], "namn": "TheName"}}

  return render_template('template_sensors.html', **template_data)


if __name__ == '__main__':
  # Note: port 80 was used by other windows app, so to be able to use port 80, had to stop that app
  # See Youtube: How to Fix:"Port 80 is used by another application ampps" - Apache start
  pwd = os.getcwd()
  print (pwd)
  try:
    modbus = Modbus.ModbusMaster("COM5")
    modbus.start()
    modbus.set_slave_id(10)
    print(modbus.read_signal("SensorIG53A_RpmFild"))
  except:
    pass
  
  app.run(host='0.0.0.0', port=5000, debug=False)
