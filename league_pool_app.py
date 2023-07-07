from flask import Flask
from opgg import calc_champion_pool
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
DB = client['LeaguePool']

@app.route('/champion-pool', methods=['GET'])
def get_champion_pool():
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
    return {'champion_pool': champion_pool}     # Return the champion pool as a JSON response


@app.teardown_appcontext
def teardown_db(exception):
    # Close the MongoDB connection
    client.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0')  # Listen on all network interfaces
