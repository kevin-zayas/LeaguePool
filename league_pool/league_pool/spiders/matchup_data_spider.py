import scrapy
import logging
from scrapy.shell import inspect_response
from pymongo import MongoClient


ROLES = ["top"]  # Add more roles if needed

class MatchupDataSpider(scrapy.Spider):
    name = "matchup_data_spider"
    allowed_domains = ["op.gg"]  # Specify the allowed domains to crawl
    start_urls = [f"https://www.op.gg/champions?region=global&tier=gold&position={role}" for role in ROLES]  # Specify the starting URL(s) for the spider

    def parse(self, response):
        role_name = response.url.split("position=")[-1]  # Extract the role name from the URL
        champion_rows = response.css('.css-cym2o0.e1oulx2j6')
        champion_list = []
        win_rate_map = {}

        for row in champion_rows:
            champion_name = row.css('a > img::attr(alt)').get()
            win_rate = row.xpath('../td[4]/text()').get()
            pick_rate = float(row.xpath('../td[5]/text()').get())
            if pick_rate > 1.0:
                champion_list.append(champion_name)
                win_rate_map[champion_name] = win_rate
                # yield {"champion":champion_name}

        self.save_to_mongodb(role_name, champion_list, win_rate_map)

    def save_to_mongodb(self, role_name, champion_list, win_rate_map):
        client = MongoClient('mongodb://localhost:27017/')
        DB = client['LeaguePool']
        collection = DB["role_champion_map"]
        query = {"role": role_name}
        document = {"role": role_name, "champions": champion_list, "win_rate_map": win_rate_map}

        try:
            result = collection.replace_one(query, document, upsert=True)
            if result.modified_count > 0 or result.upserted_id is not None:
                logging.info(f"Champ list data saved for {role_name}")
            else:
                logging.info(f"Champ list data for {role_name} was up to date")
        except PyMongoError as e:
            logging.error(f"Error occurred while saving champ list data for {role_name}: {e}")

        client.close()
