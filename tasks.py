# tasks.py
'''
I could make this more secure
I need to fix the scheduling also for production
'''

import time
from celery import Celery, chord, chain
from celery.utils.log import get_task_logger
from football_apis import Football
from football_response_parser import ResponseParser

TG_BOT_TOKEN = '1241564289:AAGHB2cruHbI9QzOGzNft6UaDy3PkU34y_k'
TG_CHAT_ID = 173075290

TEAMS_APIFOOTBALL = ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace',
                     'Everton', 'Leicester', 'Liverpool', 'Manchester City', 'Manchester United', 'Newcastle',
                     'Norwich', 'Sheffield Utd', 'Southampton', 'Tottenham', 'Watford', 'West Ham', 'Wolves']
TEAMS_THEODDS = ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brighton and Hove Albion', 'Burnley', 'Chelsea',
                 'Crystal Palace', 'Everton', 'Leicester City', 'Liverpool', 'Manchester City', 'Manchester United',
                 'Newcastle United', 'Norwich City', 'Sheffield United', 'Southampton', 'Tottenham Hotspur',
                 'Watford', 'West Ham United', 'Wolverhampton Wanderers']

app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)


@app.task(name='tasks.fixtures')
# def fixtures(api_key, date):
#    footie = Football(api_key)
def fixtures(date):
    footie = Football()
    response = footie.get_fixtures_leaguedate(date).json()
    fixtures_response = response['api']['fixtures']
    for i in fixtures_response:
        fixture = {
            'fixture_id': i['fixture_id'],
            'event_timestamp': i['event_timestamp'],
            'home_team': i['homeTeam']['team_name']
        }
        execute(fixture)


@app.task(name='tasks.odds')
# def odds(api_key, fixture):
#    footie = Football(api_key)
def odds(prev_result, fixture):
    print('odds2')
    footie = Football()
    event_timestamp = fixture['event_timestamp']
    home_team_apifootball = fixture['home_team']
    home_team_position = TEAMS_APIFOOTBALL.index(home_team_apifootball)
    home_team_theodds = TEAMS_THEODDS[home_team_position]
    response = footie.get_odds_theodds().json()
    for i in response['data']:
        if i['commence_time'] == event_timestamp and i['home_team'] == home_team_theodds:
            for j in i['sites']:
                if j['site_key'] == 'betfair':
                    fixture_odds = {
                        'Home': round((j['odds']['h2h'][0]+j['odds']['h2h_lay'][0])/2, 2),
                        'Away': round((j['odds']['h2h'][1]+j['odds']['h2h_lay'][1])/2, 2),
                        'Draw': round((j['odds']['h2h'][2]+j['odds']['h2h_lay'][2])/2, 2),
                    }
    if prev_result:
        return prev_result, fixture_odds
    else:
        return fixture_odds


@app.task(name='tasks.news')
# def news(api_key, fixture):
#    footie = Football(api_key)
def news(fixture):
    print('news')
    footie = Football()
#    fixture_id = fixture['fixture_id']
    fixture_id = 209185
    while True:
        response = footie.get_news(fixture_id).json()
        if response['api']['results'] != 0:
            fixture_news = response['api']['lineUps']
            return fixture_news
        time.sleep(60 * 10)


@app.task(name='tasks.messenger')
def messenger(data, fixture_id):
    print('messenger')
    rparser = ResponseParser()
    rparser.parse_notification(data, fixture_id)
    rparser.parse_news(data, fixture_id)


@app.task(name='tasks.execute')
def execute(fixture):
    print('execute')
    fixture_id = fixture['fixture_id']
    event_timestamp = fixture['event_timestamp']
    job = chain(
#        news.subtask(fixture_id).set(eta=datetime.date.fromtimestamp(event_timestamp-60*60*1)),
        news.s(fixture),
#        odds.subtask(fixture_id, immutable=True).set(countdown=60*5)
        odds.s(fixture).set(countdown=7)
    )
    chord([odds.s(prev_result=False, fixture=fixture), job])(messenger.s(fixture_id))
