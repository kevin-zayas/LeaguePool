import logging
from itertools import combinations
from pymongo import MongoClient

ROLE = "top"
RANK = "gold"

def load_role_champion_list(DB,role="top",rank="gold"):
    """
    Load the list of champions for the specified role and rank from the database.

    Returns:
        list: List of champions for the specified role.
    """
    logging.info(f"Loading champion list for {role}")
    collection = DB["role_champion_map"]
    query = {"role": role, "rank": rank}
    document = collection.find_one(query)

    if document is not None:
        return document["champions"]
    else:
        logging.warning(f"No champion list found for role: {role}, rank: {rank}")
        return []


def load_role_matchups(DB):
    """
    Load the matchup information for all champs in a specific role from the database.

    Returns:
        collection: A collection containing matchup information for all champs in a role.
    """
    logging.info(f"Loading {RANK} {ROLE} matchup information")

    collection = DB[f"{RANK}_{ROLE}_matchup_info"]
    return collection

def check_subsets(all_champions, matchup_sets, current_champion_pool, current_pool_matchups, DB):
    """
    Check subsets of champions to find complete champion pools.

    Args:
        all_champions (set): Set of all champions for the specified role.
        matchup_sets (list): List of sets representing containing good matchups for a specific champion.
        current_pool_matchups (set): Set of champions already in the champion pool.

    Returns:
        list: List of all complete champion pools.
    """
    collection = load_role_matchups(DB)
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
                # break

    logging.info(f"Suggested champ pool size: {subset_size}")

    for matchup_pool in complete_matchup_pools:
        champion_pool = []
        for matchup_set in matchup_pool:
            if matchup_set:
                query = {"good_matchups": sorted(list(matchup_set))}
                # logging.info(sorted(list(matchup_set)))
                documents = collection.find(query, {"champion": 1})
                champions = [doc["champion"] for doc in documents]
                if champions and champions[0] not in current_champion_pool:
                    combined_champ_name = " or ".join(champions)
                    champion_pool.append(combined_champ_name)

        logging.info(champion_pool)
        suggested_champ_pools.append(champion_pool)

    return suggested_champ_pools

def calc_champion_pool(DB,current_champion_pool = ["illaoi","garen"],excluded_champions = ["kayle", "varus", "rengar", "teemo", "irelia", "quinn", "akali", "vayne"]):
    """
    Calculate the champion pool based on good matchups and restrictions.

    Returns:
        list: List of champions in the calculated champion pool.
    """
    collection = load_role_matchups(DB)
    champion_set = set(load_role_champion_list(DB))

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

    pipeline = [
        {"$match": {"champion": {"$nin": excluded_champions}}},
        {"$project": {"good_matchups": 1}}
    ]
    result = collection.aggregate(pipeline)
    matchup_sets = [set(doc["good_matchups"]) for doc in result]

    complete_champ_pool = check_subsets(champion_set, matchup_sets, current_champion_pool, current_pool_matchups,DB)

    return complete_champ_pool


def get_champion_pool_summary(champion_pool=["illaoi","garen","mordekaiser","nasus"]):
    """
    Prints the good matchups and remaining champions not countered by the champion pool.

    Args:
        champion_pool (list): List of champions in the champion pool.
    """
    collection = load_role_matchups(DB)
    champs_not_countered = set(load_role_champion_list(DB))
    logging.info(f"Displaying summary for champion pool: {champion_pool}")
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


def print_champion_pool_winrates(opponent, champ_pool=["illaoi","garen","mordekaiser","nasus"]):
    """
    Prints the win rates of a champion pool against a specific opponent.

    Args:
        opponent (str): Name of the opponent champion.
        champ_pool (list): List of champions in the champion pool.
    """
    pass
    # TO DO

def check_DB(DB):
    champion_list = load_role_champion_list(DB)
    collection = load_role_matchups(DB)
    missing_data = []
    for champion in champion_list:
        punctuation = "'. "
        for char in punctuation:
            champion = champion.replace(char, '')
        query = {"champion":champion}
        document = collection.find_one(query)
        if document is not None:
            good_matchups = document["good_matchups"]
            bad_matchups = document["bad_matchups"]
            if not good_matchups and not bad_matchups:
                missing_data.append(champion)
        else:
            missing_data.append(champion)
    logging.info(missing_data)




# Example usage
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

# Connect to the MongoDB server
# client = MongoClient('mongodb://localhost:27017/')
# DB = client['LeaguePool']
# check_DB(DB)
# calc_champion_pool(DB,["illaoi"],["kayle"])
# get_champion_pool_summary()
# client.close()





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
