# tasks.py
'''
Test has been debugged. Need to put this on the server and set up a scheduler.

to start worker:
celery -A tasks worker -B -l info
'''

import time
from datetime import date
from celery import Celery, chord, chain
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from football_apis import Football
from football_response_parser import ResponseParser


TEAMS_APIFOOTBALL = ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace',
                     'Everton', 'Leicester', 'Liverpool', 'Manchester City', 'Manchester United', 'Newcastle',
                     'Norwich', 'Sheffield Utd', 'Southampton', 'Tottenham', 'Watford', 'West Ham', 'Wolves']
TEAMS_THEODDS = ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brighton and Hove Albion', 'Burnley', 'Chelsea',
                 'Crystal Palace', 'Everton', 'Leicester City', 'Liverpool', 'Manchester City', 'Manchester United',
                 'Newcastle United', 'Norwich City', 'Sheffield United', 'Southampton', 'Tottenham Hotspur',
                 'Watford', 'West Ham United', 'Wolverhampton Wanderers']
'''
TEAMS_APIFOOTBALL = ['Borussia Monchengladbach', 'SC Freiburg', 'Union Berlin', 'Werder Bremen']
TEAMS_THEODDS = ['Borussia Monchengladbach', 'SC Freiburg', 'Union Berlin', 'Werder Bremen']
'''
CHAT_IDS = [
    173075290,  # Nick
    200905953   # Rob
]


app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)

app.conf.beat_schedule = {
    'check-daily-matches': {
        'task': 'tasks.fixtures',
        'schedule': crontab(minute='08', hour='3', day_of_week='*'),
    }
}

@app.task(name='tasks.fixtures')
def fixtures():
    date_today = str(date.today())
    print(date_today)
    print(type(date_today))
    footie = Football()
    response = footie.get_fixtures_leaguedate(date_today).json()
    print(response)
    fixtures_response = response['api']['fixtures']
    for i in fixtures_response:
        fixture = {
            'fixture_id': i['fixture_id'],
            'event_timestamp': i['event_timestamp'],
            'home_team': i['homeTeam']['team_name']
        }
        for j in CHAT_IDS:
            print(f'ordering execution of fixture {fixture} for chat ID {j}')
            execute(fixture, j)


@app.task(name='tasks.odds')
def odds(prev_result, fixture):
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
                    if i['home_team'] == i['teams'][0]:
                        fixture_odds = {
                            'Home': round((j['odds']['h2h'][0] + j['odds']['h2h_lay'][0]) / 2, 2),
                            'Away': round((j['odds']['h2h'][1] + j['odds']['h2h_lay'][1]) / 2, 2),
                            'Draw': round((j['odds']['h2h'][2] + j['odds']['h2h_lay'][2]) / 2, 2),
                        }
                        print(f'got odds {fixture_odds} for fixture {fixture}')
                    else:
                        fixture_odds = {
                            'Home': round((j['odds']['h2h'][1] + j['odds']['h2h_lay'][1]) / 2, 2),
                            'Away': round((j['odds']['h2h'][0] + j['odds']['h2h_lay'][0]) / 2, 2),
                            'Draw': round((j['odds']['h2h'][2] + j['odds']['h2h_lay'][2]) / 2, 2),
                        }
                        print(f'got odds {fixture_odds} for fixture {fixture}')
    if prev_result:
        return prev_result, fixture_odds
    else:
        return fixture_odds


@app.task(name='tasks.news')
def news(fixture):
    print(f'starting to get news for fixture {fixture}')
    footie = Football()
    fixture_id = fixture['fixture_id']
    while True:
        response = footie.get_news(fixture_id).json()
        print(response)
        if response['api']['results'] != 0:
            fixture_news = response['api']['lineUps']
            print(f'got the news for fixture {fixture}')
            return fixture_news
        time.sleep(60 * 5)


@app.task(name='tasks.messenger')
def messenger(data, fixture_id, chat_id):
    print(f'starting to parse messages for fixture id: {fixture_id} and chat id {chat_id}')
    rparser = ResponseParser()
    rparser.parse_notification(data, fixture_id, chat_id)
    rparser.parse_news(data, fixture_id)
    print(f'parsed messages for fixture id: {fixture_id} and chat id {chat_id}')


@app.task(name='tasks.execute')
def execute(fixture, chat_id):
    print(f'starting execution of fixture {fixture} for chat id {chat_id}')
    fixture_id = fixture['fixture_id']
    event_timestamp = fixture['event_timestamp']
    now = int(time.time())
    job = chain(
        news.s(fixture).set(countdown=(event_timestamp - now - (60 * 59))),
        odds.s(fixture).set(countdown=(60 * 2))
    )
    chord([odds.s(prev_result=False, fixture=fixture).set(countdown=(event_timestamp - now - (60 * 90))), job])(messenger.s(fixture_id, chat_id))
    print(f'executed fixture {fixture} for chat id {chat_id}')
