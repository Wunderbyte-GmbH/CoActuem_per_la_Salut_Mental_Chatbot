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
