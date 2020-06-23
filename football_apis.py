# football_apis.py
'''
Ready for production
Should add exception handling though
'''
import requests
from dotenv import load_dotenv
import os


class Football:
    LEAGUE_ID_APIFOOTBALL = 524  # German bundesliga 2019 is 754. English prem 2019 is 524
    API_HOST_APIFOOTBALL = 'https://api-football-v1.p.rapidapi.com'
    API_HOST_THEODDS = 'https://api.the-odds-api.com'
    SEASON = '2019'

    def __init__(self):
        load_dotenv()
        self.API_KEY_APIFOOTBALL = os.getenv('API_KEY_APIFOOTBALL')
        self.API_KEY_THEODDS = os.getenv('API_KEY_THEODDS')

    def _headers(self):
        headers = {
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
            'x-rapidapi-key': self.API_KEY_APIFOOTBALL
        }
        return headers

    def _get_theodds(self, path):
        uri = self.API_HOST_THEODDS+path
        response = requests.get(uri)
        return response

    def _get_apifootball(self, path, headers, querystring=None):
        uri = self.API_HOST_APIFOOTBALL+path
        response = requests.get(uri, headers=headers, params=querystring)
        return response

    def get_fixtures_leaguedate(self, date):
        path = f'/v2/fixtures/league/{self.LEAGUE_ID_APIFOOTBALL}/{date}'
        headers = self._headers()
        response = self._get_apifootball(path=path, headers=headers)
        return response

    def get_news(self, fixture_id):
        path = f'/v2/lineups/{fixture_id}'
        headers = self._headers()
        response = self._get_apifootball(path=path, headers=headers)
        return response

    def get_odds_theodds(self):
        path = f'/v3/odds/?apiKey={self.API_KEY_THEODDS}&sport=soccer_epl&region=uk&mkt=h2h'
#        path = f'/v3/odds/?apiKey={self.API_KEY_THEODDS}&sport=soccer_germany_bundesliga&region=eu&mkt=h2h'
        response = self._get_theodds(path=path)
        return response

    def get_league(self):
        path = f'/v2/leagueTable/{self.LEAGUE_ID_APIFOOTBALL}'
        headers = self._headers()
        response = self._get_apifootball(path=path, headers=headers)
        return response

    def get_player_search(self, search_term):
        print('f1')
        path = f'/v2/players/search/{search_term}'
        print(path)
        headers = self._headers()
        response = self._get_apifootball(path=path, headers=headers)
        print('f2')
        return response

    def get_player_id(self, player_id):
        path = f'/v2/players/player/{player_id}/{self.SEASON}'
        headers = self._headers()
        response = self._get_apifootball(path=path, headers=headers)
        return response
