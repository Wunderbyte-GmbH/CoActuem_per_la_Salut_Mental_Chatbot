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
