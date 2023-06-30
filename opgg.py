import logging
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from itertools import combinations
from time import time
import pickle

PICK_RATE_THRESHOLD = 1.0
WIN_RATE_THRESHOLD = 50.0
RANK_TIER = "gold"
ROLE_NAME = "Top"  # Should be capitalized

def web_scrape_table_rows(page_url, table_num):
    page = urlopen(page_url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    champions_set = set()
    all_tables = soup.findChildren('table')
    table = all_tables[table_num]

    table_rows = table.findChildren(['tr'])
    return table_rows

def save_role_champion_set():
    logging.info("Saving role champion set")
    page_url = f"https://www.op.gg/champions?region=global&tier={RANK_TIER}&position={ROLE_NAME.lower()}"
    table_rows = web_scrape_table_rows(page_url, 0)
    champions_set = set()

    for row in table_rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        champion_name = cells[1].get_text()
        win_rate_percent = float(cells[4].get_text()[:-1])
        if win_rate_percent >= PICK_RATE_THRESHOLD:
            champions_set.add(champion_name.lower())

    with open(f'{ROLE_NAME}.txt', 'wb') as f:
        pickle.dump(champions_set, f)

def load_role_champion_set():
    logging.info("Loading role champion set")
    with open(f'{ROLE_NAME}.txt', 'rb') as f:
        champions_set = pickle.load(f)
    return champions_set

def get_good_matchups(target_champion, champion_set):
    if target_champion == "wukong":
        target_champion = "monkeyking"
    elif target_champion == "nunu&willump":
        target_champion = "nunu"
    logging.info(f"Finding matchup info for {target_champion}")
    page_url = f'https://www.op.gg/champions/{target_champion}/{ROLE_NAME.lower()}/counters?region=global&tier={RANK_TIER}'
    table_rows = web_scrape_table_rows(page_url, 1)
    good_matchups = []

    for row in table_rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        win_rate_percent = float(cells[2].get_text()[:-1])
        champion = cells[1].get_text().lower()
        if win_rate_percent >= WIN_RATE_THRESHOLD and champion in champion_set:
            good_matchups.append(champion)
    return frozenset(good_matchups)

def save_role_counters():
    logging.info("Saving role counters")
    champion_set = load_role_champion_set()
    champion_counters = {}
    matchup_counter_map = {}
    punctuation = "'. "
    for champion in champion_set:
        for char in punctuation:
            champion = champion.replace(char, '')
        matchup_list = get_good_matchups(champion, champion_set)
        champion_counters[champion] = matchup_list
        if matchup_list not in matchup_counter_map:
            matchup_counter_map[matchup_list] = champion
        else:
            raise Exception(f"{champion} and {matchup_counter_map[matchup_list]} have the same Counter Set")
            break

    with open(f'{ROLE_NAME}ChampCounters.txt', 'wb') as f:
        pickle.dump(champion_counters, f)

    with open(f'{ROLE_NAME}CounterMap.txt', 'wb') as f:
        pickle.dump(matchup_counter_map, f)

def load_role_counters():
    logging.info("Loading role counters")

    with open(f'{ROLE_NAME}ChampCounters.txt', 'rb') as f:
        champion_counters = pickle.load(f)

    with open(f'{ROLE_NAME}CounterMap.txt', 'rb') as f:
        matchup_counter_map = pickle.load(f)

    return champion_counters, matchup_counter_map

def check_subsets(all_champions, subsets, champion_pool_counters, counter_map):
    all_champion_pools = []
    complete_subsets = []
    subset_size = 1
    current_pool = []
    is_found = False
    while not is_found:
        # Get all combinations of subsets of size 'subset_size'
        subset_combos = list(combinations(subsets, subset_size))
        for combo in subset_combos:
            combo = combo + (champion_pool_counters,)
            union_set = frozenset.union(*combo)
            if union_set == all_champions:
                complete_subsets.append(combo)
                is_found = True
        subset_size += 1
    for current_pool in complete_subsets:
        champion_pool = []
        for matchup in current_pool:
            try:
                champion_pool.append(counter_map[matchup])
            except KeyError:
                pass
        logging.info(champion_pool)
        all_champion_pools.append(champion_pool)
    return all_champion_pools

def calc_champion_pool():
    champion_counters, counter_map = load_role_counters()
    subsets = counter_map.keys()
    all_champions = load_role_champion_set()

    restricted_champions = ["kayle", "varus", "rengar", "teemo", "irelia"]
    for i in range(len(restricted_champions)):
        logging.info(f"Removing {restricted_champions[i]} from possible champion pool")
        restricted_champions[i] = champion_counters[restricted_champions[i]]

    subsets = subsets - restricted_champions

    champion_pool = ["illaoi", "garen"]
    champion_pool_counters = []
    for champion in champion_pool:
        champion_pool_counters.append(champion_counters[champion])
    logging.info(f"\nCurrent champion pool: {champion_pool}")
    champion_pool_counters = frozenset.union(*champion_pool_counters)
    if len(champion_pool_counters) == len(all_champions):
        logging.info(f"Current champion pool covers all champions: {champion_pool}")
        return champion_pool

    check_subsets(all_champions, subsets, champion_pool_counters, counter_map)

    return champion_pool

def refresh():
    """
    Refreshes the role champion set and role counters.
    """
    save_role_champion_set()
    save_role_counters()
    logging.info("Refresh completed")

def get_champion_pool_summary(champion_pool=["drmundo", "ornn", "nasus"]):
    """
    Prints the good matchups and remaining champions not countered by the champion pool.
    """
    champion_counters, counter_map = load_role_counters()
    all_champions = load_role_champion_set()
    for champion in champion_pool:
        counters = champion_counters[champion]
        logging.info(f"\n{champion}'s good matchups: {sorted(list(counters))}")
        all_champions = all_champions - counters
    if len(all_champions) != 0:
        logging.info(f"\nChampions not countered: {all_champions}")


# Example usage
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
refresh()
calc_champion_pool()


#after generating the list of possible champ pool additions, filter through and only take the x with the highest winrate/rank? lowest banrate?

#go through champ pool and for each champ, list off which champs they have the highest winrate out of the rest of the pool

#input enemy champ and tell you the champ to play based on the highest winrate in your pool
    #can just webscrape that champs matchups and return the highest from pool
