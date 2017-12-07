from flask import render_template, jsonify, request, Flask
from flask_cors import CORS
from dateutil import parser
import requests

from gas_price import get_gas_price


application = Flask(__name__)
application.debug = True
cors = CORS(application)


@application.route('/getPrice', methods=['GET'])
def get_price():
    data = get_gas_price()
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


if __name__ == "__main__":
    application.debug = True
    application.run()
