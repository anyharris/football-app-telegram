# football_tg_bot.py
'''
Ready for production
nohup python football_tg_bot.py > football_tg_bot.log &
'''
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext
from football_postgres import FootballPostgresql
import requests
from dotenv import load_dotenv
import os
import logging

load_dotenv()
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
fpsql = FootballPostgresql()
logging.basicConfig(filename='tg_bot.log', level=logging.DEBUG)


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


def main():
    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(news_callback_query_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()