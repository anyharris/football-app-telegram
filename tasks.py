# tasks.py
'''
Ready for production. Just need to put it on the server

to start worker:
celery -A tasks worker -B -l info
nohup celery -A tasks worker -B -l info > celery.log &

to show celery queue:
sudo rabbitmqctl list_queues

to purge celery queue:
celery -A tasks purge

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

CHAT_IDS = [
    173075290,  # Nick
    200905953,   # Rob
    -1001189281782,  # Rob's group
    -497587937  # Test group
]


app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)

app.conf.beat_schedule = {
    'check-daily-matches': {
        'task': 'tasks.fixtures',
        'schedule': crontab(minute='00', hour='4', day_of_week='*'),
    }
}


@app.task(name='tasks.fixtures')
def fixtures():
    print(f'starting to get fixtures and execute them')
    date_today = str(date.today())
    footie = Football()
    response = footie.get_fixtures_leaguedate(date_today).json()
    fixtures_response = response['api']['fixtures']
    for i in fixtures_response:
        fixture = {
            'fixture_id': i['fixture_id'],
            'event_timestamp': i['event_timestamp'],
            'home_team': i['homeTeam']['team_name']
        }
        print(f'ordering execution of fixture {fixture}')
        execute(fixture)


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
                            'Home': round(j['odds']['h2h'][0], 2),
                            'Away': round(j['odds']['h2h'][1], 2),
                            'Draw': round(j['odds']['h2h'][2], 2),
                        }
                        print(f'got odds {fixture_odds} for fixture {fixture}')
                    else:
                        fixture_odds = {
                            'Home': round(j['odds']['h2h'][1], 2),
                            'Away': round(j['odds']['h2h'][0], 2),
                            'Draw': round(j['odds']['h2h'][2], 2),
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
            if response['api']['lineUps'][next(iter(response['api']['lineUps']))]['formation'] is not None:
                fixture_news = response['api']['lineUps']
                print(f'got the news for fixture {fixture}')
                return fixture_news
        print('waiting 1 min for new news')
        time.sleep(60 * 1)


@app.task(name='tasks.messenger')
def messenger(data, fixture_id):
    print(f'starting to parse messages for fixture id: {fixture_id}')
    rparser = ResponseParser()
    for i in CHAT_IDS:
        rparser.parse_notification(data, fixture_id, i)
        print(f'parsed notification messages for fixture id: {fixture_id} and chat id {i}')
    rparser.parse_news(data, fixture_id)
    print(f'parsed news message for fixture id: {fixture_id}')


@app.task(name='tasks.execute')
def execute(fixture):
    print(f'starting execution of fixture {fixture}')
    fixture_id = fixture['fixture_id']
    event_timestamp = fixture['event_timestamp']
    now = int(time.time())
    job = chain(
        news.s(fixture).set(countdown=(event_timestamp - now - (60 * 58))),
        odds.s(fixture).set(countdown=(60 * 1))
    )
    chord([odds.s(prev_result=False, fixture=fixture).set(countdown=(event_timestamp - now - (60 * 70))), job])(messenger.s(fixture_id))
    print(f'executed fixture {fixture}')
