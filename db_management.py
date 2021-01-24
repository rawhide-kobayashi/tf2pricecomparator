import requests
import sqlite3
import json
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

with open('settings.json') as json_transient:
    settings = json.load(json_transient)

def update_common_items_list():
    conn = sqlite3.connect('pricesheet.db')
    c = conn.cursor()
    c.execute('SELECT name FROM sqlite_master WHERE type="table"')
    if c.fetchone() is None:
        c.execute('''CREATE TABLE common_items (
                    sku text PRIMARY KEY,
                    defindex integer NOT NULL,
                    item_name text NOT NULL,
                    quality text NOT NULL,
                    craftability text NOT NULL,
                    market_hash_name text NOT NULL,
                    last_updated integer NOT NULL)''')
        c.execute('''CREATE TABLE steam_market_pricing (
                    market_hash_name text PRIMARY KEY,
                    quantity integer NOT NULL,
                    lowest_price float NOT NULL,
                    last_updated integer NOT NULL)''')
        c.execute('INSERT INTO common_items VALUES ("5021;6", 5021, "Mann Co. Supply Crate Key", "Unique", "Craftable", "Mann Co. Supply Crate Key", 0000000000)')
        conn.commit()

    c.execute('SELECT max("last_updated") FROM common_items')
    last_updated = c.fetchone()

    url = 'https://backpack.tf/api/IGetPrices/v4?key=' + settings['API_Keys']['backpack.tf'] + '&since=' + str(last_updated[0])

    json_transient = requests.get(url)
    bp_spreadsheet = json_transient.json()

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
                        if 'Australium' in item_name:
                            sku += ';australium'
                        c.execute('INSERT OR REPLACE INTO common_items VALUES (?,?,?,?,?,?,?)', (sku, defindex, item_name, qualities[int(quality)], craftability, market_hash_name, int(time.time())))

    conn.commit()

def update_steam_market_pricelist():
    conn = sqlite3.connect('pricesheet.db')
    c = conn.cursor()

    wheretostart = 0

    url = 'https://steamcommunity.com/market/search/render/?search_descriptions=0&sort_column=name&sort_dir=asc&norender=1&count=100&category_440_Collection%5B0%5D=any&category_440_Quality%5B0%5D=tag_Unique&category_440_Quality%5B1%5D=tag_strange&category_440_Quality%5B2%5D=tag_vintage&category_440_Quality%5B3%5D=tag_rarity1&category_440_Quality%5B4%5D=tag_haunted&category_440_Quality%5B5%5D=tag_collectors&appid=440&start=' + str(wheretostart)
    json_transient = requests.get(url)
    steam_market_listings = json_transient.json()

    while len(steam_market_listings['results']) > 0:
        for x in range(len(steam_market_listings['results'])):
            c.execute('INSERT OR REPLACE INTO steam_market_pricing VALUES (?,?,?,?)', (steam_market_listings['results'][x]['hash_name'], steam_market_listings['results'][x]['sell_listings'], steam_market_listings['results'][x]['sell_price_text'].translate(str.maketrans({'$': ''})), int(time.time())))

        conn.commit()
        wheretostart += 100
        time.sleep(30)

        url = 'https://steamcommunity.com/market/search/render/?search_descriptions=0&sort_column=name&sort_dir=asc&norender=1&count=100&category_440_Collection%5B0%5D=any&category_440_Quality%5B0%5D=tag_Unique&category_440_Quality%5B1%5D=tag_strange&category_440_Quality%5B2%5D=tag_vintage&category_440_Quality%5B3%5D=tag_rarity1&category_440_Quality%5B4%5D=tag_haunted&category_440_Quality%5B5%5D=tag_collectors&appid=440&start=' + str(wheretostart)
        json_transient = requests.get(url)
        steam_market_listings = json_transient.json()
