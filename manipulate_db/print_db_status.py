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

# prints some current values of interest form the database

myclient = pymongo.MongoClient("mongodb://localhost:27017")
db = myclient["experiment_db"]
clients_db = db["clients"]

print("status users")
for x in clients_db.find():
    print(x["_id"], x['status'])
    
print("\n\ncurrent games users")
for x in clients_db.find():
    print(x["_id"], None if x['current_game']==None else x["current_game"].get("gameId", None))

print("\n\ncurrent message in current game users")
for x in clients_db.find():
    print(x["_id"], None if x['current_game']==None else x["current_game"].get("gameId", None))
   
print("\n\ngames done users")
for x in clients_db.find():
    print(x["_id"], x['games_done'])

print("\n\nrhythm users")
for x in clients_db.find():
    print(x["_id"], x.get("rhythm", "Nope"))

