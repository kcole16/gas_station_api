from flask import render_template, jsonify, request, Flask
from flask_cors import CORS
import requests

from gas_price import get_gas_price


application = Flask(__name__)
cors = CORS(application)
DATA = {
    'safe_price_in_gwei': 40,
    'avg_block_time': 12.5,
    'wait_blocks': 5
}

@application.route('/', methods=['GET'])
def get_price():
    global DATA
    data = get_gas_price(data=DATA)
    DATA = data
    response = jsonify(data)
    return response

if __name__ == "__main__":
    application.debug = True
    application.run()
