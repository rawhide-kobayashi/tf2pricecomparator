import json
import requests
import sqlite3
import time
import db_management
import subprocess

qualities = {
    "Normal": 0,
    "Genuine": 1,
    "rarity2": 2,
    "Vintage": 3,
    "rarity3": 4,
    "Unusual": 5,
    "Unique": 6,
    "Community": 7,
    "Valve": 8,
    "Self-Made": 9,
    "customized": 10,
    "Strange": 11,
    "completed": 12,
    "Haunted": 13,
    "Collector\'s": 14,
    "Decorated Weapon": 15,
    0: "Normal",
    1: "Genuine",
    2: "rarity2",
    3: "Vintage",
    4: "rarity3",
    5: "Unusual",
    6: "Unique",
    7: "Community",
    8: "Valve",
    9: "Self-Made",
    10: "customized",
    11: "Strange",
    12: "completed",
    13: "Haunted",
    14: "Collector\'s",
    15: "Decorated Weapon",
}
craftableness = {
    "Non-Craftable": 0,
    "Craftable": 1
}

settings = json.load(open('settings.json'))

from steampy.client import SteamClient

steam_client = SteamClient(settings['API_Keys']['steam'])
steam_client.login(settings['Credentials']['username'], settings['Credentials']['password'], settings['Credentials']['steam_guard_file'])
print(steam_client.get_trade_offers_summary())
steam_client.logout()

conn = sqlite3.connect('pricesheet.db')
c = conn.cursor()

db_management.db_thread_manager()

countsofarbitrate = 0
totalcount = 0

url = 'https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key'
steam_market_keys = requests.get(url).json()

for row in c.execute('SELECT * FROM common_items'):
    print(row)
    url = 'https://backpack.tf/api/classifieds/search/v1?page_size=30&tradable=1&killstreak_tier=0&key=' + settings['API_Keys']['backpack.tf'] + '&quality=' + str(qualities[row[3]]) + '&craftable=' + str(craftableness[row[4]]) + '&item=' + row[2]
    if 'Australium' in row[2] and 'Paint' not in row[2]:
        url += '&australium=1'
    else:
        url += '&australium=-1'
    print(url)

    bp_classifieds = requests.get(url).json()

    # traverse the listings in reverse order and delete those that are from real people
    # or haven't been bumped in the last 30 minutes.
    for x in reversed(range(len(bp_classifieds['buy']['listings']))):
        if 'automatic' not in bp_classifieds['buy']['listings'][x] or bp_classifieds['buy']['listings'][x]['bump'] < time.time() - 1800:
            del bp_classifieds['buy']['listings'][x]

    for x in reversed(range(len(bp_classifieds['sell']['listings']))):
        if 'automatic' not in bp_classifieds['sell']['listings'][x] or bp_classifieds['sell']['listings'][x]['bump'] < time.time() - 1800:
            del bp_classifieds['sell']['listings'][x]

    steam_cursor = conn.cursor()

    steam_cursor.execute('SELECT * FROM steam_market_pricing WHERE market_hash_name = (?)', (row[5],))
    steam_market_price_info = steam_cursor.fetchone()

    try:
        if 'keys' not in bp_classifieds['sell']['listings'][0]['currencies']:
            if bp_classifieds['sell']['listings'][0]['currencies']['metal'] / 53.33 < ((steam_market_price_info[2] / float(steam_market_keys['median_price'].translate(str.maketrans({'$': ''})))) * 0.85):
                print('arbitrate baby')
                countsofarbitrate += 1
                print(countsofarbitrate)
            print(bp_classifieds['sell']['listings'][0]['currencies']['metal'] / 53.33)
            print((steam_market_price_info[2] / float(steam_market_keys['median_price'].translate(str.maketrans({'$': ''})))) * 0.85)
    except IndexError:
        print('no sell listings on backpack.tf')
    except TypeError:
        print('no steam market listings')

    totalcount += 1
    print(totalcount)

    time.sleep(5)

conn.close()
