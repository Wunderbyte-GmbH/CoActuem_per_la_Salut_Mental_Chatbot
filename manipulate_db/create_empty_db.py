"""
    CoActuem per la Salut Mental Chatobot
    Copyright (C) Franziska Peter

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

import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017")
new_db_name = "experiment_db" # and "experiment_db_dev" 

# check if db already exists. If so, doesn't overwrite.
dblist = myclient.list_database_names()
if new_db_name not in dblist:
    db = myclient[new_db_name]
    bot_db     = db["bot"]
    bot_dict   = [{"_id":"bot", "pending_answer":[], "pending_players":{}},
                {"_id":"objects_to_be_sent", "list_relatosCT_plus":[]}]
    x = bot_db.insert_many(bot_dict)
    print(x.inserted_ids)
    games_db   = db["gamesInfo"]
    clients_db = db["clients"]
    hashes_db  = db["hashes"]
