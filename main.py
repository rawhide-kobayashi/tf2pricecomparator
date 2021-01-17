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
            craftability text NOT NULL)''')

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
                    c.execute('INSERT OR REPLACE INTO common_items VALUES (?,?,?,?,?)', (sku, defindex, item_name, qualities[int(quality)], craftability))

conn.commit()

countsofarbitrate = 0

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

    if row[3] == 'Unique':
        url = 'https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=' + row[2]
    else:
        url = 'https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=' + row[3] + ' ' + row[2]
    print(url)

    json_transient = requests.get(url)
    steam_market = json_transient.json()
    del json_transient

    url = 'https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key'
    json_transient = requests.get(url)
    steam_market_keys = json_transient.json()
    del json_transient

    try:
        if steam_market['success'] == True and 'keys' not in bp_classifieds['sell']['listings'][0]['currencies']:
            if bp_classifieds['sell']['listings'][0]['currencies']['metal'] / 53.11 < ((float(steam_market['median_price'].translate(str.maketrans({'$': ''}))) / float(steam_market_keys['median_price'].translate(str.maketrans({'$': ''})))) * 0.85):
                print('arbitrate baby')
                countsofarbitrate += 1
                print(countsofarbitrate)
            print(bp_classifieds['sell']['listings'][0]['currencies']['metal'] / 53.11)
            print((float(steam_market['median_price'].translate(str.maketrans({'$': ''}))) / float(steam_market_keys['median_price'].translate(str.maketrans({'$': ''})))) * 0.85)
    except IndexError:
        print('no sell listings')
    except KeyError:
        print('not enough volume on the steam marketplace')

    time.sleep(10)


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