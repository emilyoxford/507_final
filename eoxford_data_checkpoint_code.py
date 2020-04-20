#################################
##### Name: Emily Oxford
##### Uniqname: eoxford
#################################

from bs4 import BeautifulSoup
import datetime
import requests
import json
import csv
import sqlite3
import secrets

# https://learnandlearn.com/python-programming/python-reference/python-get-current-date

query_date = datetime.datetime.utcnow().date()

CACHE_DICT = {}
CACHE_FILENAME = 'cache.json'

COVID_API_URL = "https://api.covid19api.com/summary"
newsapi_URL = "https://newsapi.org/v2/top-headlines"


def open_cache(): #exact code and docstring from HW5 submission
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict): #modified code and docstring from HW5 submission
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save. If dictionary key not in cache, adds new key-value pair to cache.
    
    Returns
    -------
    None
    '''
    new_cache = open_cache()

    for key, value in cache_dict.items():
        new_cache[key] = value

    dumped_json_cache = json.dumps(new_cache)

    if dumped_json_cache != open_cache():
        fw = open(CACHE_FILENAME,"w")
        fw.write(dumped_json_cache)
        fw.close()


def make_request_with_cache(query): #modified code and docstring from HW5 submission

    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    state_url: string
        The URL for the state page on NPS website (e.g. 'https://www.nps.gov/state/me/index.htm')
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache JSON;
        key is state_url, value is returns of get_sites_for_state(state_url)
    '''
    query_key = f'{COVID_API_URL}{query_date}'

    current_cache = open_cache()

    for old_key, old_result in current_cache.items():
        if old_key == query_key:
            return old_result
    
    if query not in current_cache.keys():
        new_result = requests.get(f'{COVID_API_URL}').json()
        save_cache({f'{COVID_API_URL}{query_date}': new_result})
        return new_result

raw_html = requests.get('https://www.geonames.org/countries/')
country_soup = BeautifulSoup(raw_html.text, 'html.parser').find('table', class_ = 'restable sortable')

country_code_parents = country_soup.find_all('tr')

country_codes = []

for child in country_code_parents[2:]:
    country_codes.append(child.find('a').attrs['name']) #referenced http://www.compjour.org/warmups/govt-text-releases/intro-to-bs4-lxml-parsing-wh-press-briefings/

country_name_parents = country_soup.find_all('td')

country_names_messy = []

for child in country_name_parents:
    country_names_messy.append(child.find('a'))

country_names = []

for value in country_names_messy:
    if value != None:
        if 'href' in value.attrs.keys():
            country_names.append(value.text.replace('[','').replace(']',''))

country_pops_parents = []

country_pops_parents = country_soup.find_all('td', class_ = 'rightalign')

country_pops = []

for child in country_pops_parents:
    clean_child = child.text.replace(',','')
    if '.' not in clean_child:
        country_pops.append(int(clean_child))

country_data = []

for i in range(len(country_codes)):
    country_data.append([country_codes[i],country_names[i],country_pops[i]])

with open('country_data.csv', 'w') as target:
    country_writer = csv.writer(target)
    country_writer.writerows(country_data)

# talked through best way to write to database with Stephen Hayden (schayden) - thanks, Stephen!

conn = sqlite3.connect("country_data.sqlite")
cur = conn.cursor()

drop_table = '''
    DROP TABLE IF EXISTS "populations";
'''

create_table = '''CREATE TABLE if not exists 'populations'
                    ('id' integer primary key autoincrement,
                    'alpha2_code' text,
                    'country_name' text,
                    'population' integer)'''

# query = f'''
#     INSERT INTO populations(id,alpha2_code, country_name, population)
#     VALUES(NULL,1,2,3)
# '''

cur.execute(drop_table)
cur.execute(create_table)
# cur.execute(query)

insert = '''INSERT INTO populations VALUES (NULL, ?, ?, ?)'''

for row in country_data:
    cur.execute(insert,row)

conn.commit()

conn.close()

def get_news(country):
    return requests.get('https://newsapi.org/v2/top-headlines',params = {'country':country,'apiKey':secrets.news_api_key}).json()['articles'][0]

print(get_news('us'))