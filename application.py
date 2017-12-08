from flask import render_template, jsonify, request, Flask
from flask_cors import CORS
import requests

from gas_price import get_gas_price


application = Flask(__name__)
cors = CORS(application)


@application.route('/', methods=['GET'])
def get_price():
    data = get_gas_price()
    response = jsonify(data)
    return response

if __name__ == "__main__":
    application.debug = True
    application.run()
