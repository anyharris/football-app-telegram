from dotenv import load_dotenv
import os
import psycopg2
import logging
import traceback

DATABASE = 'football_bot'

load_dotenv()
psql_host = os.getenv('POSTGRES_HOST')
psql_user = os.getenv('POSTGRES_USER')
psql_password = os.getenv('POSTGRES_PASS')
#    Connecting to psql DB
try:
    con = psycopg2.connect(database=DATABASE, host=psql_host, user=psql_user, password=psql_password)
    cursorObj = con.cursor()
except Exception as err:
    '''
    Stop the program if it can't connect
    '''
    logging.error(err)
    logging.error(traceback.format_exc())
    sys.exit()
#   Creating postgres table if there isn't one already
try:
    cursorObj.execute('CREATE TABLE news_messages (id serial PRIMARY KEY, time_stamp text, message_id text, message_text text)')
    con.commit()
    logging.info('created the table')
except Exception as err:
    logging.info(err)
    logging.debug(traceback.format_exc())