from flask import Flask
from opgg import calc_champion_pool
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
DB = client['LeaguePool']

@app.route('/champion-pool', methods=['GET'])
def get_champion_pool():
    # Your code for calculating the champion pool
    champion_pool = calc_champion_pool(DB)

    # Return the champion pool as a JSON response
    return {'champion_pool': champion_pool}


@app.teardown_appcontext
def teardown_db(exception):
    # Close the MongoDB connection
    client.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0')  # Listen on all network interfaces
