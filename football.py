import requests


class Football:
    API_HOST = 'https://api-football-v1.p.rapidapi.com/v2'
    BOOKMAKER_ID = 3  # Betfair. Pinnacle is 4
    LEAGUE_ID = 754  # German bundesliga

    def __init__(self, api_key):
        self.API_KEY = api_key

    def _headers(self):
        headers = {
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
            'x-rapidapi-key': self.API_KEY
        }
        return headers

    def _get(self, path, querystring=None):
        uri = self.API_HOST+path
        headers = self._headers()
        response = requests.get(uri, headers=headers, params=querystring)
        return response

    def get_odds_fixture(self, fixture_id):
        path = f'/odds/fixture/{fixture_id}/bookmaker/{self.BOOKMAKER_ID}'
        response = self._get(path=path)
        return response

    def get_fixtures_leaguedate(self, date):
        path = f'/fixtures/league/{self.LEAGUE_ID}/{date}'
        response = self._get(path=path)
        return response

    def get_news(self, fixture_id):
        path = f'/lineups/{fixture_id}'
        response = self._get(path=path)
        return response
