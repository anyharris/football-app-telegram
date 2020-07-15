# api_wrappers.py
import requests
import json


def _get(uri, headers=None, params=None):
    response = requests.get(uri, headers=headers, params=params)
    return response


class APIFootball:
    API_HOST = 'https://api-football-v1.p.rapidapi.com'

    def __init__(self, api_key, season):
        self.API_KEY = api_key
        self.SEASON = f'{season}-{season+1}'

    def _headers(self):
        headers = {
            'x-rapidapi-host': self.API_HOST[8:],
            'x-rapidapi-key': self.API_KEY
        }
        return headers

    def get_fixtures_leaguedate(self, league_id, date):
        path = f'/v2/fixtures/league/{league_id}/{date}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_news(self, fixture_id):
        path = f'/v2/lineups/{fixture_id}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_league(self, league_id):
        path = f'/v2/leagueTable/{league_id}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_player_search(self, search_term):
        path = f'/v2/players/search/{search_term}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_player_id(self, player_id):
        path = f'/v2/players/player/{player_id}/{self.SEASON}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_squad(self, team_id):
        path = f'/v2/players/squad/{team_id}/{self.SEASON}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_league_search(self, search_term):
        path = f'/v2/leagues/search/{search_term}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response

    def get_teams(self, league_id):
        path = f'/v2/teams/league/{league_id}'
        uri = self.API_HOST + path
        headers = self._headers()
        response = _get(uri, headers=headers)
        return response


class TheOdds:
    API_HOST = 'https://api.the-odds-api.com'

    def __init__(self, api_key):
        self.API_KEY = api_key

    def get_odds_theodds(self):
        path = f'/v3/odds/'
        uri = self.API_HOST + path
        params = {
            'apiKey': self.API_KEY,
            'sport': 'soccer_epl',
            'region': 'uk',
            'mkt': 'h2h'
        }
        response = _get(uri, params=params)
        return response


class Telegram:
    API_HOST = 'https://api.telegram.org'

    def __init__(self, bot_token):
        self.BOT_TOKEN = bot_token

    def callback_button_message(self, chat_id, message, identifier):
        path = f'/bot{self.BOT_TOKEN}/sendMessage'
        uri = self.API_HOST + path
        inline_keyboard_button = [[{
            'text': 'Show lineups',
            'callback_data': identifier
        }]]
        inline_keyboard_markup = {
            'inline_keyboard': inline_keyboard_button
        }
        inline_keyboard_markup_json = json.dumps(inline_keyboard_markup)
        params = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'MarkdownV2',
            'reply_markup': inline_keyboard_markup_json
        }
        response = _get(uri=uri, params=params)
        return response
