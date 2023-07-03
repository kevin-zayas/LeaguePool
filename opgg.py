import logging
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from itertools import combinations
from time import time
import pickle
from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient('mongodb://localhost:27017/')
DB = client['LeaguePool']

PICK_RATE_THRESHOLD = 1.0
GOOD_MATCHUP_THRESHOLD = 51.0
BAD_MATCHUP_THRESHOLD = 49.0
RANK_TIER = "gold"
ROLE_NAME = "Top"  # Should be capitalized

def web_scrape_table_rows(page_url, table_num):
    """
    Web scrape the table rows from the given URL and table number.

    Args:
        page_url (str): The URL of the webpage to scrape.
        table_num (int): The index of the table to extract rows from.

    Returns:
        list: List of table rows extracted from the webpage.
    """
    page = urlopen(page_url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    champions_set = set()
    all_tables = soup.findChildren('table')
    table = all_tables[table_num]

    table_rows = table.findChildren(['tr'])
    return table_rows

def save_role_champion_list():
    """
    Check op.gg and save the list of champions for the specified role to the database.
    """
    logging.info(f"Saving champion list for {ROLE_NAME}")
    page_url = f"https://www.op.gg/champions?region=global&tier={RANK_TIER}&position={ROLE_NAME.lower()}"
    table_rows = web_scrape_table_rows(page_url, 0)
    champion_list = []

    for row in table_rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        champion_name = cells[1].get_text()
        pick_rate = float(cells[4].get_text()[:-1])
        if pick_rate >= PICK_RATE_THRESHOLD:
            champion_list.append(champion_name.lower())

    collection = DB["role_champion_map"]
    query = {"role": ROLE_NAME.lower()}
    document = {"role": ROLE_NAME.lower(), "champions": champion_list}

    try:
        result = collection.replace_one(query, document, upsert=True)
        if result.modified_count > 0 or result.upserted_id is not None:
            logging.info(f"Champ list data saved for {ROLE_NAME}")
        else:
            logging.info(f"Champ list data for {ROLE_NAME} was up to date")
    except PyMongoError as e:
        logging.error(f"Error occurred while saving champ list data for {ROLE_NAME}: {e}")

def load_role_champion_list():
    """
    Load the list of champions for the specified role from the database.

    Returns:
        list: List of champions for the specified role.
    """
    logging.info(f"Loading champion list for {ROLE_NAME}")
    collection = DB["role_champion_map"]
    query = {"role": ROLE_NAME.lower()}
    document = collection.find_one(query)

    if document is not None:
        return document["champions"]
    else:
        logging.warning(f"No champion list found for role: {ROLE_NAME}")
        return []

def get_champ_matchups(target_champion, champion_list):
    """
    Get the list of good and matchups for the specified champion and role.

    Args:
        target_champion (str): The champion to find good matchups for.
        champion_list (list): List of champions for the specified role.

    Returns:
        tuple: tuple of lists containing champions considered as good and bad matchups for the target champion.
    """
    logging.info(f"Finding matchup info for {target_champion}")
    if target_champion == "wukong":
        target_champion = "monkeyking"
    elif target_champion == "nunu&willump":
        target_champion = "nunu"

    punctuation = "'. "
    for char in punctuation:
        target_champion = target_champion.replace(char, '')

    page_url = f'https://www.op.gg/champions/{target_champion}/{ROLE_NAME.lower()}/counters?region=global&tier={RANK_TIER}'
    table_rows = web_scrape_table_rows(page_url, 1)
    good_matchups, bad_matchups = [],[]

    for row in table_rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        win_rate_percent = float(cells[2].get_text()[:-1])
        champion = cells[1].get_text().lower()
        if champion in champion_list:
            if win_rate_percent >= GOOD_MATCHUP_THRESHOLD:
                good_matchups.append(champion)
            elif win_rate_percent <= BAD_MATCHUP_THRESHOLD:
                bad_matchups.append(champion)
    return sorted(good_matchups),sorted(bad_matchups)

def save_role_matchups():
    """
    Save the matchup information for all champs in a specific role to the database.
    """
    logging.info(f"Saving {ROLE_NAME} matchup information")
    champion_list = load_role_champion_list()

    collection = DB[f"{ROLE_NAME.lower()}_matchup_info"]

    for champion in champion_list:
        good_matchups,bad_matchups = get_champ_matchups(champion, champion_list)
        query = {"champion": champion}
        document = {"champion": champion, "good_matchups": good_matchups, "bad_matchups":bad_matchups}
        # logging.info(f"{champion}   -   {good_matchups}")
        try:
            result = collection.replace_one(query, document, upsert=True)
            if result.modified_count > 0 or result.upserted_id is not None:
                logging.info(f"Matchup data updated for {champion}")
            else:
                logging.info(f"Matchup data for {champion} was up to date")
        except PyMongoError as e:
            logging.error(f"Error occurred while saving matchup data for {champion}: {e}")


def load_role_matchups():
    """
    Load the matchup information for all champs in a specific role from the database.

    Returns:
        collection: A collection containing matchup information for all champs in a role.
    """
    logging.info(f"Loading {ROLE_NAME} matchup information")

    collection = DB[f"{ROLE_NAME.lower()}_matchup_info"]
    return collection       #may delete this method

def check_subsets(all_champions, matchup_sets, current_pool_matchups):
    """
    Check subsets of champions to find complete champion pools.

    Args:
        all_champions (set): Set of all champions for the specified role.
        matchup_sets (list): List of sets representing containing good matchups for a specific champion.
        current_pool_matchups (set): Set of champions already in the champion pool.

    Returns:
        list: List of all complete champion pools.
    """
    collection = load_role_matchups()
    suggested_champ_pools = []
    complete_matchup_pools = []
    subset_size = 0
    is_found = False
    while not is_found:
        # Get all combinations of matchup_sets of size 'subset_size'
        subset_size += 1
        matchup_combos = list(combinations(matchup_sets, subset_size))
        for combo in matchup_combos:
            combo = combo + (current_pool_matchups,)
            union_set = set.union(*combo)
            if union_set.issuperset(all_champions):
                complete_matchup_pools.append(combo)
                is_found = True

    logging.info(f"Suggested champ pool size: {subset_size}")
    for matchup_pool in complete_matchup_pools:
        champion_pool = []
        for matchup_set in matchup_pool:
            query = {"good_matchups": sorted(list(matchup_set))}
            documents = collection.find(query, {"champion": 1})
            champions = [doc["champion"] for doc in documents]
            if champions:
                combined_champ_name = " or ".join(champions)
                champion_pool.append(combined_champ_name)

        logging.info(champion_pool)
        suggested_champ_pools.append(champion_pool)

    return suggested_champ_pools

def calc_champion_pool():
    """
    Calculate the champion pool based on good matchups and restrictions.

    Returns:
        list: List of champions in the calculated champion pool.
    """
    collection = load_role_matchups()
    champion_set = set(load_role_champion_list())

    current_champion_pool = ["illaoi","garen","mordekaiser","nasus"]
    current_pool_matchups = []
    logging.info(f"Current champion pool: {current_champion_pool}")

    if current_champion_pool:
        for champion in current_champion_pool:
            query = {"champion":champion}
            matchups = collection.find_one(query,{"good_matchups":1})
            current_pool_matchups.append(set(matchups["good_matchups"]))

        current_pool_matchups = set.union(*current_pool_matchups)
        if current_pool_matchups.issuperset(champion_set):
            logging.info(f"Current champion pool covers all champions: {current_champion_pool}")
            return current_champion_pool

    excluded_champions = ["kayle", "varus", "rengar", "teemo", "irelia", "quinn", "akali", "vayne"]
    pipeline = [
        {"$match": {"champion": {"$nin": excluded_champions}}},
        {"$project": {"good_matchups": 1}}
    ]
    result = collection.aggregate(pipeline)
    matchup_sets = [set(doc["good_matchups"]) for doc in result]

    complete_champ_pool = current_champion_pool+check_subsets(champion_set, matchup_sets, current_pool_matchups)[0]
    # get_champion_pool_summary(complete_champ_pool)

def refresh():
    """
    Refreshes the role champion set and role counters.
    """
    save_role_champion_list()
    save_role_matchups()
    logging.info("Refresh completed")

def get_champion_pool_summary(champion_pool=["illaoi","garen","mordekaiser","nasus"]):
    """
    Prints the good matchups and remaining champions not countered by the champion pool.

    Args:
        champion_pool (list): List of champions in the champion pool.
    """
    collection = load_role_matchups()
    champs_not_countered = set(load_role_champion_list())
    for champion in champion_pool:
        query = {"champion":champion}
        document = collection.find_one(query)
        good_matchups,bad_matchups = document["good_matchups"],document["bad_matchups"]

        logging.info(f"\n\n{champion}'s good matchups: {good_matchups}\n")
        # logging.info(f"\n{champion}'s bad matchups: {bad_matchups}\n\n")
        champs_not_countered = champs_not_countered - set(good_matchups)

    if len(champs_not_countered) != 0:
        logging.info(f"\nChampions not countered: {champs_not_countered}")
        for champion in champs_not_countered:
            query = {"champion":champion}
            document = collection.find_one(query)
            bad_matchups = document["bad_matchups"]
            logging.info(f"\n\n{champion}'s bad matchups: {bad_matchups}\n")

def print_champion_pool_winrates(champ_pool = ["illaoi","garen","mordekaiser","nasus"], opponent):
    # TO DO




# Example usage
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
refresh()
calc_champion_pool()
get_champion_pool_summary()

client.close()


#after generating the list of possible champ pool additions, filter through and only take the x with the highest winrate/rank? lowest banrate?
    #Can do this by storing each champ and their win rate in role_champion_map
    #Since we are already checking pickrate, checking and storing this wont be much extra work

#go through champ pool and for each champ, list off which champs they have the highest winrate compared to the rest of the pool
    #This would require storing matchup percentages so it would make sense to store this when storing matchup data
    #**if we store matchup data, when we want to find champ_pool win rates against an enemy, we can just look at their matchup pools
        #If its an off-meta pick (not in the DB) we can webscrape

#input enemy champ and tell you the champ to play based on the highest winrate in your pool
    #can just webscrape that champs matchups and return the highest from pool
    #**Or store the matchup percentages for each champ
