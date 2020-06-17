# football_response_parser.py
'''
Ready for production
'''
import requests
import json
from football_postgres import FootballPostgresql
from dotenv import load_dotenv
import os


class ResponseParser:
    API_HOST = 'https://api.telegram.org'

    def __init__(self):
        load_dotenv()
        self.TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

    def parse_notification(self, celery_response, fixture, chat_id):
        # Parse response to form notification message
        bet_old = celery_response[0]
        bet_new = celery_response[1][1]
        news = celery_response[1][0]
        teams = list(news)
        notification_text = f'__*{teams[0]}* vs *{teams[1]}*__\n'
        notification_text += f'Odds 90 mins before the match:\n'
        for key in bet_old:
            notification_text += f'`{key}: {bet_old[key]}`\n'
        notification_text += '\nOdds after team news:\n'
        for key in bet_new:
            notification_text += f'`{key}: {bet_new[key]}`\n'
        notification_text = notification_text.replace('.', '\\.')
        # Format telegram bot API request and send the notification message
        #   Includes a button to press for additional team news information
        #   callback_data is a unique identifier for when the button is pressed
        path = f'/bot{self.TG_BOT_TOKEN}/sendMessage'
        uri = self.API_HOST + path
        inline_keyboard_button = [[{
            'text': 'Tell me more...',
            'callback_data': fixture
        }]]
        inline_keyboard_markup = {
            'inline_keyboard': inline_keyboard_button
        }
        inline_keyboard_markup_json = json.dumps(inline_keyboard_markup)
        params = {
            'chat_id': chat_id,
            'text': notification_text,
            'parse_mode': 'MarkdownV2',
            'reply_markup': inline_keyboard_markup_json
        }
        response = requests.get(uri, params=params)
        return response

    def parse_news(self, celery_response, fixture):
        # Parse response to form news message
        news = celery_response[1][0]
        news_notification = ''
        for key in news:
            data = news[key]
            news_notification += f'__*{key}*__\n'
            news_notification += f'`{data["formation"]} formation`\n\n'
            news_notification += f'Coach:\n`{data["coach"]}`\n\n'
            news_notification += 'Starting XI:\n'
            for i in data['startXI']:
                news_notification += f'`{i["number"]:2}  {i["player"]}`\n'
            news_notification += '\nSubstitutes:\n'
            for i in data['substitutes']:
                news_notification += f'`{i["number"]:2}  {i["player"]}`\n'
            news_notification += '\n\n'
        news_notification = news_notification.replace('-', '\\-')
        news_notification = news_notification.replace('.', '\\.')
        # Store the news message in a database in case it is asked for
        #    Uses the fixture number as a unique identifier in the db
        fpsql = FootballPostgresql()
        fpsql.write_news(fixture, news_notification)
