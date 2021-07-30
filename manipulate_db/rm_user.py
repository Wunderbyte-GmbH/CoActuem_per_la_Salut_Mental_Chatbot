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

# cleanly remove all data of a participant from the database, e.g. when he/she decides to quit the experiment 

myclient = pymongo.MongoClient("mongodb://localhost:27017")
db = myclient["experiment_db"]

# participant id of user that is to be deleted
delete_id = 'put a hashed Telegram id here' 

# delete user from clients db
clients_db = db["clients"]
result = clients_db.delete_one({'_id': delete_id})
#print "customers" after the update:
for x in clients_db.find():
  print(x["_id"])

# delete user from hashes db
hashes_db  = db["hashes"]
result = hashes_db.delete_one({'_id': delete_id})
#print "customers" after the update:
for x in hashes_db.find():
  print(x["_id"])
