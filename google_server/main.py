import os
import time
from datetime import datetime, timedelta
import urllib.request, simplejson
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    now = datetime.now()
    while now.minute % 5 != 0:
        time.sleep(60)
        now = datetime
    station_status = simplejson.load(
        urllib.request.urlopen('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json'))
    with open(f'data/{now.strftime("%Y-%m-%d-%H-%M")}.pickle', 'w') as f:
        simplejson.dump(station_status, f)
    return hello_world()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
