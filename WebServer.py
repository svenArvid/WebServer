from flask import Flask, render_template
from random import randint
from flask import jsonify
import datetime

app = Flask(__name__)


@app.route('/GetLatest')
def get_latest():
    now = datetime.datetime.utcnow()
    total_time_ms = (now - datetime.datetime(1970, 1, 1)).total_seconds()*1000
    r1 = randint(0, 9)
    r2 = randint(10, 19)
    r3 = randint(-5,5)
    return jsonify({"time": int(total_time_ms), "signal": [r1, r2, r3]})


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
    app.run(host='0.0.0.0', port=5000, debug=True)
