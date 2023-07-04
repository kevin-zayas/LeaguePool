import scrapy
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError

PICK_RATE_THRESHOLD = 1.0

class ChampionListSpider(scrapy.Spider):
    """
    Spider for scraping champion list and win rates from op.gg.
    """
    name = "champion_list_spider"
    allowed_domains = ["op.gg"]
    ranks = ["gold", "platinum"]  # Add more ranks if needed
    roles = ["top", "jungle"]  # Add more roles if needed

    def start_requests(self):
        """
        Generate the initial requests to scrape champion lists for each rank and role combination.
        """
        for rank in self.ranks:
            for role in self.roles:
                url = f"https://www.op.gg/champions?region=global&tier={rank}&position={role}"
                yield scrapy.Request(url=url, callback=self.parse, meta={'rank': rank, 'role': role})

    def parse(self, response):
        """
        Parse the champion list and win rates from the response.
        """
        role = response.meta.get('role')
        rank = response.meta.get('rank')
        champion_rows = response.css('.css-cym2o0.e1oulx2j6')

        champion_list = []
        win_rate_map = {}

        for row in champion_rows:
            champion_name = row.css('a > img::attr(alt)').get().lower()
            win_rate = row.xpath('../td[4]/text()').get()
            pick_rate = float(row.xpath('../td[5]/text()').get())
            if pick_rate > PICK_RATE_THRESHOLD:
                champion_list.append(champion_name)
                win_rate_map[champion_name] = win_rate
                yield {"champion": champion_name}

        self.save_to_mongodb(role, rank, champion_list, win_rate_map)

    def save_to_mongodb(self, role, rank, champion_list, win_rate_map):
        """
        Save the champion list and win rates to MongoDB.
        """
        client = MongoClient('mongodb://localhost:27017/')
        DB = client['LeaguePool']
        collection = DB["role_champion_map"]
        query = {"role": role, "rank": rank}
        document = {"role": role, "rank": rank, "champions": champion_list, "win_rate_map": win_rate_map}

        try:
            result = collection.replace_one(query, document, upsert=True)
            if result.modified_count > 0 or result.upserted_id is not None:
                logging.info(f"Champion list data saved for role: {role}, rank: {rank}")
            else:
                logging.info(f"Champion list data for role: {role}, rank: {rank} was up to date")
        except PyMongoError as e:
            logging.error(f"Error occurred while saving champion list data for role: {role}, rank: {rank}: {e}")

        client.close()
