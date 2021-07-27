import pymongo

# comment out the correct lines to delete the current_game of e.g. only one participant (comment out lines 8, 11; un-uncomment lines 9, 10) and so forth.

myclient = pymongo.MongoClient("mongodb://localhost:27017")
db = myclient["experiment_db"]
clients_db = db["clients"]
myquery = {} # all
#my_id = 'put a hashed Telegram id here' # one or all but one 
#myquery = {"_id":my_id}                    # one 
#myquery = {"_id":{"$ne":my_id}}            # all but one 
newvalues = { "$set": { "current_game": None } }
x = clients_db.update_many(myquery, newvalues)
#print "customers" after the update:
for x in clients_db.find():
    print(x["_id"], x['current_game'])




