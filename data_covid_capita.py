#################################
##### Name: Emily Oxford ########
##### Uniqname: eoxford #########
#################################

from bs4 import BeautifulSoup
import datetime
import requests
import json
import csv
import sqlite3
import secrets
import plotly.graph_objs as go
import numpy as np
import pandas as pd #all numpy and pandas methods learned in SI 618 with Chris Teplovs in winter 2020 (thanks, Dr. Chris!)

# Constants

CACHE_DICT = {}
CACHE_FILENAME = 'cache.json'

COVID_API_URL = "https://api.covid19api.com/summary"
GEO_COUNTRY_URL = "https://www.geonames.org/countries/"
NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"

# check_same_thread debug solution from https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
POP_DB = "populations.sqlite"
conn = sqlite3.connect(POP_DB, check_same_thread = False)
cur = conn.cursor()

# Setting today's date
# referenced https://learnandlearn.com/python-programming/python-reference/python-get-current-date

QUERY_DATE = datetime.date.today()

def get_covid_data():
    return requests.get(COVID_API_URL).json()['Countries']

# Caching

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

def covid_api_query_key():
    return f'covid_api_{QUERY_DATE}'

def covid_api_cache(query_key): #modified code and docstring from HW5 submission
    current_cache = open_cache()

    for old_key, old_result in current_cache.items():
        if old_key == query_key:
            return old_result
    
    if query_key not in current_cache.keys():
        new_result = get_covid_data() #update this so it actually holds results
        save_cache({f'{query_key}': new_result})
        return new_result


# Extracting population data

def scrape_country_codes():
    raw_html = requests.get(GEO_COUNTRY_URL)

    country_soup = BeautifulSoup(raw_html.text, 'html.parser').find('table', class_ = 'restable sortable')

    country_code_parents = country_soup.find_all('tr')

    country_codes = []

    for child in country_code_parents[1:]:
        country_codes.append(child.find('a').attrs['name']) #referenced http://www.compjour.org/warmups/govt-text-releases/intro-to-bs4-lxml-parsing-wh-press-briefings/

    return country_codes


def scrape_country_names():    
    raw_html = requests.get(GEO_COUNTRY_URL)

    country_soup = BeautifulSoup(raw_html.text, 'html.parser').find('table', class_ = 'restable sortable')

    country_name_parents = country_soup.find_all('td')

    country_names_messy = []

    for child in country_name_parents:
        country_names_messy.append(child.find('a'))

    country_names = []

    for value in country_names_messy:
        if value != None:
            if 'href' in value.attrs.keys():
                country_names.append(value.text.replace('[','').replace(']',''))

    return country_names


def scrape_country_pops():
    raw_html = requests.get(GEO_COUNTRY_URL)

    country_soup = BeautifulSoup(raw_html.text, 'html.parser').find('table', class_ = 'restable sortable')

    country_pops_parents = []

    country_pops_parents = country_soup.find_all('td', class_ = 'rightalign')

    country_pops = []

    for child in country_pops_parents:
        clean_child = child.text.replace(',','')
        if '.' not in clean_child:
            country_pops.append(int(clean_child))
    
    return country_pops


def scrape_continent_codes():
    raw_html = requests.get(GEO_COUNTRY_URL)

    country_soup = BeautifulSoup(raw_html.text, 'html.parser').find('table', class_ = 'restable sortable')

    continent_soup = country_soup.find_all('tr')

    continent_codes = [row.text[-2:] for row in continent_soup[1:]]

    return continent_codes


def merge_geo_data(country_codes, country_names, country_pops, continent_codes):
    country_data = []

    for i in range(len(country_codes)):
        country_data.append([country_codes[i],country_names[i],country_pops[i],continent_codes[i]])
    
    return country_data

# Writing population database

def create_pop_db():
    drop_countries = '''
    DROP TABLE IF EXISTS "countries";
    '''

    create_countries = '''
    CREATE TABLE IF NOT EXISTS 'countries'
    ('country_id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'alpha2_code' TEXT,
    'country_name' TEXT,
    'population' INTEGER,
    'continent_id' INTEGER);
    '''

    drop_continents = '''
    DROP TABLE IF EXISTS "continents";
    '''

    create_continents = '''
    CREATE TABLE IF NOT EXISTS 'continents'
    ('continent_id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'continent_code' TEXT,
    'continent_name' TEXT,
    'population' INTEGER)
    '''

    cur.execute(drop_countries)
    cur.execute(create_countries)
    cur.execute(drop_continents)
    cur.execute(create_continents)


def insert_country_data(country_data):
    populate_countries = f'''
    INSERT INTO countries 
    VALUES (NULL, ?, ?, ?, ?)
    '''

    for row in country_data:
        cur.execute(populate_countries, row)

    conn.commit()


def insert_continent_data(country_data):
    continent_codes = []

    for row in country_data:
        if row[-1] not in continent_codes:
            continent_codes.append(row[-1])

    continent_codes = sorted(continent_codes)

    continent_names = ['Africa', 'Antarctica', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']

    continent_pops = pd.DataFrame(country_data)[[2, 3]].groupby(3).sum()

    continents_all = []

    for i in range(len(continent_codes)):
        continents_all.append([continent_codes[i], continent_names[i], int(continent_pops[2][i])])
    
    populate_continents = f'''
    INSERT INTO continents 
    VALUES (NULL, ?, ?, ?)
    '''

    for row in continents_all:
        cur.execute(populate_continents, row)

    conn.commit()

# create_pop_db()
# insert_country_data(merge_geo_data(scrape_country_codes(), scrape_country_names(), scrape_country_pops(), scrape_continent_codes()))
# insert_continent_data(merge_geo_data(scrape_country_codes(), scrape_country_names(), scrape_country_pops(), scrape_continent_codes()))

# Extracting news data


def get_iso_and_pop_from_db(country_name):
    iso_pop = cur.execute(f'SELECT alpha2_code, population FROM countries WHERE country_name = "{country_name}"').fetchall()[0]
    return iso_pop


def merge_metrics_from_covid_api(country_name):
    iso = get_iso_and_pop_from_db(country_name)[0]

    metrics = ['CountryCode', 'Country', 'TotalConfirmed', 'TotalDeaths', 'TotalRecovered']

    api_results = covid_api_cache(covid_api_query_key())

    country_dict = {}

    for metric in metrics:
        for country in api_results:
            if country['CountryCode'] == iso:
                country_dict[metric] = country[metric]
            else:
                continue

    country_dict['Population'] = get_iso_and_pop_from_db(country_name)[1]

    return country_dict

def metric_per_capita(country_name):
    country_dict = merge_metrics_from_covid_api(country_name)

    per_cap_dict = {}

    metrics = ['TotalConfirmed', 'TotalDeaths', 'TotalRecovered']

    for metric in metrics:
        per_cap_dict[(country_name, metric)] = country_dict[metric]/country_dict['Population']

    return per_cap_dict

def display_country_per_capita_bars(country_names):    
    countries = []

    joined_cap_dicts = []

    for country_name in country_names:
        if country_name != "--":
            joined_cap_dicts.append(metric_per_capita(country_name))
            countries.append(country_name)

    cap_confirmed = []
    cap_deaths = []
    cap_recovered = []

    for cap_dict in joined_cap_dicts:
        for key, value in cap_dict.items():
            if key[1] == 'TotalConfirmed':
                cap_confirmed.append(value)
            elif key[1] == 'TotalDeaths':
                cap_deaths.append(value)
            elif key[1] == 'TotalRecovered':
                cap_recovered.append(value)

    confirmed_bar_data = go.Bar(x = countries, y = cap_confirmed)
    confirmed_layout = go.Layout(title = "Total Confirmed per Capita (by country)")
    confirmed_fig = go.Figure(data = confirmed_bar_data, layout = confirmed_layout)
    confirmed_div = confirmed_fig.to_html(full_html=False)

    deaths_bar_data = go.Bar(x = countries, y = cap_deaths)
    deaths_layout = go.Layout(title = "Total Deaths per Capita (by country)")
    deaths_fig = go.Figure(data = deaths_bar_data, layout = deaths_layout)
    deaths_div = deaths_fig.to_html(full_html=False)

    recovered_bar_data = go.Bar(x = countries, y = cap_recovered)
    recovered_layout = go.Layout(title = "Total Recoveries per Capita (by country)")
    recovered_fig = go.Figure(data = recovered_bar_data, layout = recovered_layout)
    recovered_div = recovered_fig.to_html(full_html=False)

    return confirmed_div, deaths_div, recovered_div


def continent_per_capita_totals(continents):
    api_results = covid_api_cache(covid_api_query_key())

    continent_countries = {}

    for continent in continents:
        if continent != '--':
            countries = cur.execute(f'''SELECT countries.alpha2_code FROM countries JOIN continents ON countries.continent_id = continents.continent_code WHERE continents.continent_name =
            "{continent}"''').fetchall()
            for country in countries:
                continent_countries[continent] = [country[0] for country in countries]

    continent_pops = cur.execute(f'''SELECT continent_name, continent_code, population FROM continents''').fetchall()

    all_pops = {}

    for row in continent_pops:
        all_pops[row[0]] = row[2]

    confirmed = {}

    for continent, countries in continent_countries.items():
        confirmed[continent] = {}
        for country in countries:
            for result in api_results:
                if result['CountryCode'] == country:
                    confirmed[continent][country] = result['TotalConfirmed']

    cap_total_confirmed = {}
    for continent, countries in confirmed.items():
        cap_total_confirmed[continent] = np.sum(list(confirmed[continent].values()))/all_pops[continent]

    deaths = {}
    
    for continent, countries in continent_countries.items():
        deaths[continent] = {}
        for country in countries:
            for result in api_results:
                if result['CountryCode'] == country:
                    deaths[continent][country] = result['TotalDeaths']

    cap_total_deaths = {}
    for continent, countries in deaths.items():
        cap_total_deaths[continent] = np.sum(list(deaths[continent].values()))/all_pops[continent]

    recovered = {}

    for continent, countries in continent_countries.items():   
        recovered[continent] = {}
        for country in countries:
            for result in api_results:
                if result['CountryCode'] == country:
                    recovered[continent][country] = result['TotalRecovered']/all_pops[continent]

    cap_total_recovered = {}

    for continent,countries in recovered.items():
        cap_total_recovered[continent] = np.sum(list(recovered[continent].values()))

    return [cap_total_confirmed, cap_total_deaths, cap_total_recovered]


def display_continent_per_capita_bars(continent_cap_totals):

    confirmed_bar_data = go.Bar(x = list(continent_cap_totals[0].keys()), y = list(continent_cap_totals[0].values()), opacity = 0.5)
    confirmed_layout = go.Layout(title = "Total Confirmed per Capita (by continent)")
    confirmed_fig = go.Figure(data = confirmed_bar_data, layout = confirmed_layout)
    confirmed_div = confirmed_fig.to_html(full_html=False)

    deaths_bar_data = go.Bar(x = list(continent_cap_totals[1].keys()), y = list(continent_cap_totals[1].values()), opacity = 0.5)
    deaths_layout = go.Layout(title = "Total Deaths per Capita (by continent)")
    deaths_fig = go.Figure(data = deaths_bar_data, layout = deaths_layout)
    deaths_div = deaths_fig.to_html(full_html=False)

    recovered_bar_data = go.Bar(x = list(continent_cap_totals[2].keys()), y = list(continent_cap_totals[1].values()), opacity = 0.5)
    recovered_layout = go.Layout(title = "Total Recoveries per Capita (by continent)")
    recovered_fig = go.Figure(data = recovered_bar_data, layout = recovered_layout)
    recovered_div = recovered_fig.to_html(full_html=False)

    return confirmed_div, deaths_div, recovered_div


def get_news(country_name):
    headlines = []
    if country_name != '--':
        try:
            iso = get_iso_and_pop_from_db(country_name)[0]

            all_articles = requests.get('https://newsapi.org/v2/top-headlines', params = {'country':iso,'apiKey':secrets.news_api_key, 'pageSize':5}).json()['articles']

            for article in all_articles:
                headlines.append(article['title'])

        except:
            headlines.append(f'No headlines available from {country_name}.')
        
        if headlines == []:
            return [f'No headlines available from {country_name}.']
        else:
            return headlines

def country_options():
    api_results = covid_api_cache(covid_api_query_key())

    api_available_countries = []

    for result in api_results:
        api_available_countries.append(result['CountryCode'])

    country_options = []

    for row in merge_geo_data(scrape_country_codes(), scrape_country_names(), scrape_country_pops(), scrape_continent_codes()):
        if row[2] != 0:
            if row[0] in api_available_countries:
                country_options.append(row[1])
    
    return sorted(country_options)