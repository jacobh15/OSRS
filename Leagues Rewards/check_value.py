import requests
import json
import pandas

MAPPING_URL = 'https://prices.runescape.wiki/api/v1/osrs/mapping'
LATEST_URL = 'https://prices.runescape.wiki/api/v1/osrs/latest'
ONE_HOUR_URL = 'https://prices.runescape.wiki/api/v1/osrs/1h'
HEADERS = {'User-Agent': 'Leagues Rewards Price Checker'}

points_data = pandas.read_csv('points.csv', index_col='Name')
points = points_data['Point Cost'].to_dict()
quantities = points_data['Quantity'].to_dict()
tradeable_sets = pandas.read_csv('tradeables.csv').to_dict('records')
tradeables = {entry['Name'] for entry in tradeable_sets}

purchaseables = {}
for entry in tradeable_sets:
    purchaseables.setdefault(entry['Set'], []).append(entry['Name'])


def load_from_url(url):
    r = requests.get(url, headers=HEADERS)
    return json.loads(r.content.decode('utf-8'))


mapping = load_from_url(MAPPING_URL)
item_ids = {item['name'].lower(): str(item['id']) for item in mapping}


def get_price_data():
    price_data = {}
    latest_prices = load_from_url(LATEST_URL)['data']
    one_hour_prices = load_from_url(ONE_HOUR_URL)['data']
    for item_name in tradeables:
        latest = latest_prices.get(item_ids[item_name], {'low': None})
        one_hour = one_hour_prices.get(item_ids[item_name], {'avgLowPrice': None, 'lowPriceVolume': 0})
        price_data[item_name] = {
            'name': item_name,
            'latest': latest['low'],
            'one_hour': one_hour['avgLowPrice'],
            'volume': one_hour['lowPriceVolume']
        }
    
    return price_data


def summarize_item(item_prices, cost, quantity, indent):
    if item_prices['one_hour'] is not None:
        gp_per_point = item_prices['one_hour'] * quantity / cost
        volume = item_prices['volume']
        print(indent + f'GP/point (latest): {gp_per_point:.01f}, Volume/h: {volume:.01f}')
    elif item_prices['latest'] is not None:
        gp_per_point = item_prices['latest'] * quantity / cost
        volume = item_prices['volume']
        print(indent + f'GP/point (latest): {gp_per_point:.01f}, Volume/h: {volume:.01f}')
    else:
        gp_per_point = 0
        volume = 0
        print(indent + 'No reliable prices')
    
    return gp_per_point, volume


def summarize_set(items, cost, quantity, indent):
    use_latest = all(item['latest'] is not None for item in items)
    use_one_hour = all(item['one_hour'] is not None for item in items)
    effective_prices = {
        'latest': 0 if use_latest else None,
        'one_hour': 0 if use_one_hour else None,
        'volume': 0
    }
    
    for item in items:
        if use_latest:
            effective_prices['latest'] += item['latest'] / len(items)
        
        if use_one_hour:
            effective_prices['one_hour'] += item['one_hour'] / len(items)
        
        effective_prices['volume'] += item['volume'] / len(items)
    
    gp_per_point = summarize_item(effective_prices, cost, quantity, indent)[0]
    
    for item in items:
        if item['one_hour'] is not None:
            print(indent + '  ' + item['name'] + f': 1h = {item["one_hour"]}, volume = {item["volume"]}') 
        elif item['latest'] is not None:
            print(indent + '  ' + item['name'] + f': latest = {item["latest"]}, volume = {item["volume"]}')
        else:
            print(indent + '  ' + item['name'] + ': No reliable price')
    
    return gp_per_point, effective_prices['volume']


def main():
    out_rows = {'Store item': [], 'GP/point': [], 'Volume/h': []}
    prices = get_price_data()
    for purchaseable, cost in points.items():
        quantity = quantities[purchaseable]
        set_items = purchaseables[purchaseable]
        print(f'Store item: {purchaseable}')
        if len(set_items) == 1:
            gp_per_point, volume = summarize_item(prices[set_items[0]], cost, quantity, '  ')
        else:
            gp_per_point, volume = summarize_set([prices[item] for item in set_items], cost, quantity, '  ')
        
        out_rows['Store item'].append(purchaseable)
        out_rows['GP/point'].append(gp_per_point)
        out_rows['Volume/h'].append(volume)
    
    pandas.DataFrame.from_dict(out_rows).set_index('Store item').to_csv('last_value_check.csv')


if __name__ == '__main__':
    main()
        