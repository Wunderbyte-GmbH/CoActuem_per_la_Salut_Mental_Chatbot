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

