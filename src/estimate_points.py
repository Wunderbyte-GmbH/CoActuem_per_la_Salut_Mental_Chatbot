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

# external libraries
from pymongo import MongoClient
import numpy as np
"""
asigns points to each player according to how many games he/she has solved already
and stores them in mongoDB
"""

# load clients collection from database
from __main__ import clients, gamesInfo
 
for client in clients.find({}):
    # for each client, gather ids of gamesInfo they already played
    infos = [gamesInfo.find_one({'_id': game['gameId']}) for game in client['game_history']]
    dilemes = [game['gameId'] for i,game in enumerate(client['game_history']) if len(infos[i]['initial_messages']) == 1 and not infos[i].get('repeatable', False)]
    dilemes2p = [game['gameId'] for i,game in enumerate(client['game_history']) if len(infos[i]['initial_messages']) == 2]
    n_points = client.get('points', 0) + 3 * len(dilemes2p) + len(dilemes)

    clients.update({'_id': client['_id']}, {'$set': {'points': n_points}})
    print('{}\t{}\t{}'.format(client['_id'], client.get('points', 0), n_points))
