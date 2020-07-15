# football_tg_bot.py
"""
to run:
nohup python football_tg_bot.py > football_tg_bot.log &
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler
from modules.postgres_methods import FootballPostgres
import modules.response_parser as rp
from modules.api_wrappers import APIFootball, TheOdds
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime

load_dotenv()
SEASON = int(os.getenv('SEASON'))
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
API_KEY_APIFOOTBALL = os.getenv('API_KEY_APIFOOTBALL')
API_KEY_THEODDS = os.getenv('API_KEY_THEODDS')
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASS = os.getenv('POSTGRES_PASS')

apif = APIFootball(API_KEY_APIFOOTBALL, SEASON)
todds = TheOdds(API_KEY_THEODDS)
fpsg = FootballPostgres(POSTGRES_DATABASE, POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASS)

with open('data/league_data.txt') as league_data_file:
    league_data = json.load(league_data_file)
LEAGUE_ID = league_data['APIFootball_league_ID']

logging.basicConfig(filename='tg_bot.log', level=logging.INFO)


def callback_query_handler(update, context):
    bot = context.bot
    cqd = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if cqd[0] == 'f':
        logging.info(f'news callback for cqd {cqd}')
        msg_text = fpsg.read_news(cqd[1:])
        msg_text = msg_text[0][0]
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
        logging.info(f'sent request for cqd {cqd}')
    elif cqd[0] == 'p':
        logging.info(f'player callback for cqd {cqd}')
        response = apif.get_player_id(cqd[1:]).json()
        msg_text = rp.player_stats(response)
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        logging.warning("Button click didn't callback anything")


def league_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    response = apif.get_league(LEAGUE_ID).json()
    msg_text = rp.league(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def player_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    search_term = context.args[0]
    response = apif.get_player_search(search_term).json()
    player_list = rp.player_search(response)
    if len(player_list) == 0:
        msg_text = 'No search results\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    elif len(player_list) > 4:
        msg_text = 'Too many search results\\, please be more specific\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        if len(player_list) == 1:
            response = apif.get_player_id(player_list[0]['player_id']).json()
            msg_text = rp.player_stats(response)
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
    msg_text = rp.fixtures(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="All set!")
    try:
        with open('data/chat_ids.txt') as chat_ids_file:
            chat_dict = json.load(chat_ids_file)
        chat_ids = chat_dict['chat_ids']
    except IOError:
        chat_ids = []
    chat_ids.append(update.effective_chat.id)
    chat_dict = {'chat_ids': chat_ids}
    with open('data/chat_ids.txt', 'w') as outfile:
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
