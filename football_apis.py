# football_apis.py
'''
I need a better API for real time match data
'''
import requests


class Football:
    API_HOST = 'https://api-football-v1.p.rapidapi.com/v2'
    BOOKMAKER_ID = 3  # Betfair. Pinnacle is 4
    LEAGUE_ID = 524  # German bundesliga is 754. 524 is english prem
    API_KEY = '9a3a7d1d81msh7c32f567f3666e0p12ad03jsndd531285bac1'

    API_KEY_THEODDS = 'c2badc9ffea53e976b5420fc2a623ac6'
    API_HOST_THEODDS = 'https://api.the-odds-api.com'

    def __init__(self, api_key=None):
        pass
 #       self.API_KEY = api_key

    def _headers(self):
        headers = {
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
            'x-rapidapi-key': self.API_KEY
        }
        return headers

    def _get_theodds(self, path):
        uri = self.API_HOST_THEODDS+path
        response = requests.get(uri)
        return response

    def _get(self, path, headers=None, querystring=None):
        uri = self.API_HOST+path
        response = requests.get(uri, headers=headers, params=querystring)
        return response

    def get_odds_fixture(self, fixture_id):
        path = f'/odds/fixture/{fixture_id}/bookmaker/{self.BOOKMAKER_ID}'
        headers = self._headers()
        response = self._get(path=path, headers=headers)
        return response

    def get_fixtures_leaguedate(self, date):
        path = f'/fixtures/league/{self.LEAGUE_ID}/{date}'
        headers = self._headers()
        response = self._get(path=path, headers=headers)
        return response

    def get_news(self, fixture_id):
        path = f'/lineups/{fixture_id}'
        headers = self._headers()
        response = self._get(path=path, headers=headers)
        return response

    def get_odds_theodds(self):
        path = f'/v3/odds/?apiKey={self.API_KEY_THEODDS}&sport=soccer_epl&region=uk&mkt=h2h'
        response = self._get_theodds(path=path)
        return response
