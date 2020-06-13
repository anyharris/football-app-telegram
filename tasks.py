# tasks.py
import time
from celery import Celery
from football import Football

app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')


@app.task(name='tasks.fixtures')
def fixtures(api_key, date):
    footie = Football(api_key)
    response = footie.get_fixtures_leaguedate(date).json()
    fixtures_response = response['api']['fixtures']
    fixtures_data = []
    for i in fixtures_response:
        fixture = {'fixture_id': i['fixture_id'], 'event_timestamp': i['event_timestamp']}
        fixtures_data.append(fixture)
    return fixtures_data


@app.task(name='tasks.odds')
def odds(api_key, fixture):
    footie = Football(api_key)
    response = footie.get_odds_fixture(fixture).json()
    bets = response['api']['odds'][0]['bookmakers'][0]['bets']
    for i in bets:
        if i['label_name'] == 'Match Winner':
            fixture_odds = i['values']
            return fixture_odds
    else:
        return 'Couldn\'t find bet odds'


@app.task(name='tasks.news')
def news(api_key, fixture):
    footie = Football(api_key)
    while True:
        response = footie.get_news(fixture).json()
        if response['api']['results'] != 0:
            fixture_news = response['api']['results']['lineUps']
            return fixture_news
        time.sleep(60*10)
