# postgres_methods.py
import psycopg2
import datetime


class FootballPostgres:
    def __init__(self, database, host, user, password):
        self.con = psycopg2.connect(database=database, host=host, user=user, password=password)
        cur = self.con.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS testing (id serial PRIMARY KEY, time_stamp text, message_id text, message_text text)')
        self.con.commit()

    def write_news(self, message_id, news_message):
        time_stamp = datetime.datetime.now()
        entities = (time_stamp, message_id, news_message)
        cur = self.con.cursor()
        cur.execute(
            'INSERT INTO news_messages (time_stamp, message_id, message_text) VALUES (%s,%s,%s)', entities)
        self.con.commit()

    def read_news(self, message_id):
        cur = self.con.cursor()
        cur.execute(
            'SELECT message_text FROM news_messages WHERE message_id=(%s)', (message_id,))
        return cur.fetchall()
