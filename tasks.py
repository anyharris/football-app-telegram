# tasks.py
"""
to start worker:
nohup celery -A tasks worker -B -l info > celery.log &

to show celery queue:
sudo rabbitmqctl list_queues

to purge celery queue:
celery -A tasks purge
"""
import time
import json
import os
from dotenv import load_dotenv
from datetime import date
from celery import Celery, chain
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from modules.postgres_methods import FootballPostgres
from modules.api_wrappers import APIFootball, TheOdds, Telegram
import modules.response_parser as rp


# Load environment variables
load_dotenv()
SEASON = int(os.getenv('SEASON'))
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
API_KEY_APIFOOTBALL = os.getenv('API_KEY_APIFOOTBALL')
API_KEY_THEODDS = os.getenv('API_KEY_THEODDS')
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASS = os.getenv('POSTGRES_PASS')

# Initialize objects with env variables
tg = Telegram(bot_token=TG_BOT_TOKEN)
apif = APIFootball(api_key=API_KEY_APIFOOTBALL, season=SEASON)
todds = TheOdds(api_key=API_KEY_THEODDS)
fpsg = FootballPostgres(database=POSTGRES_DATABASE, host=POSTGRES_HOST, user=POSTGRES_USER, password=POSTGRES_PASS)

app = Celery('tasks', backend='redis://localhost:6379/0', broker='pyamqp://guest@localhost//')

# Load league data and list of bot subscribers
with open('data/league_data.txt') as json_file:
    league_data = json.load(json_file)
TEAMS_APIFOOTBALL = league_data['APIFootball_team_names']
TEAMS_THEODDS = league_data['TheOdds_team_names']
LEAGUE_ID = league_data['APIFootball_league_ID']
with open('data/chat_ids.txt') as json_file:
    chat_dict = json.load(json_file)
CHAT_IDS = chat_dict['chat_ids']

# Default celery task logger
logger = get_task_logger(__name__)


# Schedule when to look for the day's fixtures (UTC time)
app.conf.beat_schedule = {
    'check-daily-matches': {
        'task': 'tasks.fixtures',
        'schedule': crontab(minute='00', hour='4', day_of_week='*'),
    }
}


@app.task(name='tasks.fixtures')
def fixtures():
    print('starting to get fixtures and execute them')
    date_today = str(date.today())
    response = apif.get_fixtures_leaguedate(LEAGUE_ID, date_today).json()
    fixtures_response = response['api']['fixtures']
    for each in fixtures_response:
        fixture = {
            'fixture_id': each['fixture_id'],
            'event_timestamp': each['event_timestamp'],
            'home_team': each['homeTeam']['team_name']
        }
        print(f'ordering execution of fixture {fixture}')
        execute(fixture)


@app.task(name='tasks.odds')
def odds(fixture_news, fixture):
    print(fixture_news)
    if fixture_news == 'task.news: timeout - no news':
        fixture_odds = {}
        print(f"task.odds: no news, so didn't get odds for fixture {fixture['fixture_id']}")
        return fixture_news, fixture_odds
    event_timestamp = fixture['event_timestamp']
    home_team_apifootball = fixture['home_team']
    home_team_position = TEAMS_APIFOOTBALL.index(home_team_apifootball)
    home_team_theodds = TEAMS_THEODDS[home_team_position]
    response = todds.get_odds_theodds().json()
    fixture_odds = None
    for response_fixture in response['data']:
        if response_fixture['commence_time'] == event_timestamp and response_fixture['home_team'] == home_team_theodds:
            for bookmaker in response_fixture['sites']:
                if bookmaker['site_key'] == 'betfair':
                    if response_fixture['home_team'] == response_fixture['teams'][0]:
                        fixture_odds = {
                            'Home': round(bookmaker['odds']['h2h'][0], 2),
                            'Away': round(bookmaker['odds']['h2h'][1], 2),
                            'Draw': round(bookmaker['odds']['h2h'][2], 2),
                        }
                        print(f"got odds {fixture_odds} for fixture {response_fixture['teams']}")
                    else:
                        fixture_odds = {
                            'Home': round(bookmaker['odds']['h2h'][1], 2),
                            'Away': round(bookmaker['odds']['h2h'][0], 2),
                            'Draw': round(bookmaker['odds']['h2h'][2], 2),
                        }
                        print(f"got odds {fixture_odds} for fixture {response_fixture['teams']}")
        else:
            fixture_odds = {}
            print(f"task.odds: news, but didn't get odds for fixture {response_fixture['teams']}")
    return fixture_news, fixture_odds


@app.task(name='tasks.news')
def news(fixture):
    print(f'starting to get news for fixture {fixture}')
    fixture_id = fixture['fixture_id']
    while True:
        event_timestamp = fixture['event_timestamp']
        now = int(time.time())
        if event_timestamp - now <= 35:
            return 'task.news: timeout - no news'
        response = apif.get_news(fixture_id).json()
        if response['api']['results'] != 0:
            if response['api']['lineUps'][next(iter(response['api']['lineUps']))]['formation'] is not None:
                fixture_news = response['api']['lineUps']
                print(f'task.news: got the news for fixture {fixture}')
                return fixture_news
        print('task.news: waiting 1 min for new news')
        time.sleep(60 * 1)


@app.task(name='tasks.messenger')
def messenger(fixture_news_odds, fixture_id):
    if fixture_news_odds[0] == 'task.news: timeout - no news':
        print(f'task.messenger: no news for fixture id: {fixture_id}')
    else:
        print(f'task.messenger: starting to parse messages for fixture id: {fixture_id}')
        notification_msg = rp.notification(fixture_news_odds)
        identifier = f'f{fixture_id}'
        for chat_id in CHAT_IDS:
            tg.callback_button_message(chat_id, notification_msg, identifier)
            print(f'task.messenger: parsed and sent notification messages for fixture id: {fixture_id} and chat id {chat_id}')
        news_message = rp.news(fixture_news_odds)
        fpsg.write_news(fixture_id, news_message)
        print(f'task.messenger: parsed and stored news message for fixture id: {fixture_id}')


@app.task(name='tasks.execute')
def execute(fixture):
    print(f'task.execute: starting execution of fixture {fixture}')
    fixture_id = fixture['fixture_id']
    event_timestamp = fixture['event_timestamp']
    now = int(time.time())
    chain(
        news.s(fixture).set(countdown=(event_timestamp - now - (60 * 58))),
        odds.s(fixture), messenger.s(fixture_id)
    )()
    print(f'task.execute: executed fixture {fixture}')
