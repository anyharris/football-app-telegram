# response_parser.py
'''
Add parser for league and individual players
'''
import json
import time

# This TEAMS_SHORT thing is going to break next season. I'll fix it sometime if I want to run the bot next year
TEAMS_SHORT = ['BOU', 'ARS', 'AVA', 'BRH', 'BUR', 'CHE', 'CRY',
               'EVE', 'LEI', 'LIV', 'MCI', 'MUN', 'NEW', 'NOR',
               'SHU', 'SOU', 'TOT', 'WAT', 'WHU', 'WLV']
with open('data/league_data.txt') as json_file:
    league_data = json.load(json_file)
TEAMS_LONG = league_data['APIFootball_team_names']
PREM_PLAYERS = league_data['APIFootball_player_IDs']


def _weird_division(n, d):
    return n / d if d else 0


def notification(celery_response):
    # Parse celery response to form notification message
    bet_old = celery_response[0]
    bet_new = celery_response[1][1]
    news_dict = celery_response[1][0]
    teams = list(news_dict)
    text = f'__*{teams[0]}* vs *{teams[1]}*__\n'
    text += f'`      70mins  Post-news`\n'
    for key in bet_old:
        text += f'`{key}: {bet_old[key]:<5}   {bet_new[key]}`\n'
    text = text.replace('.', '\\.')
    return text


def news(celery_response, fixture):
    # Parse response to form news message
    news_dict = celery_response[1][0]
    text = ''
    for key in news_dict:
        data = news_dict[key]
        text += f'__*{key}*__\n'
        text += f'`{data["formation"]} formation`\n\n'
        text += 'Starting XI:\n'
        for player in data['startXI']:
            text += f'`{player["number"]:2}  {player["player"]}`\n'
        text += '\nSubstitutes:\n'
        for player in data['substitutes']:
            text += f'`{player["number"]:2}  {player["player"]}`\n'
        text += '\n\n'
    text = text.replace('-', '\\-')
    text = text.replace('.', '\\.')
    # Store the news message in a database in case it is asked for
    #    Uses the fixture number as a unique identifier in the db
    return text


def league(request_response):
    league_dict = request_response['api']['standings'][0]
    text = '```'
    text += f'      P  W  D  L  GF GA  GD Pts\n'
    for team in league_dict:
        team_long = team["teamName"]
        team_position = TEAMS_LONG.index(team_long)
        team_short = TEAMS_SHORT[team_position]
        text += f'{team_short:3}  {team["all"]["matchsPlayed"]:>2} {team["all"]["win"]:>2} {team["all"]["draw"]:>2} ' \
                f'{team["all"]["lose"]:>2}  {team["all"]["goalsFor"]:>2} {team["all"]["goalsAgainst"]:>2} ' \
                f'{team["goalsDiff"]:>3} {team["points"]:>3}\n'
    text += '```'
    text = text.replace('-', '\\-')
    return text


def player_search(request_response):
    players_list = request_response['api']['players']
    players_list[:] = [i for i in players_list if (i['player_id'] in PREM_PLAYERS)]
    text = []
    for player in players_list:
        text.append(player)
    return text


def fixtures(request_response):
    fixtures_list = request_response['api']['fixtures']
    text = '__*Today\'s Fixtures*__\n'
    for fixture in fixtures_list:
        text += f'{fixture["homeTeam"]["team_name"]} vs {fixture["awayTeam"]["team_name"]}\n'
        text += f'`{time.strftime("%d-%m %H:%M", time.gmtime(fixture["event_timestamp"]))} in England`\n'
        text += f'`{time.strftime("%d-%m %H:%M", time.localtime(fixture["event_timestamp"]))} in Thailand`\n\n'
    text = text[:-1]
    text = text.replace('-', '\\-')
    return text


def player_stats(request_response):
    raw_stats = request_response['api']['players']
    raw_stats[:] = [i for i in raw_stats if (i['league'] == 'Premier League')]
    player = raw_stats[0]
    text = f'{player["firstname"]} {player["lastname"]}\n'
    text += f'Birth date: {player["birth_date"]}\n'
    text += f'Games:\n `appeared: {player["games"]["appearences"]}, mins: {player["games"]["minutes_played"]}`\n'
    text += f'Goals:\n `tot: {player["goals"]["total"]}, assists: {player["goals"]["assists"]}`\n'
    text += f'Shots:\n `tot: {player["shots"]["total"]}, on: {"{:.0%}".format(_weird_division(player["shots"]["on"], player["shots"]["total"]))}`\n'
    text += f'Passes:\n `tot: {player["passes"]["total"]}, key: {player["passes"]["key"]}, acc: {player["passes"]["accuracy"]}%`\n'
    text += f'Tackles:\n `tot: {player["tackles"]["total"]}, blk: {player["tackles"]["blocks"]}, int: {player["tackles"]["interceptions"]}`\n'
    text += f'Duels:\n `tot: {player["duels"]["total"]}, won: {"{:.0%}".format(_weird_division(player["duels"]["won"], player["duels"]["total"]))}`\n'
    text += f'Dribbles:\n `att: {player["dribbles"]["attempts"]}, success: {"{:.0%}".format(_weird_division(player["dribbles"]["success"], player["dribbles"]["attempts"]))}`'
    text = text.replace('-', '\\-')
    return text
