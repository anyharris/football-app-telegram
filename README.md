# football-app-telegram

### Info

This app is a telegram bot that provides information about premier league football.  

It sends notifications for every fixture after the team news has been released. The notification shows the betting lines shortly before and after the news, and has a button to click to show the news.  

The bot also takes a few commands:  
`/start` start the bot  
`/fixtures` show today's fixtures detail in London and Bangkok time  
`/league` shows the current league standings  
`/player {searchterm}` searches for player stats by last name  

### Setup

To set up your `.env` file see `example.env`. You will need (free) API keys from `https://www.api-football.com/` and `https://the-odds-api.com/`. You can set up your Telegram bot by messaging BotFather on Telegram.  

Once your `.env` file is set up, first run `update_team_players.py` to collect team and player info. You can see example files in the `data` folder. Then run celery using the command `celery -A tasks worker -B -l info`, and run `football_tg_bot.py`.
