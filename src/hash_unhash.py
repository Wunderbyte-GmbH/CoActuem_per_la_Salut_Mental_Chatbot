"""
hashes and unhashes Telegram user ids

The unhashed ID is needed to send and receive to/from the participant, respectively.
These IDs can neatly be removed from the database after finishing the experiment by deleting the "hashes" collection from the database.
Thanks to the Open Knowledge Foundation for this valuable advice!
"""
import asyncio
import pymongo

# load hashes collection from database
from __main__ import hashes


def save_unhashed_and_hashed_id_mongodb(hashed_user_id, unhashed_user_id):
    """
    only if id was not yet hashed, this function saves hashed id and unhashed id 
    together in the hashes database in mongodb
    """
    if len(str(hashed_user_id))==32 and len(str(unhashed_user_id)) != 32 and type(unhashed_user_id)==int:
        user_hash = {"_id": hashed_user_id, "Tele_id": unhashed_user_id}
        hashes.update_one(user_hash,{'$set':user_hash},upsert=True)


def hash_id(Telgram_user_id):
    print("Dear user of this code. Please use your own way of hashing the Telegram ID in src/hash_unhash.py. For privacy reasons, we don't want to tell you which hashing algorithm we chose.")
    # hash user_id
    if type(Telgram_user_id) == int:
        un_hashed_id = str(Telgram_user_id)
    elif type(Telgram_user_id) == str:
        un_hashed_id = Telgram_user_id
    elif type(Telgram_user_id) == dict:
        un_hashed_id = str(Telgram_user_id["id"])
    if len(un_hashed_id) == 32:
        return Telgram_user_id
    else:
        hashed_user_id = str(Telgram_user_id) # TODO Please use your own way of hashing the Telegram ID, other than just converting the Telegram ID to a string!
        save_unhashed_and_hashed_id_mongodb(hashed_user_id, Telgram_user_id)
        return hashed_user_id
    
def un_hash_id(hashed_user_id):
    # unhash user_id
    unhashed_user_id = hashes.find_one({'_id': hashed_user_id})["Tele_id"]
    return unhashed_user_id
    
    
