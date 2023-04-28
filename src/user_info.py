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
import pymongo
import sys
import copy
import asyncio
from functools import partial
import datetime
import pytz

# internal libraries
from src.status import Status
from src.game import Game, when_is_next_CT_according_to_user_rhythm
from src.event import Event
import src.hash_unhash as hash_unhash

# load clients collection from database
from __main__ import clients
# load bot collection from database
from __main__ import bot
# load gamesInfo collection from database
from __main__ import gamesInfo

night_starts_at = datetime.datetime(2021, 1, 1, 21, 00, 00) # day does not matter we only use time
night_ends_at   = datetime.datetime(2021, 1, 2, 7, 00, 00) # day does not matter we only use time, here one day later than the other (next morning)
duration_of_night_in_seconds = (night_ends_at-night_starts_at).seconds

class UserInfo(object):
    """
    A class to store and work on the info that is stored with each user: 
    some info abou them, like id, sociodemografics, timezone, language
    and the info about games they are currently playing or have already played and messages they sent
        
    Attributes
    ----------
     data :: dictionary with keys same as clients in mongo db: 
     ['_id',               :: currently user id en telegram del participante
     'status',             :: participant status START, INBOT, DOWN, OUT represented by integers, see status.py
     'message_id',         :: id of current msg 
     'game_history',       :: array of game objects to keep track of when a game was played with which results 
     'game_dnd',           :: do not disturb - pair of game_id and timestamp after which bot.py adds the game_id to a list games_not_done
     'games_done',         :: List of played games' id's
     'message_history',    :: array of incoming text messages
     'points',             :: players points
     'dnd',                :: do not disturb - time stamp until which bot.py doesn't send any messages
     'language',           :: language, as chosen in welcome dialog
     'admin_pass']         :: password of a Telegram user that is thereby allowed to control certain things directly from Telegram. see user.py /admin     
      
    Methods
    -------
    get_user_id       ::  returns telegram user id as string
    post_init         ::  deals with current game (after restart?): sets it none or brings game to an end
    locale            ::  takes dict of text in different languages, gives back text in user language
    delete_games_done ::  in developer mode: type /delete_games_done inside Telegram to delete games done
    save, sync_save   ::  exact same function, once in async mode, once not. 
                            
    """
    storage = {}

    def __init__(self, user_id, data=None): 
        # Load from DB
        self.data = data if data else clients.find_one({'_id': user_id}) # loads client database into dictionary
        self.data = {'_id': user_id} if not self.data else self.data
        self.data['unhashed_id'] = hash_unhash.un_hash_id(user_id)

        # Setup basic state: only fill empty fields, don't overwrite
        self.data['status'] = Status(self.data.get('status', int(Status.START)))
        
        # 
        if self.data.get('message_id', None):
            self.data['message_id'] = tuple(self.data['message_id'])
        else:
            self.data['message_id'] = None

        # ordered list of played games of this user with results and timestamps
        if 'game_history' not in self.data:
            self.data['game_history'] = []

        # dict with game id as key and time stamp as value.
        if 'game_dnd' not in self.data:
            self.data['game_dnd'] = {}

        # unordered set of games that the user has already done
        if 'games_done' not in self.data:
            self.data['games_done'] = set()
        else:
            self.data['games_done'] = set(self.data['games_done'])     

        # list of text strings that the user sent to the bot as messages
        if 'message_history' not in self.data:
            self.data['message_history'] = []

        # Points
        self.data['points'] = self.data.get('points', 0)

        # Do not disturb.
        self.data['dnd'] = self.data.get('dnd', 0)
        
        # Default language
        if 'language' not in self.data:
            self.data['language'] = 'ca'

        # Default timeshift_in_seconds
        if 'timeshift_in_seconds' not in self.data:
            self.data['timeshift_in_seconds'] = 0

    def get_user_id(self):
        """
        returns hashed telegram user id as string
        """
        return self.data['_id']

    def get_un_hashed_user_id(self):
        """
        returns (unhashed) telegram user id as string
        """
        return self.data['unhashed_id']
    
    def get_next_game(self):
        """
        compare list "games_done" of a user with ordered list of games to be played
        return id of next game and game type indicator of next game
        """
        # list of all stories the user has already seen/answered
        list_all_games_done   = list(self.data['games_done']) 
        # if current_game is not none, add game id of current game to list of played games
        current_game = self.data.get('current_game', {}) 
        if current_game != None:
            list_all_games_done += [current_game.info.get_game_id()]
        # full ordered list of stories of this type to be answered 
        ordered_list_of_games = bot.find_one({"_id": 'objects_to_be_sent'})["list_relatosCT_plus"]
        # list of stories of type CompViven and TrobSolJunts the user has already answered
        list_games_done_CT  = [x for x in list_all_games_done if x in ordered_list_of_games]
        N=len(list(set(list_games_done_CT)))
        # get next game that should be played
        if set(ordered_list_of_games[0:N]) == set(list_games_done_CT): # if games C+T played are exactly the first games in the ordered list
            if N< len(ordered_list_of_games):
                next_game_id = ordered_list_of_games[N]                 # get next item from ordered list
                print("List of relatos was equal to list of gamesdone for user: ", self.get_user_id(),", next game: ", next_game_id)
            else:
                next_game_id = None
                print("user ", self.get_user_id()," finished all stories")
        else:
            next_game_id = [item for item in ordered_list_of_games[0:N] if item not in list_games_done_CT][0] # get first game from ordered list that wasn't already sent
            print("List of relatos was not equal to list of gamesdone", self.get_user_id(), list_games_done_CT, next_game_id)
        # now: get game type = game_title           
        next_game_data = gamesInfo.find_one({'_id': next_game_id})
        try:
            game_title = next_game_data.get("title", "Demo")
        except:
            game_title = None
            print("see which next game can't be found.. : ", str(next_game_id))
        return next_game_id, game_title

    def is_in_users_night(self, next_time_CT):
        """
        """
        timeshift_in_seconds     = self.data.get('timeshift_in_seconds', 0)
        now_here                 = datetime.datetime.now().astimezone(pytz.timezone("Europe/Madrid"))
        planned_event_here       = now_here + datetime.timedelta(seconds = next_time_CT)
        planned_event_user_time  = planned_event_here + datetime.timedelta(seconds = timeshift_in_seconds)
        is_in_users_night        = False
        if planned_event_user_time.time() > night_starts_at.time() or planned_event_user_time.time() < night_ends_at.time():
            is_in_users_night    = True
        else:
            is_in_users_night    = False
        return is_in_users_night
    
    def set_next_relats_event_from_list(self, appbot, next_time_CT):
        """
        stories of type "compartir vivencias" and "trobar solucions junts"
        will be send in the order given in a list inside the bot collection in mongoDB
        
        next_time_CT :: is the time in seconds until the user receives the next story of type C+T
        (C, T)= (Compartir vivencias, Trobar solucions junts)
        """
        if self.data['status']==Status.INBOT or (self.data.get("legal",[]) and self.data.get("legal", []) =="Si"):
            user_id = self.get_user_id()
            # get game id of next not already played game
            game_id, game_title = self.get_next_game()
            if game_title and game_id:
                if not game_title in ["compartir_vivencias", "encontrar_soluciones_juntos"]:
                    next_time_CT/= 4 # send next game more quickly if its not a "story"
                print("game_title", game_title)
                if game_id in ["welcome", "capacitation_Teatre_Amigues", "sociodem_coact"]:
                    next_time_CT= 0 # directly send the next game
                elif self.is_in_users_night(next_time_CT):
                    print("it's night for user ", self.get_user_id())
                    next_time_CT += duration_of_night_in_seconds

                appbot.add_event(Event.after(next_time_CT, partial(Game.start_game, Game, appbot, game_id, user_id), daytime_only=True, is_new_game=True)) # comment this line out to supress automatic sending according to sequence
        
    def post_init(self, appbot):
        """ 
        after having (re)loaded a users data 
        update info on current game  
        """
        current_game = self.data.get('current_game', {}) # get data on current game from UserInfo instance dict
        current_game = {} if current_game is None else current_game # if field current game is null, set empty dict
        print("post_init({}) {} - {}".format(self.data['_id'], self.data.get('status', Status.DOWN), current_game.get('_id', None))) # logging entry
        if self.data['status'] == Status.DOWN:
            return
            #self.data['current_game'] = None
        #elif self.data['status'] != Status.START: 
        #   self.data['current_game'] = None
        #   appbot.add_waiting(self)
        else:
            # see if there is a rest of a current game left over after restart of bot
            if not 'current_game' in self.data or self.data['current_game'] is None:
                self.data['current_game'] = None
                appbot.add_waiting(self)
            else:
                self.data['current_game'] = Game.from_game_dict(self.data['current_game'], appbot)
            # send rest of current game or calculate next game
            if self.data['current_game']:
                asyncio.ensure_future(self.data['current_game'].resume(appbot, self)) # bring current game to an end, game.py func resume      
            else:    
                # set next C+T relats event
                # get timing of next C+T relat according to rhythm of user
                time_till_next_CT_in_seconds = when_is_next_CT_according_to_user_rhythm(self)/2
                if self.is_in_users_night(time_till_next_CT_in_seconds):
                    print("would be at night for user ", self.get_user_id())
                    time_till_next_CT_in_seconds += duration_of_night_in_seconds
                self.set_next_relats_event_from_list(appbot, time_till_next_CT_in_seconds) # add some random offset for rhythm
            
        
        #if self.data['status'] == Status.DOWN:
        #    self.data['current_game'] = None
        #else:# self.data['status'] != Status.DOWN: 
        #    if not 'current_game' in self.data or self.data['current_game'] is None:
        #        self.data['current_game'] = None
        #    else:
        #        self.data['current_game'] = Game.from_game_dict(self.data['current_game'], appbot)
        #if self.data['status'] == Status.INBOT:
        #    if self.data['current_game'] != None: 
        #        asyncio.ensure_future(self.data['current_game'].resume(appbot, self)) # bring current game to an end, game.py func resume
        

    def locale(self, text): 
        """
        Grasps "language" from user info and returns text in according language
        If Language isn't listed: default "ca"
        If isn't a dict: return text as is.
        """
        if type(text) == dict:
            return text[self.data.get('language', 'ca')]
        return text
        
               
    async def delete_games_done(self):                                                                                                            
        """                                                                                                                                       
        after user wrote "/delete_games_done" the code                                                                                            
        comes here and deletes all games but welcome from the database                                                                            
        --> "/delete_games_done" works only in developer mode, 
        so that the developer can run the same game multiple times
        
        """
        data = copy.copy(self.data)
        data['status'] = int(data['status'])
        data['games_done'] = ["welcome"] 
        data['current_game'] = None
        data.pop('unhashed_id', None) # never write unhashed id to database
        clients.update({'_id': self.data['_id']}, data, True)
        
            
    async def save(self):    
        """
        save user info data to mongoDB clients
        """
        data = copy.copy(self.data)
        data['status'] = int(data['status'])          # put status in int form
        data['games_done'] = list(data['games_done']) # put games_done in list form instead of set
        data['current_game'] = None if data['current_game'] is None else data['current_game'].to_game_dict() 
        data.pop('unhashed_id', None) # never write unhashed id to database
        clients.update({'_id': self.data['_id']}, data, True)

    def sync_save(self):
        """
        put user info to mongoDB digestible format and save to mongoDB clients database
        """
        data = copy.copy(self.data)      
        data['status'] = int(data['status'])          # put status in int form
        data['games_done'] = list(data['games_done']) # put games_done in list form instead of set
        data['current_game'] = None if data['current_game'] is None else data['current_game'].to_game_dict()
        clients.update({'_id': self.data['_id']}, data, True)
