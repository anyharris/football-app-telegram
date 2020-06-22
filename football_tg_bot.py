# football_tg_bot.py
'''
add handlers for league and player stats

nohup python football_tg_bot.py > football_tg_bot.log &
'''
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext
from football_postgres import FootballPostgresql
from football_response_parser import ResponseParser
from football_apis import Football
import requests
from dotenv import load_dotenv
import os
import logging
from datetime import date
import json

load_dotenv()
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
fpsql = FootballPostgresql()
rp = ResponseParser()
fb = Football()
logging.basicConfig(filename='tg_bot.log', level=logging.INFO)


def news_callback_query_handler(update, context):
    cqd = update.callback_query.data
    logging.info(f'news callback for cqd {cqd}')
    news = fpsql.read_news(cqd)
    chat_id = update.callback_query.message.chat_id
    API_HOST = 'https://api.telegram.org'
    path = f'/bot{TG_BOT_TOKEN}/sendMessage'
    uri = API_HOST + path
    params = {
        'chat_id': chat_id,
        'text': news,
        'parse_mode': 'MarkdownV2',
    }
    requests.get(uri, params=params)
    logging.info(f'sent request for cqd {cqd}')


def league_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    response = fb.get_league().json()
    msg_text = rp.parse_league(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def player_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    search_term = context.args
    response = fb.get_player(search_term)
    msg_text = rp.parse_player(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def fixtures_today(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    date_today = str(date.today())
    response = fb.get_fixtures_leaguedate(date_today).json()
    msg_text = rp.parse_fixtures(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def main():
    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(news_callback_query_handler))
    dp.add_handler(CommandHandler('league', league_stats))
    dp.add_handler(CommandHandler('player', player_stats, pass_args=True))
    dp.add_handler(CommandHandler('fixtures', fixtures_today))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()