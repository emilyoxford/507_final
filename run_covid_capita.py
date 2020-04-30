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
import data_covid_capita as data

from flask import Flask, render_template, request
app = Flask(__name__)

data.create_pop_db()
data.insert_country_data(data.merge_geo_data(data.scrape_country_codes(), data.scrape_country_names(), data.scrape_country_pops(), data.scrape_continent_codes()))
data.insert_continent_data(data.merge_geo_data(data.scrape_country_codes(), data.scrape_country_names(), data.scrape_country_pops(), data.scrape_continent_codes()))

@app.route('/')
def index():
    countries = sorted(data.country_options())
    continents = ['Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']
    return render_template('index.html', countries = countries, continents = continents)


@app.route('/results', methods = ['POST'])
def results():

    country_1 = request.form['country_1']
    country_2 =  request.form['country_2']
    country_3 = request.form['country_3']
    continent_1 = request.form['continent_1']
    continent_2 = request.form['continent_2']
    continent_3 = request.form['continent_3']
    news = request.form['news']

    countries = [country_1, country_2, country_3]

    if countries == ['--','--','--']:
        country_charts = ''
    else:
        country_charts = data.display_country_per_capita_bars([country_1,country_2,country_3])

    continents = [continent_1, continent_2, continent_3]

    if continents == ['--','--','--']:
        continent_charts = ''
    else:
        continent_charts = data.display_continent_per_capita_bars(data.continent_per_capita_totals([continent_1, continent_2, continent_3]))

    if news == 'Yes':
        headlines_1 = data.get_news(country_1)
        headlines_2 = data.get_news(country_2)
        headlines_3 = data.get_news(country_3)
    else:
        headlines_1 = ''
        headlines_2 = ''
        headlines_3 = ''

    return render_template('results.html',
                            country_charts = country_charts,
                            continent_charts = continent_charts,
                            country_1 = country_1,
                            country_2 = country_2,
                            country_3 = country_3,
                            news = news,
                            headlines_1 = headlines_1,
                            headlines_2 = headlines_2,
                            headlines_3 = headlines_3)

if __name__ == "__main__":
    app.run(debug=True)