# tasks.py
'''
I could make this more secure
I need to fix the scheduling also for production
'''

import time
import requests
import datetime
from celery import Celery, chord, chain
from celery.utils.log import get_task_logger
from football_apis import Football

TG_BOT_TOKEN = '1241564289:AAGHB2cruHbI9QzOGzNft6UaDy3PkU34y_k'
TG_CHAT_ID = 173075290

app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)


@app.task(name='tasks.fixtures')
#def fixtures(api_key, date):
#    footie = Football(api_key)
def fixtures(date):
    footie = Football()
    response = footie.get_fixtures_leaguedate(date).json()
    fixtures_response = response['api']['fixtures']
    fixtures_data = []
    for i in fixtures_response:
        fixture = {'fixture_id': i['fixture_id'], 'event_timestamp': i['event_timestamp']}
        fixtures_data.append(fixture)
#    return fixtures_data
    return fixtures_data[0]


@app.task(name='tasks.odds')
#def odds(api_key, fixture):
#    footie = Football(api_key)
def odds(prev_result, fixture):
    footie = Football()
    fixture_id = fixture['fixture_id']
    response = footie.get_odds_fixture(fixture_id).json()
    bets = response['api']['odds'][0]['bookmakers'][0]['bets']
    fixture_odds = None
    for i in bets:
        if i['label_name'] == 'Match Winner':
            fixture_odds = i['values']
    if prev_result:
        return prev_result, fixture_odds
    else:
        return fixture_odds


@app.task(name='tasks.news')
#def news(api_key, fixture):
#    footie = Football(api_key)
def news(fixture):
    footie = Football()
    fixture_id = fixture['fixture_id']
    while True:
        response = footie.get_news(fixture_id).json()
        if response['api']['results'] != 0:
            fixture_news = response['api']['lineUps']
            return fixture_news
        time.sleep(60*10)


@app.task(name='tasks.messenger')
def messenger(data):
    logger.info('====DATA====')
    logger.info(data)
#    o1 = odds_24hr[0]['odd']
#    o2 = odds[0]['odd']
#    news['api']['results']
#    notification_text = f'o24h: {o1}, o: {o2}, news: {n1}'
    notification_text = f'so far so good'
    requests.get(
        f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={notification_text}&parse_mode=markdown')


@app.task(name='tasks.execute')
def execute(fixture):
    fixture_id = fixture['fixture_id']
    event_timestamp = fixture['event_timestamp']
    callback = messenger.subtask()
    header = [
#        odds.subtask(fixture_id).set(eta=datetime.date.fromtimestamp(event_timestamp-60*60*24)),
        odds.subtask(fixture_id),
        chain(
#            news.subtask(fixture_id).set(eta=datetime.date.fromtimestamp(event_timestamp-60*60*1)),
            news.subtask(fixture_id),
#            odds.subtask(fixture_id, immutable=True).set(countdown=60*5)
            odds.subtask(fixture_id, immutable=True)
        )
    ]
    chord(header)(callback)
    pass
