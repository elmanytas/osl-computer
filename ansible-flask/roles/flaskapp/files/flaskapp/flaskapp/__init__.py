from flask import Flask
from flask import request
from flask import json

import requests

app = Flask(__name__)


# http://blog.luisrei.com/articles/flaskrest.html
@app.route('/oslh2b', methods = ['POST'])
def oslh2b():
    if request.method == 'POST':

        json_headers = request.headers
        data = json.loads(request.data)

        destination_url = data["destination_url"]
        data.pop("destination_url", None)
        json_data = json.dumps(data) 

        r = requests.post(destination_url, data=json_data, headers=json_headers)
	data = {}
        data["body"] = json.loads(r.text)
	data["headers"] = r.headers

        return str(data)


if __name__ == '__main__':
    app.run()
