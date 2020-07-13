# response_parser.py
'''
Add parser for league and individual players
'''
import requests
import json
from postgres_methods import FootballPostgresql
from dotenv import load_dotenv
import os
import time


class ResponseParser:
    API_HOST = 'https://api.telegram.org'
    # This TEAMS_SHORT thing is going to break next season. I'll fix it sometime if I want to run the bot next year
    TEAMS_SHORT = ['BOU', 'ARS', 'AVA', 'BRH', 'BUR', 'CHE', 'CRY',
                   'EVE', 'LEI', 'LIV', 'MCI', 'MUN', 'NEW', 'NOR',
                   'SHU', 'SOU', 'TOT', 'WAT', 'WHU', 'WLV']

    def __init__(self):
        load_dotenv()
        self.TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
        with open('league_data.txt') as json_file:
            league_data = json.load(json_file)
        self.TEAMS_LONG = league_data['APIFootball_team_names']
        self.PREM_PLAYERS = league_data['APIFootball_player_IDs']

    def _weird_division(self, n, d):
        return n / d if d else 0

    def parse_notification(self, celery_response, fixture, chat_id):
        # Parse response to form notification message
        bet_old = celery_response[0]
        bet_new = celery_response[1][1]
        news = celery_response[1][0]
        teams = list(news)
        notification_text = f'__*{teams[0]}* vs *{teams[1]}*__\n'
        notification_text += f'`      70mins  Post-news`\n'
        for key in bet_old:
            notification_text += f'`{key}: {bet_old[key]:<5}   {bet_new[key]}`\n'
        notification_text = notification_text.replace('.', '\\.')
        # Format telegram bot API request and send the notification message
        #   Includes a button to press for additional team news information
        #   callback_data is a unique identifier for when the button is pressed
        path = f'/bot{self.TG_BOT_TOKEN}/sendMessage'
        uri = self.API_HOST + path
        inline_keyboard_button = [[{
            'text': 'Show lineups',
            'callback_data': f'f{fixture}'
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

    def parse_league(self, request_response):
        standings = request_response['api']['standings']
        text = '```'
        text += f'      P  W  D  L  GF GA  GD Pts\n'
        for i in standings[0]:
            team_long = i["teamName"]
            team_position = self.TEAMS_LONG.index(team_long)
            team_short = self.TEAMS_SHORT[team_position]
            text += f'{team_short:3}  {i["all"]["matchsPlayed"]:>2} {i["all"]["win"]:>2} {i["all"]["draw"]:>2} ' \
                    f'{i["all"]["lose"]:>2}  {i["all"]["goalsFor"]:>2} {i["all"]["goalsAgainst"]:>2} {i["goalsDiff"]:>3} ' \
                    f'{i["points"]:>3}\n'
        text += '```'
        text = text.replace('-', '\\-')
        return text

    def parse_player_search(self, request_response):
        players = request_response['api']['players']
        players[:] = [i for i in players if (i['player_id'] in self.PREM_PLAYERS)]
        text = []
        for i in players:
            text.append(i)
        return text

    def parse_fixtures(self, request_response):
        fixtures = request_response['api']['fixtures']
        text = '__*Today\'s Fixtures*__\n'
        for i in fixtures:
            text += f'{i["homeTeam"]["team_name"]} vs {i["awayTeam"]["team_name"]}\n'
            text += f'`{time.strftime("%d-%m %H:%M", time.gmtime(i["event_timestamp"]))} in England`\n'
            text += f'`{time.strftime("%d-%m %H:%M", time.localtime(i["event_timestamp"]))} in Thailand`\n\n'
        text = text[:-1]
        text = text.replace('-', '\\-')
        return text

    def parse_player_stats(self, request_response):
        raw_stats = request_response['api']['players']
        raw_stats[:] = [i for i in raw_stats if (i['league'] == 'Premier League')]
        player = raw_stats[0]
        text = f'{player["firstname"]} {player["lastname"]}\n'
        text += f'Birth date: {player["birth_date"]}\n'
        text += f'Games:\n `appeared: {player["games"]["appearences"]}, mins: {player["games"]["minutes_played"]}`\n'
        text += f'Goals:\n `tot: {player["goals"]["total"]}, assists: {player["goals"]["assists"]}`\n'
        text += f'Shots:\n `tot: {player["shots"]["total"]}, on: {"{:.0%}".format(self._weird_division(player["shots"]["on"], player["shots"]["total"]))}`\n'
        text += f'Passes:\n `tot: {player["passes"]["total"]}, key: {player["passes"]["key"]}, acc: {player["passes"]["accuracy"]}%`\n'
        text += f'Tackles:\n `tot: {player["tackles"]["total"]}, blk: {player["tackles"]["blocks"]}, int: {player["tackles"]["interceptions"]}`\n'
        text += f'Duels:\n `tot: {player["duels"]["total"]}, won: {"{:.0%}".format(self._weird_division(player["duels"]["won"], player["duels"]["total"]))}`\n'
        text += f'Dribbles:\n `att: {player["dribbles"]["attempts"]}, success: {"{:.0%}".format(self._weird_division(player["dribbles"]["success"], player["dribbles"]["attempts"]))}`'
        text = text.replace('-', '\\-')
        return text
