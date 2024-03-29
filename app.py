from flask import Flask, render_template, request
from opgg import calc_champion_pool,load_role_champion_list
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/champion-pool', methods=['GET'])
def get_champion_pool():
    # client = MongoClient('mongodb://localhost:27017/')
    client = MongoClient('mongodb://3.145.60.140:27017/')
    DB = client['LeaguePool']

    current_champions = request.args.get('current_champions')
    if current_champions:
        current_champions = current_champions.split(',')
    else:
        current_champions = []

    exclude_champions = request.args.get('exclude_champions')
    if exclude_champions:
        exclude_champions = exclude_champions.split(',')
    else:
        exclude_champions = []

    champion_pools = calc_champion_pool(DB, current_champions,exclude_champions)
    client.close()
    return {'champion_pools': champion_pools}     # Return the champion pool as a JSON response

@app.route('/champion-list', methods=['GET'])
def get_champion_list():
    client = MongoClient('mongodb://localhost:27017/')
    DB = client['LeaguePool']

    role = request.args.get('role')

    champion_list = load_role_champion_list(DB, role)
    client.close()
    return {'champion_list': champion_list}     # Return the champion list as a JSON response



if __name__ == '__main__':
    app.run(host='0.0.0.0')  # Listen on all network interfaces
