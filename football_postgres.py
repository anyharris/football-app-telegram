# football_postgres.py
'''
This part is done
'''
import psycopg2
import datetime


class FootballPostgresql():
    DATABASE = 'football_bot'

    def __init__(self):
        self.con = psycopg2.connect(database=self.DATABASE, host='localhost', user='postgres',
                                    password='NjURWXzJgVs3fEAR')

    def write_news(self, message_id, news_message):
        time_stamp = datetime.datetime.now()
        entities = (time_stamp, message_id, news_message)
        cursorObj = self.con.cursor()
        cursorObj.execute(
            'INSERT INTO news_messages (time_stamp, message_id, message_text) VALUES (%s,%s,%s)', entities)
        self.con.commit()

    def read_news(self, message_id):
        cursorObj = self.con.cursor()
        cursorObj.execute(
            'SELECT message_text FROM news_messages WHERE message_id=(%s)', (message_id,))
        return cursorObj.fetchall()
