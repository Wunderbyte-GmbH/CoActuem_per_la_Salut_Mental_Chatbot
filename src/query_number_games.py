"""
    CoActuem per la Salut Mental Chatobot
    Copyright (C) Franziska Peter, Santi Seguí, Guillem Pascual Guinovart

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
