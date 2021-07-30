"""
    CoActuem per la Salut Mental Chatobot
    Copyright (C) Franziska Peter, Santi Seguí, Guillem Pascual Guinovart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import asyncio

############# LOAD MONGO DATABASE WITH GAMES AND CLIENTS ######################
from src.settings import TOKEN, database

# load collections from database
bot         = database.bot       # serves as "where was I just now" memory of the bot
clients     = database.clients   # Who uses the bot, what dialogues has s/he received/ answered how?
gamesInfo   = database.gamesInfo # message bundles to be sent from the bot = dialogues
hashes      = database.hashes    # links between Telegram ID and hash

############## LOAD INTERNAL MODULES ##########################################
from src.telegram_bot import TelegramBot
from src.bot import Bot
from src.user import User
from src.telegram_user import TelegramUser
from src.event import Event
from src.status import Status
from src.user_info import UserInfo
from src.game import Game, GameInfo
from src.helpers import list_of_ids

#################### RUN BOT ##################################################
def run():
    # load users and games from mongoDB 
    User.preload_all_users
    Game.preload_all_games()
    Bot.restart_bot
    # create instance of TelegramBot 
    bot = TelegramBot(TOKEN)
    # telegram_bot.py method get_me: tests bot's auth token and grasps bot info
    asyncio.ensure_future(bot.get_me())
    # bot.py method loop_events: awaits poll events
    asyncio.ensure_future(bot.loop_events())
    # telegram_bot method wait: makes loop run forever
    bot.wait()
    

if __name__ == "__main__":    
    run()
    
