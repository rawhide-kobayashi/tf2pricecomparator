import json
import requests

#import test json file and discard dead weight
with open('test data set.json') as json_transient:
    bp_spreadsheet = json.load(json_transient)
    del json_transient

#iterate through the relevant fields in bp.tf's spreadsheet json to end up with unique item
#information, while maintaining relevancy.  why catalog untradable objects?
#no need to grab prices from this sheet, it updates too slowly.  this sheet merely serves
#as a reference for items likely to be frequently traded.
for keys in bp_spreadsheet['response']['items']:
    item_name = keys
    for x in bp_spreadsheet['response']['items'][item_name]['defindex']:
        defindex = x
        for values in bp_spreadsheet['response']['items'][item_name]['prices']:
            quality = values
            for keys in bp_spreadsheet['response']['items'][item_name]['prices'][quality]['Tradable']:
                craftability = keys
                print(item_name, defindex, quality, craftability)

                """
                if isinstance(bp_spreadsheet['response']['items'][item_name]['prices'][quality]['Tradable'][craftability], list) == True:
                    print(item_name, defindex, quality, craftability)

                do i care about catalogging the individual unusual effects of any given hat,
                since bp classifieds can just search for all unusuals of a given hat, and steam market
                doesn't differentiate in the first place?
                
                else:
                    for keys in bp_spreadsheet['response']['items'][item_name]['prices'][quality]['Tradable'][craftability]:
                        unusual_effect = keys
                        print(item_name, defindex, quality, craftability, unusual_effect)
                """