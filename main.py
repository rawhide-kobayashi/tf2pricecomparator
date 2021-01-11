import json
import requests
import sqlite3

qualities = ('Normal', 'Genuine', 'Unused', 'Vintage', 'Unused', 'Unusual', 'Unique', 'Community', 'Valve', 'Self-Made', 'Unused', 'Strange', 'Unused', 'Haunted', 'Collector\'s', 'Decorated')

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
            quality integer NOT NULL,
            craftability text NOT NULL)''')

# iterate through the relevant fields in bp.tf's spreadsheet to make a basic catalog of commonly traded items.
for keys in bp_spreadsheet['response']['items']:
    item_name = keys
    for x in bp_spreadsheet['response']['items'][item_name]['defindex']:
        # ignores tough break reskins and normal quality weapons present in this dataset.
        if len(bp_spreadsheet['response']['items'][item_name]['defindex']) == 1 or (35 <= x < 15000):
            defindex = x
            for values in bp_spreadsheet['response']['items'][item_name]['prices']:
                quality = values
                # noinspection PyAssignmentToLoopOrWithParameter
                for keys in bp_spreadsheet['response']['items'][item_name]['prices'][quality]['Tradable']:
                    craftability = keys
                    print(item_name, defindex, quality, craftability)
                    print(int(quality))
                    print(qualities[int(quality)])
                    if craftability == 'Craftable':
                        sku = str(defindex) + ';' + quality
                    else:
                        sku = str(defindex) + ';' + quality + ';' + 'uncraftable'
                    print(sku)
                    c.execute('INSERT OR REPLACE INTO common_items VALUES (?,?,?,?,?)', (sku, defindex, item_name, qualities[int(quality)], craftability))

conn.commit()
conn.close()
