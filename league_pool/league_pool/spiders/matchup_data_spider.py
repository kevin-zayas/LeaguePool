import scrapy
import logging
from scrapy.shell import inspect_response
from pymongo import MongoClient
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver

GOOD_MATCHUP_THRESHOLD = 51.0
BAD_MATCHUP_THRESHOLD = 49.0


class MatchupDataSpider(scrapy.Spider):
    name = "matchup_data_spider"
    allowed_domains = ["op.gg"]
    ranks = ["platinum"]  # Add more ranks if needed
    roles = ["top"]  # Add more roles if needed
    chanmpion_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run Chrome in headless mode
        self.driver = webdriver.Chrome(options=options)

    def start_requests(self):
        for rank in self.ranks:
            for role in self.roles:
                self.champion_list = self.load_role_champion_list(role,rank)
                for champion in self.champion_list:
                    logging.info(f"Finding matchup info for {champion}")
                    champion = self.filter_champion_name(champion)

                    url = f'https://www.op.gg/champions/{champion}/{role}/counters?region=global&tier={rank}'
                    print("url:",url)
                    yield scrapy.Request(url=url, callback=self.parse, meta={'rank': rank, 'role': role, 'champion':champion})
                    # break

    def parse(self, response):
        role = response.meta.get('role')
        rank = response.meta.get('rank')
        champion = response.meta.get('champion')
        print(len(self.champion_list))

        self.driver.get(response.url)
        body = self.driver.page_source
        response = HtmlResponse(url=response.url, body=body, encoding='utf-8')
        matchup_rows = response.css('.css-12a3bv1.eocu2m74')

        good_matchups,bad_matchups = [],[]
        matchup_win_rate_map = {}
        for row in matchup_rows:
            champion_name = row.xpath('.//td[2]//div/text()').get().lower()
            win_rate = float(row.xpath('.//td[3]//span/text()').get())

            if champion_name in self.champion_list:
                if win_rate >= GOOD_MATCHUP_THRESHOLD:
                    good_matchups.append(champion_name)
                elif win_rate <= BAD_MATCHUP_THRESHOLD:
                    bad_matchups.append(champion_name)

                matchup_win_rate_map[champion_name] = win_rate

                # yield {
                #     'champion': champion_name,
                #     'win_rate': win_rate,
                # }

        self.save_to_mongodb(role, rank, champion, good_matchups, bad_matchups, matchup_win_rate_map)

    def save_to_mongodb(self, role, rank, champion, good_matchups, bad_matchups, matchup_win_rate_map):
        client = MongoClient('mongodb://localhost:27017/')
        DB = client['LeaguePool']
        collection = DB[f"{rank}_{role}_matchup_info"]
        query = {"champion": champion}
        document = {"champion": champion, "good_matchups": good_matchups,"bad_matchups": bad_matchups, "matchup_win_rate_map": matchup_win_rate_map}

        try:
            result = collection.replace_one(query, document, upsert=True)
            if result.modified_count > 0 or result.upserted_id is not None:
                logging.info(f"{champion} matchup data saved for {role}, {rank} rank")
            else:
                logging.info(f"{champion} matchup data for {role}, {rank} rank was up to date")
        except PyMongoError as e:
            logging.error(f"Error occurred while saving {champion} matchup data for {role}, {rank} rank: {e}")

        client.close()

    def load_role_champion_list(self, role, rank):
        """
        Load the list of champions for the specified role and rank from the database.

        Returns:
            list: List of champions for the specified role and rank.
        """
        logging.info(f"Loading champion list for {role}, {rank} rank")
        client = MongoClient('mongodb://localhost:27017/')
        DB = client['LeaguePool']
        collection = DB["role_champion_map"]
        query = {"role": role, "rank":rank}
        document = collection.find_one(query)
        client.close()

        if document is not None:
            return document["champions"]
        else:
            logging.warning(f"No champion list found for role: {role}")
            return []

    def filter_champion_name(self,champion):
        """
        Changes the input champion name to a format suited for the op.gg url
        """

        if champion == "wukong":
            champion = "monkeyking"
        elif champion == "nunu&willump":
            champion = "nunu"

        punctuation = "'. "
        for char in punctuation:
            champion = champion.replace(char, '')
        return champion
