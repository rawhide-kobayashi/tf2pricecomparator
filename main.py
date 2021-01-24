import json
import requests
import sqlite3
import time

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

# import test json file
with open('test data set.json') as json_transient:
    bp_spreadsheet = json.load(json_transient)
    del json_transient

with open('settings.json') as json_transient:
    settings = json.load(json_transient)
    del json_transient

# url = 'https://backpack.tf/api/IGetPrices/v4?key=' + settings['API_Keys']['backpack.tf']

# json_transient = requests.get(url)
# bp_spreadsheet = json_transient.json()
# del json_transient

conn = sqlite3.connect('pricesheet.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS common_items (
            sku text PRIMARY KEY,
            defindex integer NOT NULL,
            item_name text NOT NULL,
            quality text NOT NULL,
            craftability text NOT NULL,
            market_hash_name text NOT NULL)''')

# iterate through the relevant fields in bp.tf's spreadsheet to make a basic catalog of commonly traded items.
for keys in bp_spreadsheet['response']['items']:
    item_name = keys
    for x in bp_spreadsheet['response']['items'][item_name]['defindex']:
        # ignores tough break reskins and default weapons present in this dataset.
        if len(bp_spreadsheet['response']['items'][item_name]['defindex']) == 1 or (35 <= x < 15000):
            defindex = x
            for values in bp_spreadsheet['response']['items'][item_name]['prices']:
                quality = values
                # noinspection PyAssignmentToLoopOrWithParameter
                for keys in bp_spreadsheet['response']['items'][item_name]['prices'][quality]['Tradable']:
                    craftability = keys
                    if craftability == 'Craftable':
                        sku = str(defindex) + ';' + quality
                    else:
                        sku = str(defindex) + ';' + quality + ';uncraftable'
                    if qualities[int(quality)] == 'Unique' or qualities[int(quality)] == 'Normal' or qualities[int(quality)] == 'rarity3':
                        market_hash_name = item_name
                    else:
                        # noinspection PyTypeChecker
                        market_hash_name = qualities[int(quality)] + ' ' + item_name
                    print(market_hash_name)
                    c.execute('INSERT OR REPLACE INTO common_items VALUES (?,?,?,?,?,?)', (sku, defindex, item_name, qualities[int(quality)], craftability, market_hash_name))

conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS steam_market_pricing (
            market_hash_name text PRIMARY KEY,
            quantity integer NOT NULL,
            lowest_price float NOT NULL,
            last_updated integer NOT NULL)''')
'''
wheretostart = 0

url = 'https://steamcommunity.com/market/search/render/?search_descriptions=0&sort_column=name&sort_dir=asc&norender=1&count=100&category_440_Collection%5B0%5D=any&category_440_Quality%5B0%5D=tag_Unique&category_440_Quality%5B1%5D=tag_strange&category_440_Quality%5B2%5D=tag_vintage&category_440_Quality%5B3%5D=tag_rarity1&category_440_Quality%5B4%5D=tag_haunted&category_440_Quality%5B5%5D=tag_collectors&appid=440&start=' + str(wheretostart)
json_transient = requests.get(url)
steam_market_listings = json_transient.json()
del json_transient

while len(steam_market_listings['results']) > 0:
    for x in range(len(steam_market_listings['results'])):
        c.execute('INSERT OR REPLACE INTO steam_market_pricing VALUES (?,?,?,?)', (steam_market_listings['results'][x]['hash_name'], steam_market_listings['results'][x]['sell_listings'], steam_market_listings['results'][x]['sell_price_text'].translate(str.maketrans({'$': ''})), int(time.time())))

    conn.commit()
    wheretostart += 100
    time.sleep(30)
    print(wheretostart)

    url = 'https://steamcommunity.com/market/search/render/?search_descriptions=0&sort_column=name&sort_dir=asc&norender=1&count=100&category_440_Collection%5B0%5D=any&category_440_Quality%5B0%5D=tag_Unique&category_440_Quality%5B1%5D=tag_strange&category_440_Quality%5B2%5D=tag_vintage&category_440_Quality%5B3%5D=tag_rarity1&category_440_Quality%5B4%5D=tag_haunted&category_440_Quality%5B5%5D=tag_collectors&appid=440&start=' + str(wheretostart)
    json_transient = requests.get(url)
    steam_market_listings = json_transient.json()
    del json_transient
'''
countsofarbitrate = 0
totalcount = 0

url = 'https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key'
json_transient = requests.get(url)
steam_market_keys = json_transient.json()
del json_transient

for row in c.execute('SELECT * FROM common_items'):
    print(row)
    url = 'https://backpack.tf/api/classifieds/search/v1?page_size=30&tradable=1&killstreak_tier=0&key=' + settings['API_Keys']['backpack.tf'] + '&quality=' + str(qualities[row[3]]) + '&craftable=' + str(craftableness[row[4]]) + '&item=' + row[2]
    if 'Australium' in row[2] and 'Paint' not in row[2]:
        url += '&australium=1'
    else:
        url += '&australium=-1'
    print(url)

    json_transient = requests.get(url)
    bp_classifieds = json_transient.json()
    del json_transient

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


import base64
import hmac
import struct
from hashlib import sha1


# magical bullshit that i don't understand, but you get a guard code
time_hmac = hmac.new(base64.b64decode(settings['Steam_Guard']['shared_secret']), struct.pack('>Q', int(time.time()) // 30), digestmod=sha1).digest()
ordered = ord(time_hmac[19:20]) & 0xf
full_code = struct.unpack('>I', time_hmac[ordered:ordered + 4])[0] & 0x7fffffff
chars = '23456789BCDFGHJKMNPQRTVWXY'
code = ''

for _ in range(5):
    full_code, i = divmod(full_code, len(chars))
    code += chars[i]

print(code)
