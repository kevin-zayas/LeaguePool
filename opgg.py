from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from itertools import combinations
from time import time
import pickle

PickRateThreshHold = 1.0
WinRateThreshold = 50.0
Rank = "gold"
Role = "Top" #Should be capitalized

def webScrapeTableRows(url,table_num):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    champs = set()
    tables = soup.findChildren('table')
    table = tables[table_num]

    rows = table.findChildren(['tr'])
    return rows

def saveRoleChampSet():
    print("saving role champ set")
    url = "https://www.op.gg/champions?region=global&tier={}&position={}".format(Rank,Role.lower())
    rows = webScrapeTableRows(url,0)
    champs = set()

    for row in rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        champ = cells[1].get_text()
        percent = float(cells[4].get_text()[:-1])
        if percent >= PickRateThreshHold:
            champs.add(champ.lower())

    with open('{}.txt'.format(Role),'wb') as f:
        pickle.dump(champs, f)

def loadRoleChampSet():
    print("loading role champ set")
    with open('{}.txt'.format(Role),'rb') as f:
        champs = pickle.load(f)
    return champs

def getGoodMatchups(target_champ,champ_set):
    if target_champ == "wukong":
        target_champ = "monkeyking"
    elif target_champ == "nunu&willump":
        target_champ = "nunu"
    print("finding matchup info for "+target_champ)
    url = 'https://www.op.gg/champions/{}/{}/counters?region=global&tier={}'.format(target_champ,Role.lower(),Rank)
    rows = webScrapeTableRows(url,1)
    good_matchups = []

    for row in rows:
        cells = row.findChildren('td')
        if not cells:
            continue
        percent = float(cells[2].get_text()[:-1])
        champ = cells[1].get_text().lower()
        if percent >= WinRateThreshold and champ in champ_set:
            good_matchups.append(champ)
    return frozenset(good_matchups)

def saveRoleCounters():
    print("saving role counters")
    champ_set = loadRoleChampSet()
    champ_counters = {}
    counter_map = {}
    punctuation = "'. "
    for champ in champ_set:
        for char in punctuation:
            champ = champ.replace(char,'')
        matchup_list = getGoodMatchups(champ,champ_set)
        champ_counters[champ]= matchup_list
        if matchup_list not in counter_map:
            counter_map[matchup_list]=champ
        else:
            raise Exception(champ +" and "+ counter_map[matchup_list] +" have the same Counter Set")
            break

    with open('{}ChampCounters.txt'.format(Role),'wb') as f:
        pickle.dump(champ_counters, f)

    with open('{}CounterMap.txt'.format(Role),'wb') as f:
        pickle.dump(counter_map, f)

def loadRoleCounters():
    print("loading role counters")

    with open('{}ChampCounters.txt'.format(Role),'rb') as f:
        champ_counters = pickle.load(f)

    with open('{}CounterMap.txt'.format(Role),'rb') as f:
        counter_map = pickle.load(f)

    return champ_counters, counter_map

def checkSubsets(all_champs, subsets, champ_pool_counters, counter_map):
        all_champ_pools = []
        complete_subsets = []
        n = 1
        pool = []
        found = False
        while not found:
            # Get all combinations of n subsets
            subset_combos = list(combinations(subsets, n))
            # print("checking subsets of size: ", n)
            for combo in subset_combos:
                combo= combo +(champ_pool_counters,)
                u = frozenset.union(*combo)
                if u == all_champs:
                    complete_subsets.append(combo)
                    found = True
            # Add one more subset
            n += 1
        for pool in complete_subsets:
            champ_pool = []
            for champ in pool:
                try:
                    champ_pool.append(counter_map[champ])
                except KeyError:
                    pass
            print(champ_pool)
            all_champ_pools.append(champ_pool)
        return all_champ_pools

def calcChampPool():
    champ_counters,counter_map = loadRoleCounters()
    subsets = counter_map.keys()
    all_champs = loadRoleChampSet()

    restricted_champs = ["kayle","varus", "rengar", "teemo", "irelia"]
    for i in range(len(restricted_champs)):
        print("removing " + restricted_champs[i] + " from possible champ pool")
        restricted_champs[i] = champ_counters[restricted_champs[i]]

    subsets = subsets - restricted_champs

    champ_pool = ["drmundo", "ornn", "nasus"]
    champ_pool_counters = []
    for champ in champ_pool:
        champ_pool_counters.append(champ_counters[champ])
    print("\nCurrent champ pool:",champ_pool)
    champ_pool_counters = frozenset.union(*champ_pool_counters)
    if len(champ_pool_counters) == len(all_champs):
        print("current champ pool covers all champs:",champ_pool)
        return champ_pool

    checkSubsets(all_champs, subsets, champ_pool_counters, counter_map)

    return champ_pool

def refresh():
    saveRoleChampSet()
    saveRoleCounters()


def getChampPoolSummary(champ_pool=["drmundo", "ornn", "nasus"]):
    champ_counters, counter_map = loadRoleCounters()
    all_champs = loadRoleChampSet()
    for champ in champ_pool:
        counters = champ_counters[champ]
        print("\n" + champ + "'s good matchups: ", sorted(list(counters)))
        all_champs = all_champs - counters
    if len(all_champs) != 0:
        print("\n Champs not countered: ", all_champs)

refresh()
# calcChampPool()
getChampPoolSummary()

#after generating the list of possible champ pool additions, filter through and only take the x with the highest winrate/rank? lowest banrate?

#go through champ pool and for each champ, list off which champs they have the highest winrate out of the rest of the pool

#input enemy champ and tell you the champ to play based on the highest winrate in your pool
    #can just webscrape that champs matchups and return the highest from pool
