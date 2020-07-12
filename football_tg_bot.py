# football_tg_bot.py
"""
to run:
nohup python football_tg_bot.py > football_tg_bot.log &
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext
from football_postgres import FootballPostgresql
from football_response_parser import ResponseParser
from football_apis import Football
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

load_dotenv()
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
fpsql = FootballPostgresql()
rp = ResponseParser()
fb = Football()
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
        response = fb.get_player_id(cqd[1:]).json()
        msg_text = rp.parse_player_stats(response)
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        logging.warning('Button click didn\'t callback anything')


def league_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    response = fb.get_league().json()
    msg_text = rp.parse_league(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def player_stats(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    search_term = context.args[0]
    response = fb.get_player_search(search_term).json()
    player_list = rp.parse_player_search(response)
    if len(player_list) == 0:
        msg_text = 'No search results\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    elif len(player_list) > 4:
        msg_text = 'Too many search results\\, please be more specific\\.'
        bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')
    else:
        if len(player_list) == 1:
            response = fb.get_player_id(player_list[0]['player_id']).json()
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
    response = fb.get_fixtures_leaguedate(date_today).json()
    msg_text = rp.parse_fixtures(response)
    bot.send_message(chat_id=chat_id, text=msg_text, parse_mode='MarkdownV2')


def main():
    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(CommandHandler('league', league_stats))
    dp.add_handler(CommandHandler('player', player_stats, pass_args=True))
    dp.add_handler(CommandHandler('fixtures', fixtures_today))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
