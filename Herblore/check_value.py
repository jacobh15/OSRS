import requests
import json
import pandas

MAPPING_URL = 'https://prices.runescape.wiki/api/v1/osrs/mapping'
LATEST_URL = 'https://prices.runescape.wiki/api/v1/osrs/latest'
ONE_HOUR_URL = 'https://prices.runescape.wiki/api/v1/osrs/1h'
HEADERS = {'User-Agent': 'Herblore Calculator'}

training_data = pandas.read_csv('training.csv')


def load_from_url(url):
    r = requests.get(url, headers=HEADERS)
    return json.loads(r.content.decode('utf-8'))


mapping = load_from_url(MAPPING_URL)
item_ids = {item['name'].lower(): str(item['id']) for item in mapping}


def get_price_data(items):
    price_data = {}
    latest_prices = load_from_url(LATEST_URL)['data']
    one_hour_prices = load_from_url(ONE_HOUR_URL)['data']
    for item_name in map(lambda s: s.lower(), items):
        latest = latest_prices.get(item_ids[item_name], {'low': None, 'high': None})
        one_hour = one_hour_prices.get(item_ids[item_name], {'avgLowPrice': None, 'lowPriceVolume': 0, 'avgHighPrice': None, 'highPriceVolume': 0})
        price_data[item_name] = {
            'name': item_name,
            'latest_low': latest['low'],
            'one_hour_low': one_hour['avgLowPrice'],
            'volume_low': one_hour['lowPriceVolume'],
            'latest_high': latest['high'],
            'one_hour_high': one_hour['avgHighPrice'],
            'volume_high': one_hour['highPriceVolume']
        }
    
    return price_data


def main():
    four_dose_potions = training_data['potion'].apply(lambda name: name + '(4)')
    herbs = training_data['herb'][training_data['herb'].apply(lambda herb: isinstance(herb, str))]
    grimies = herbs.apply(lambda name: 'Grimy ' + name)
    bases = training_data['base']
    secondaries = training_data['secondary']

    all_items = set(herbs).union(grimies).union(secondaries)
    for base in bases:
        all_items.update(base.split(', '))
    
    all_prices = get_price_data(all_items)
    
    for obj in all_prices.values():
        print(obj)

if __name__ == '__main__':
    main()
        