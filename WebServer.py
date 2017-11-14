import os
from flask import Flask, render_template
from random import randint
from flask import jsonify
import datetime

app = Flask(__name__)
pwd = ""

@app.route('/GetLatest')
def get_latest():
    now = datetime.datetime.utcnow()
    total_time_ms = (now - datetime.datetime(1970, 1, 1)).total_seconds()*1000

    get_latest.counter += 10
    log_file = open("log.txt", "r")
    file_dump = log_file.read()
    lines = file_dump.splitlines()
    data = lines[get_latest.counter].split(',')
    data = [int(i) for i in data]    # Convert list of strings to ints
    log_file.close()

    return jsonify({"time": int(total_time_ms), "signal": data})


get_latest.counter = 0


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
    app.run(host='0.0.0.0', port=5000, debug=True)
