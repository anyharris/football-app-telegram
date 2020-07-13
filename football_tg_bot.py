# football_tg_bot.py
"""
to run:
nohup python football_tg_bot.py > football_tg_bot.log &
v1: 1226601001:AAEPGWAChBRbk93RMaJ5GtD8sdEgyHxGAtI
v2: 1266321518:AAG46QcdxkoebdmnTLMPabIYGI9hhCYiEIQ
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext
from football_postgres import FootballPostgresql
from football_response_parser import ResponseParser
from football_apis import APIFootball, TheOdds
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime

load_dotenv()
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
apif = APIFootball(api_key=os.getenv('API_KEY_APIFOOTBALL'), season=int(os.getenv('SEASON')))
todds = TheOdds(api_key=os.getenv('API_KEY_THEODDS'))
fpsql = FootballPostgresql()
rp = ResponseParser()
with open('league_data.txt') as json_file:
    league_data = json.load(json_file)
LEAGUE_ID = league_data['APIFootball_league_ID']


logging.basicConfig(filename='tg_bot.log', level=logging.INFO)


def callback_query_handler(update, context):
    bot = context.bot
    cqd = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if cqd[0] == 'f':
        logging.info(f'news callback for cqd {cqd}')
        msg_text = fpsql.read_news(cqd[1:])
        msg_text = msg_text[0][0]
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
        logging.info(f'sent request for cqd {cqd}')
    elif cqd[0] == 'p':
        logging.info(f'player callback for cqd {cqd}')
        response = apif.get_player_id(cqd[1:]).json()
        msg_text = rp.parse_player_stats(response)
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        logging.warning('Button click didn\'t callback anything')


def league_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    response = apif.get_league(LEAGUE_ID).json()
    msg_text = rp.parse_league(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def player_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    search_term = context.args[0]
    response = apif.get_player_search(search_term).json()
    player_list = rp.parse_player_search(response)
    if len(player_list) == 0:
        msg_text = 'No search results\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    elif len(player_list) > 4:
        msg_text = 'Too many search results\\, please be more specific\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        if len(player_list) == 1:
            response = apif.get_player_id(player_list[0]['player_id']).json()
            msg_text = rp.parse_player_stats(response)
            bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
        else:
            keyboard = []
            for i in player_list:
                keyboard.append([InlineKeyboardButton(i['player_name'], callback_data=f'p{i["player_id"]}')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)


def fixtures_today(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    date_today = str(datetime.utcnow().date())
    response = apif.get_fixtures_leaguedate(LEAGUE_ID, date_today).json()
    msg_text = rp.parse_fixtures(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="All set!")
    try:
        with open('chat_ids.txt') as json_file:
            chat_dict = json.load(json_file)
        chat_ids = chat_dict['chat_ids']
    except IOError:
        chat_ids = []
    chat_ids.append(update.effective_chat.id)
    chat_dict = {'chat_ids': chat_ids}
    with open('chat_ids.txt', 'w') as outfile:
        json.dump(chat_dict, outfile)


def main():
    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('league', league_stats))
    dp.add_handler(CommandHandler('player', player_stats, pass_args=True))
    dp.add_handler(CommandHandler('fixtures', fixtures_today))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
