from flask import Flask
from flask import request
from opgg import calc_champion_pool
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/champion-pool', methods=['GET'])
def get_champion_pool():
    client = MongoClient('mongodb://localhost:27017/')
    DB = client['LeaguePool']

    current_champions = request.args.get('current_champions')
    if current_champions:
        current_champions = current_champions.split(',')
    else:
        current_champions = []

    exclude_champions = request.args.get('exclude_champions')
    if exclude_champions:
        exclude_champions = current_champions.split(',')
    else:
        exclude_champions = []

    champion_pool = calc_champion_pool(DB, current_champions,exclude_champions)
    client.close()
    return {'champion_pool': champion_pool}     # Return the champion pool as a JSON response



if __name__ == '__main__':
    app.run(host='0.0.0.0')  # Listen on all network interfaces
