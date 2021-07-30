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

# comment out the correct lines to delete the record of answered dialogues/played games of e.g. only one participant (comment out lines 8, 11; un-uncomment lines 9, 10) and so forth.

myclient = pymongo.MongoClient("mongodb://localhost:27017")
db = myclient["experiment_db"]
clients_db = db["clients"]
myquery = {} # all
#my_id = 'put a hashed Telegram id here' # one or all but one 
#myquery = {"_id":my_id}                    # one 
#myquery = {"_id":{"$ne":my_id}}            # all but one 
newvalues = { "$set": { "games_done": [] } }
x = clients_db.update_many(myquery, newvalues)
#print "customers" after the update:
for x in clients_db.find():
    print(x["_id"], x['games_done'])
