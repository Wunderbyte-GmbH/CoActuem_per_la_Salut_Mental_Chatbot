import pymongo

# comment out the correct lines to change the status of e.g. only one participant (comment out lines 8, 11; un-uncomment lines 9, 10) and so forth.

myclient = pymongo.MongoClient("mongodb://localhost:27017")
db = ["experiment_db"]
clients_db = db["clients"]
myquery = {} # all
#my_id = "put a hashed Telegram id here'    # one or all but one
#myquery = {"_id":my_id}                    # one 
#myquery = {"_id":{"$ne":my_id}}            # all but one 
update_dict = {"$set":{"status":1}} # status can be set 0, 1, 2, 3. See ./src/status.py
clients_db.update_many(myquery, update_dict)
for x in clients_db.find():
    print(x["_id"], x['status'])

