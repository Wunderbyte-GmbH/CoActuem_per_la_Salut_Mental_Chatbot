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
