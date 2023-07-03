import scrapy
import logging
from scrapy.shell import inspect_response
from pymongo import MongoClient

# API_KEY = 'ff432356-cf3e-4272-a433-10bdee517657' # doesnt appear to be needed

# def get_scrapeops_url(url):
#     payload = {'api_key': API_KEY, 'url': url}
#     proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
#     return proxy_url

class ChampionListSpider(scrapy.Spider):
    name = "champion_list_spider"
    allowed_domains = ["op.gg"]
    ranks = ["gold", "platinum"]  # Add more ranks if needed
    roles = ["top", "jungle"]  # Add more roles if needed

    def start_requests(self):
        for rank in self.ranks:
            for role in self.roles:
                url = f"https://www.op.gg/champions?region=global&tier={rank}&position={role}"
                yield scrapy.Request(url=url, callback=self.parse, meta={'rank': rank, 'role': role})

    def parse(self, response):
        role = response.meta.get('role')
        rank = response.meta.get('rank')
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

        self.save_to_mongodb(role, rank, champion_list, win_rate_map)

    def save_to_mongodb(self, role, rank, champion_list, win_rate_map):
        client = MongoClient('mongodb://localhost:27017/')
        DB = client['LeaguePool']
        collection = DB["role_champion_map"]
        query = {"role": role, "rank":rank}
        document = {"role": role, "rank":rank, "champions": champion_list, "win_rate_map": win_rate_map}

        try:
            result = collection.replace_one(query, document, upsert=True)
            if result.modified_count > 0 or result.upserted_id is not None:
                logging.info(f"Champ list data saved for {role}, {rank} rank")
            else:
                logging.info(f"Champ list data for {role}, {rank} rank was up to date")
        except PyMongoError as e:
            logging.error(f"Error occurred while saving champ list data for {role}, {rank} rank: {e}")

        client.close()
