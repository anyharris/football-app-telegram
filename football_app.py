# football_app.py

from tasks import fixtures, odds, news

'''
app workflow:
    - every day run tasks.fixtures to get the fixture (match) number and timestamp for 2 days from now
    - for each fixture,
        - run tasks.odds 1 day before (timestamp - 60*60*24)
        - run tasks.news 1 hour before (timestamp - 60*60*1)
        - run tasks.odds 5 minutes after tasks.news
            - I'll need a new API with live betting info for this
        - take both odds results and the team news, format it, and send it via Telegram message 
'''

