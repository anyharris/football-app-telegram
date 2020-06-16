# football_tg_bot.py
'''
This part is done
'''
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext
from football_postgres import FootballPostgresql
import requests

TG_BOT_TOKEN = '1241564289:AAGHB2cruHbI9QzOGzNft6UaDy3PkU34y_k'
fpsql = FootballPostgresql()


def news_callback_query_handler(update, context):
    cqd = update.callback_query.data
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


def main():
    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(news_callback_query_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()