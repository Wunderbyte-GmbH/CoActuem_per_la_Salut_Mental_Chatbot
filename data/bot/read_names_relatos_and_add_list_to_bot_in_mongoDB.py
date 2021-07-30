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
import random 

################### set mongo database ######################
dbclient = pymongo.MongoClient(serverSelectionTimeoutMS=1000)
database = dbclient.experiment_db
bot      = database.bot

########## get list of relatos, shuffle order ###############
filename = "sequence.txt"
with open(filename) as f:
    content = f.readlines()
 
# remove line breaks "\n" 
list_all_relatos = [line.rstrip('\n') for line in content]

######### write shuffled list into array in bot DB ##########
bot.update({"_id": 'objects_to_be_sent'}, {"$set": {"list_relatosCT_plus": list_all_relatos}}, upsert=True)
