# football_response_parser.py
'''
This part is done
'''
import requests
import json
from football_postgres import FootballPostgresql


class ResponseParser:
    def __init__(self):
        self.TG_BOT_TOKEN = '1241564289:AAGHB2cruHbI9QzOGzNft6UaDy3PkU34y_k'
        self.TG_CHAT_ID = 173075290
        self.API_HOST = 'https://api.telegram.org'

    def parse_notification(self, fixture, celery_response):
        # Parse response to form notification message
        bet_old = celery_response[0]
        bet_new = celery_response[1][1]
        news = celery_response[1][0]
        teams = list(news)
        notification_text = f'__*{teams[0]}* vs *{teams[1]}*__\n'
        notification_text += f'Odds 24h before:\n'
        for i in bet_old[::-1]:
            notification_text += f'`{list(i.values())[0]}: {list(i.values())[1]:4}`\n'
        notification_text += '\nOdds after team news:\n'
        for i in bet_new[::-1]:
            notification_text += f'`{list(i.values())[0]}: {list(i.values())[1]:4}`\n'
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
            'chat_id': self.TG_CHAT_ID,
            'text': notification_text,
            'parse_mode': 'MarkdownV2',
            'reply_markup': inline_keyboard_markup_json
        }
        response = requests.get(uri, params=params)
        return response

    def parse_news(self, fixture, celery_response):
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
