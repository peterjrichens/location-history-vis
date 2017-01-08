# -*- coding: utf-8 -*-

import json

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_data():
    with open('input/location_sample.json') as data_file:
        return json.load(data_file)

if __name__ == "__main__":
    app.run(debug=True)