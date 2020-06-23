# football_response_parser.py
'''
Add parser for league and individual players
'''
import requests
import json
from football_postgres import FootballPostgresql
from dotenv import load_dotenv
import os
import time


class ResponseParser:
    API_HOST = 'https://api.telegram.org'
    TEAMS_SHORT = ['BOU', 'ARS', 'AVA', 'BRH', 'BUR', 'CHE', 'CRY',
                   'EVE', 'LEI', 'LIV', 'MCI', 'MUN', 'NEW', 'NOR',
                   'SHU', 'SOU', 'TOT', 'WAT', 'WHU', 'WLV']
    TEAMS_LONG = ['Bournemouth', 'Arsenal', 'Aston Villa', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace',
                  'Everton', 'Leicester', 'Liverpool', 'Manchester City', 'Manchester United', 'Newcastle', 'Norwich',
                  'Sheffield Utd', 'Southampton', 'Tottenham', 'Watford', 'West Ham', 'Wolves']

    PREM_PLAYERS = [138832, 138831, 152974, 152976, 152977, 291, 1756, 303, 19613, 19937, 18812, 20224, 281, 162687,
                    290, 287, 284, 289, 286, 285, 138780, 138825, 18862, 97938, 138828, 138826, 152979, 36922, 296, 294,
                    292, 295, 307, 293, 19035, 138830, 152975, 93671, 151754, 138829, 151755, 301, 304, 306, 1101,
                    196876, 44798, 127472, 280, 299, 302, 305, 300, 283, 297, 19640, 19064, 19080, 19087, 47521, 2049,
                    19061, 147834, 19070, 19287, 19073, 19066, 19069, 2804, 720, 19082, 19075, 19074, 19072, 19071,
                    19078, 19081, 19079, 138799, 25643, 130417, 19067, 396, 19085, 19077, 19062, 19076, 25349, 18832,
                    18822, 18820, 90497, 2886, 90506, 18821, 47326, 2997, 19629, 144709, 18813, 18818, 41301, 18817,
                    18814, 18815, 18816, 2412, 2473, 18828, 18827, 18826, 1697, 18829, 18819, 144715, 18823, 19428,
                    1826, 193296, 2500, 2812, 18834, 1243, 2937, 19229, 637, 105971, 615, 227, 638, 617, 19197, 627,
                    641, 622, 619, 144730, 144729, 634, 640, 631, 628, 144732, 644, 635, 618, 643, 624, 642, 614, 629,
                    626, 645, 44, 623, 633, 855, 636, 18871, 151757, 45096, 18877, 18047, 18859, 20355, 151756, 18865,
                    18863, 18864, 18869, 19769, 18867, 18868, 19263, 196000, 114756, 18874, 18879, 18876, 18872, 18878,
                    18870, 18873, 2734, 130416, 18880, 18883, 83, 18884, 180289, 18858, 2490, 18866, 19221, 18861, 2939,
                    18881, 18860, 19098, 19096, 48105, 82004, 8924, 19089, 19090, 19095, 19091, 18759, 19094, 19294,
                    971, 19104, 19592, 19105, 19302, 19481, 19109, 18882, 19567, 12555, 19088, 19102, 19337, 1934,
                    19236, 19093, 19097, 19108, 19462, 18928, 18923, 87791, 18913, 19597, 18908, 18909, 18916, 18918,
                    2936, 18917, 18914, 21383, 18912, 17711, 19886, 18922, 2790, 19268, 18926, 18925, 180771, 18927,
                    18931, 19169, 18930, 18929, 137299, 2288, 18911, 19115, 18915, 18921, 18924, 119878, 47430, 18932,
                    18951, 18939, 18950, 19480, 47421, 190, 18935, 18933, 18934, 18943, 18940, 18936, 171, 130420,
                    25287, 18942, 19232, 2114, 18949, 2938, 2710, 18948, 130421, 18956, 18955, 19524, 18957, 130422,
                    18947, 18944, 2735, 2999, 18945, 18946, 18837, 68125, 182282, 18848, 18850, 90495, 45027, 18857,
                    18998, 82227, 18835, 18847, 18844, 18839, 18842, 18843, 2281, 68124, 18840, 182201, 18851, 2991,
                    18854, 18849, 18763, 20055, 199312, 18853, 3428, 3247, 18768, 18836, 2928, 18845, 18852, 153424,
                    2727, 19728, 18763, 18768, 18756, 18755, 19150, 18757, 2934, 102, 18758, 37146, 630, 1455, 18764,
                    18761, 18765, 3240, 18762, 19550, 83422, 18766, 18769, 877, 19009, 138787, 2413, 2484, 2932, 2724,
                    2795, 148099, 50101, 1374, 1107, 18770, 19760, 18774, 18773, 3421, 18738, 18781, 18777, 18778,
                    18779, 18782, 18785, 18786, 18788, 2778, 18906, 127580, 18780, 18776, 18146, 2925, 2926, 2728, 2933,
                    18784, 18771, 18772, 152961, 18747, 41557, 152959, 123437, 741, 18738, 18737, 18736, 130418, 18739,
                    18741, 18740, 18745, 18744, 82022, 152957, 1853, 18746, 125705, 2716, 152963, 149564, 158432, 518,
                    152947, 1864, 2887, 18753, 2584, 1649, 2922, 2674, 1605, 2676, 2677, 2678, 18742, 44807, 18792,
                    191972, 18790, 47251, 18789, 18791, 44775, 18796, 19147, 18798, 18799, 18794, 18795, 18797, 191977,
                    195759, 191975, 18804, 18803, 18805, 18806, 18807, 127470, 18802, 30812, 2475, 195760, 195761,
                    191976, 17926, 195762, 18809, 18808, 1469, 10329, 18810, 2777, 2218, 17878, 20378, 82131, 18811,
                    18801, 30816, 2860, 18793, 18966, 93168, 18976, 138792, 18981, 3398, 2767, 19593, 18960, 18958,
                    138815, 18963, 19265, 30743, 18965, 18964, 18961, 82948, 137300, 151752, 18977, 18968, 18970, 18973,
                    137301, 138791, 100079, 151753, 138790, 639, 138881, 19364, 2700, 18982, 18980, 138877, 18978,
                    17715, 6716, 2741, 1946, 19050, 18975, 18962, 19772, 43071, 181, 19393, 156428, 159, 160, 158, 161,
                    170, 163, 149550, 154800, 176, 175, 19032, 172, 178, 180, 569, 162076, 186, 244, 171, 113, 168, 166,
                    1578, 164, 162, 174, 167, 182, 184, 662, 179, 149551, 19180, 19171, 19189, 19178, 3245, 19192,
                    19175, 19174, 2931, 1624, 19354, 18941, 21999, 21636, 19186, 19177, 2288, 19190, 19187, 76, 19195,
                    19533, 2664, 153506, 19185, 47370, 1945, 137302, 44791, 47522, 84, 19181, 2758, 19179, 19191, 19172,
                    19188, 19173, 82100, 18888, 68127, 19163, 18900, 18887, 18885, 18892, 2806, 18894, 1813, 18893,
                    18896, 18895, 20168, 68126, 18904, 22173, 19299, 18903, 18899, 3423, 18901, 409, 130419, 18831, 723,
                    19166, 18905, 138905, 133246, 18897, 2507, 25353, 167, 2855, 18886, 18891, 1436, 1466, 138840,
                    138784, 1161, 1447, 20386, 1439, 1117, 1450, 1440, 1448, 19016, 46792, 2283, 190, 138781, 1446, 748,
                    1458, 1456, 1463, 1460, 138835, 1467, 1465, 3246, 727, 1468, 127769, 1455, 1445, 1457, 19599, 1464,
                    1462, 1454, 1438, 1442, 44873, 890, 883, 884, 138804, 885, 888, 886, 891, 18846, 19182, 138806,
                    138807, 19018, 138775, 153429, 158699, 904, 901, 900, 899, 905, 896, 902, 895, 903, 138809, 138814,
                    908, 12975, 897, 906, 138808, 138776, 894, 19329, 70335, 907, 2935, 909, 882, 889, 1485, 106721,
                    2277, 67971, 18902, 2275, 2276, 2285, 2278, 19545, 2280, 21996, 138816, 2287, 2292, 17, 130423,
                    138777, 19611, 2299, 138822, 2283, 138815, 2288, 2286, 2294, 2284, 2289, 2927, 2282, 2291, 19209,
                    19220, 19194, 2298, 2273, 2726, 2290, 2295]

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
        print('p1')
        players = request_response['api']['players']
        print(players)
        players[:] = [i for i in players if (i['player_id'] in self.PREM_PLAYERS)]
        print(players)
        text = []
        for i in players:
            text.append(i)
        print('p2')
        return text

    def parse_fixtures(self, request_response):
        fixtures = request_response['api']['fixtures']
        text = '__*Today\'s Fixtures*__\n'
        for i in fixtures:
            text += f'{i["homeTeam"]["team_name"]} vs {i["awayTeam"]["team_name"]}\n'
            text += f'`{time.strftime("%d-%m %H:%M", time.gmtime(i["event_timestamp"]))} in England`\n'
            text += f'`{time.strftime("%d-%m %H:%M", time.localtime(i["event_timestamp"]))} in Thailand`\n'
        text = text[:-1]
        text = text.replace('-', '\\-')
        return text

    def parse_player_stats(self, request_response):
        print('x1')
        raw_stats = request_response['api']['players']
        print(raw_stats)
        raw_stats[:] = [i for i in raw_stats if (i['league'] == 'Premier League')]
        print(raw_stats)
        player = raw_stats[0]
        text = f'{player["firstname"]} {player["lastname"]}\n'
        text += f'Birth date: {player["birth_date"]}\n'
        text += f'Games:\n `appeared: {player["games"]["appearences"]}, mins: {player["games"]["minutes_played"]}`\n'
        text += f'Goals:\n `tot: {player["goals"]["total"]}, assists: {player["goals"]["assists"]}`\n'
        text += f'Shots:\n `tot: {player["shots"]["total"]}, on: {"{:.0%}".format(player["shots"]["on"]/player["shots"]["total"])}`\n'
        text += f'Passes:\n `tot: {player["passes"]["total"]}, key: {player["passes"]["key"]}, acc: {player["passes"]["accuracy"]}%`\n'
        text += f'Tackles:\n `tot: {player["tackles"]["total"]}, blk: {player["tackles"]["blocks"]}, int: {player["tackles"]["interceptions"]}`\n'
        text += f'Duels:\n `tot: {player["duels"]["total"]}, won: {"{:.0%}".format(player["duels"]["won"]/player["duels"]["total"])}`\n'
        text += f'Dribbles:\n `att: {player["dribbles"]["attempts"]}, success: {"{:.0%}".format(player["dribbles"]["success"]/player["dribbles"]["attempts"])}`'
        #text += f'Fouls:\n `drawn: {player["fouls"]["drawn"]}  committed: {player["fouls"]["committed"]}`\n'
        #text += f'Cards:\n `yellow: {player["cards"]["yellow"]}  red:{player["cards"]["red"]}`\n'
        #text += f'Penalty:\n `won: {player["penalty"]["won"]}  com: {player["penalty"]["commited"]}  suc: {player["penalty"]["success"]}  miss: {player["penalty"]["missed"]}  saved: {player["penalty"]["saved"]}`\n'
        #text += f'Substitutes:\n `in: {player["substitutes"]["in"]}  out: {player["substitutes"]["out"]}  bench: {player["substitutes"]["bench"]}`'
        text = text.replace('-', '\\-')
        return text
