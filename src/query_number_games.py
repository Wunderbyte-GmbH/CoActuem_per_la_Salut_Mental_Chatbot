"""
This little program tells you how many users played how many games already
"""

# external libraries
from pymongo import MongoClient
import numpy as np

# load clients collection and games Info collection from database
from __main__ import clients, gamesInfo


n_rep = [] # initialize list of how many (non-repeated/able, 1-weighted) games the players played already

for client in clients.find({}):
    # get ids of all the games the player already played
    infos = [gamesInfo.find_one({'_id': game['gameId']}) for game in client['game_history']]
    # get sublist of non-repeatable games that have "weight" one 
    dilemes = [game['gameId'] for i,game in enumerate(client['game_history']) if len(infos[i]['initial_messages']) == 1 and not infos[i].get('repeatable', False)]
    # append number of unique games of player to list
    n_rep += [len(set(dilemes))]

print("mean number of played games per user: ", np.mean(n_rep))
print(sorted(n_rep)[clients.count() // 2]) # no idea what this does..
print("numbers of games played per player: ", n_rep)
