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

# external libraries
import pymongo
from argparse import ArgumentParser
from security.decrypt_files import decrypt
import json

"""
This file allows to enter developer mode and is called in the moment the instance of Telegram_bot 
The run mode and the developer mode can have two different TOKENs
"""
# bot instances (keys in encrypted file tokens.json, with chatbot TOKEN as value)
bot_instance_in_dev_mode = "my_bot_dev"
bot_instance_in_run_mode = "my_bot"

def load_key(which):
    """
    Loads the decryption key from the current directory named `key.key`
    which : string alias for key, eg "db" or "token"
    """
    key = open("security/keys/" + which + ".key", "rb").read()
    print("key = ", key)
    return key

############# BOT SETTINGS ####################################################

#### run mode or dev mode?
# set either developer or run mode via input arguments
parser = ArgumentParser()
parser.add_argument("-d", "--dev", action="store_true", default=False, help="Start in dev mode")
options, extra = parser.parse_known_args() 

if options.dev:
    print("bot will be started in dev mode")
else:
    print("bot will be started in run mode")

#### token
# get all tokens from encrypted json 
tokens_key = open("./security/keys/tokens.key", "rb").read()    
tokens = decrypt('tokens.json', tokens_key)
tokens = json.loads(tokens)

# dev mode / run mode settings
if options.dev: # if developer mode
    TOKEN = tokens[bot_instance_in_dev_mode]
else: # different TOKEN in developer mode
    TOKEN = tokens[bot_instance_in_run_mode]
    
############# LOAD MONGO DATABASE WITH GAMES AND CLIENTS ######################    
dbclient = pymongo.MongoClient(serverSelectionTimeoutMS=1000)
if options.dev:
    database = dbclient.experiment_db_dev
else:
    database = dbclient.experiment_db

# write database name into output, for logging    
print(database["database"])
dbclient.server_info()




