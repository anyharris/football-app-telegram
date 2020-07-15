# update_teams_players.py
"""
This should be run every season, or maybe more often if the players are changing

I wish there was a good way to get the team abbreviations at the same time
Probably I could dig up an API somewhere that has them
"""
from modules.api_wrappers import TheOdds, APIFootball
import json
from dotenv import load_dotenv
import os
import sys

load_dotenv()
SEASON = int(os.getenv('SEASON'))    # storing in .env so it's easy to modify without making the local repo out of sync
todds = TheOdds(api_key=os.getenv('API_KEY_THEODDS'))
apif = APIFootball(api_key=os.getenv('API_KEY_APIFOOTBALL'), season=SEASON)

# Get the league ID for the current prem season
response = apif.get_league_search('premier_league').json()
league_id = None
for league in response['api']['leagues']:
    if league['country_code'] == 'GB' and league['season'] == SEASON:
        league_id = league['league_id']
if not league_id:
    print('Can\'t find the league ID')
    sys.exit()

# Get prem team names and ids from APIFootball
response = apif.get_teams(league_id).json()
apif_teams = []
apif_names = []
for team in response['api']['teams']:
    apif_teams.append(team['team_id'])
    apif_names.append(team['name'])
apif_names = (sorted(apif_names))

# Iterate through team IDs to get a list of all prem player IDs
apif_player_ids = []
for team_id in apif_teams:
    response = apif.get_squad(team_id).json()
    players = response['api']['players']
    for player in players:
        apif_player_ids.append(player["player_id"])

# Get prem team names from TheOdds
response = todds.get_odds_theodds().json()
todds_teams = []
for fixture in response['data']:
    todds_teams.append(fixture['teams'][0])
    todds_teams.append(fixture['teams'][1])
todds_teams = list(set(todds_teams))
todds_teams = (sorted(todds_teams))

# Store all of this as a json file
json_storage = {
    'APIFootball_league_ID': league_id,
    'APIFootball_team_names': apif_names,
    'APIFootball_player_IDs': apif_player_ids,
    'TheOdds_team_names': todds_teams
}
with open('league_data.txt', 'w') as outfile:
    json.dump(json_storage, outfile)

