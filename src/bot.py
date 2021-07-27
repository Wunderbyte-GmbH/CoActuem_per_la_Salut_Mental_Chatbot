# external libraries
import math
import time
import asyncio
import random
import pymongo
import numpy as np
import sys
from functools import partial
from itertools import count
from heapq import heappush, heappop 

# internal libraries
from src.user import User
from src.event import Event
from src.user_info import UserInfo
from src.game import Game, GameInfo
from src.helpers import list_of_ids
from src.conversation_elements import time_is_over
import src.hash_unhash as hash_unhash

# load bot collection from database
from __main__ import bot


class Bot(object):
    """
    A class to handle who gets which game of several players when.
    Takes access on Mongodb collection "bot".
    
    Attributes
    ----------
    _users_info       :: copy of UserInfo 
    _waiting_list     :: list of players, with full user info, for two players games: player in list is waiting for another player
    _busy_list        :: list of players, with full user info, player in list is currently busy
    _events           :: list of triples of (timestamp, counter, _game_event) :     
    _game_select_pct  :: part of the point system that rewards frequent usage
    _game_event       :: Event instance with _recurring = True attribute 
    _pending_answer   :: list of copies of current_game
    _pending_players  :: dict with game_ids as keys and lists of pending players as value
    
    Methods
    -------
    save                          ::  updates the "bot" collection in mongodb
    preload_data                  ::  loads info from clients and from games into appbot
    reload_users                  ::  reloads user data from mongodb
    reload_games                  ::  reloads game data from mongodb
    clear_user                    ::  remove user from list of pending answers
    remove_user                   ::  remove user from pending, busy and waiting list
    set_game_event                ::
    check_waiting_queue           ::
    post_invitation_start_game    ::
    get_user_info                 ::
    add_busy                      ::
    add_waiting                   ::
    get_one_waiting               ::
    add_event                     ::
    poll_events                   ::
    loop_events                   ::
    
    Methods parameters
    ------------------
    force :: bool, apparently to "force" the relaoding of user information 
    
    
    
    """
    
    def __init__(self):
        # Save bot
        User.appbot = self 

        # Setup basic attributes
        self._users_info   = {} 
        # read in waiting list and busy list from mongoDB
        self._waiting_list = []
        self._busy_list    = []
        
        self.event_counter = count() # counts from 0 up, each time next(event_counter) is applied
        self._events       = []

        # Create recurring daytime event
        self._game_select_pct = 18 
        self._game_event = Event.recurring(60, self.check_waiting_queue, True)
        self.add_event(self._game_event) # comment out to suppress new games

        # Preload users and games
        self.preload_data() # is actually already done in main

        # Fetch queues
        self._pending_answer = []
        self._pending_players = {}

        # Update attributes from mongodatabase, "bot" here is mongodb collection
        bot_info = bot.find_one({'_id': 'bot'})
        
        # Update Queues from database, add to busy
        for player in bot_info.get('pending_answer', []):
            user_info = self.get_user_info(player)
            self._pending_answer.append(user_info.data['current_game'])
            self.add_busy(user_info)
        for game_id in bot_info.get('pending_players', {}):
            self._pending_players[game_id] = []            
            for player in bot_info['pending_players'][game_id]:
                user_info = self.get_user_info(player)
                self._pending_players[game_id].append(user_info)
                self.add_busy(user_info)
        
    def save(self):
        """
        updates the "bot" collection in mongodb
        """
        bot.update({"_id": 'bot'}, {"$set": {'pending_answer':   [game._players[0].get_user_id() for game in self._pending_answer]}}, upsert=True)
        bot.update({"_id": 'bot'}, {"$set": {'pending_players':  {game_id: [player.get_user_id() for player in pending] for game_id, pending in self._pending_players.items()}}}, upsert=True)

    def preload_data(self):
        """
        loads info from clients and from games into appbot
        """
        User.preload_all_users(self) # from user_info.py
        Game.preload_all_games()     # from game.py
        
    def restart_bot(self):
        """
        after reinitializing the bot, the current game should be resumed and the next event should be set
        """
        for user_info in self._waiting_list + self._busy_list:
            user_info.post_init(self)
        


    async def reload_users(self, force=False):
        """                                                                                                                                    
        reloads user data from mongodb                                                                                                         
        overwrites runtime storage user_info.data in user_info.py  with data from mongodb,                                                     
        including current current_game                                                                                                         
        """
        if force:
            # join waiting list and busy list and run through them
            for user_info in self._waiting_list + self._busy_list: 
                # initialize user again with data from mongodb
                user_info.__init__(user_info.get_user_id())
                # update field "current_game"
                user_info.post_init(self)
                # update client database
                await user_info.save()
        self.preload_data()

    async def reload_games(self):
        """
        reloads game data from mongodb
        therefore first overwrites runtime storage "GameInfo" in game.py with data from mongodb 
        """
        GameInfo.storage = {}
        preload_all_games()

    def clear_user(self, user):
        """
        remove user from list of pending answers
        """
        print('clear_user {}'.format(user.get_user_id()))
        try:
            i = 0
            while i < len(self._pending_answer):
                if self._pending_answer[i] is None:
                    self._pending_answer.pop(i)
                elif user in self._pending_answer[i]._players:
                    self._pending_answer.pop(i)
                else:
                    i += 1

        except Exception as e:
            print("Could not remove {} from pending_answer".format(user.get_user_id()))
            print(e)

        for game_id, players in self._pending_players.items():
            try:
                players.remove(user)
            except:
                print("Could not remove {} from pending_players".format(user))

    def remove_user(self, user):
        """
        remove user from pending, busy and waiting list
        """        
        print('remove_user {}'.format(user.get_user_id()))
        self.clear_user(user)

        try: 
            self._busy_list.remove(user)
        except:
            pass

        try:
            self._waiting_list.remove(user)
        except:
            pass

    def set_game_event(self, interval=None, pct=None, daytime=None):
        """
        
        """        
        if interval:
            # Set interval
            self._game_event.set_every(interval)

            # Remove current                                                                                                                         
            for i in range(len(self._events)):                                                                                                       
                ts, counter, evt = self._events[i]                                                                                                   
                if evt == self._game_event:                                                                                                          
                    self._events.pop(i)                                                                                                              
                    break                                                                                                                            
                                                                                                                                                     
            # Add new                                                                                                                                
            self.add_event(self._game_event) # comment out to suppress new games

        if pct:
            self._game_select_pct = pct

        if daytime:
            self._game_event._daytime_only = daytime

    async def check_waiting_queue(self, selected=None, force_game_id=None, max_selected=None, filter_query=None):
        """
        
        """
        # Check pending actions
        #print('START check_waiting_queue PENDING TIME-OUTS')
        return

        should_save = False
        reschedule_games = {}
        i = 0
        while i < len(self._pending_answer):
            game = self._pending_answer[i]
            game_id = game.custom_data.get('next_game', 'Col·laboració_2')
            player = game._players[0]

            if time.time() - game._start_time >= 20:
                self.send_message_after(player.get_user_id(), 1, player.locale(time_is_over), wait=0)
                await game.cancel(player)

                # Back to waiting, search another partner
                player.data['current_game'] = None
                player.sync_save()

                self.add_waiting(player)
                reschedule_games[game_id] = reschedule_games.get(game_id, 0) + 1

                self._pending_answer.pop(i)
                should_save = True
            else:
                i += 1

        for game_id, nplayers in reschedule_games.items():
            self.add_event(Event.after(5, partial(self.check_waiting_queue,
                                                  force_game_id=game_id,
                                                  max_selected=nplayers,
                                                  filter_query=lambda p: p.data['dnd'] < time.time())))

        # Check busy players for time-outs
        #print('START check_waiting_queue 2P TIME-OUTS')

        cancel_games = set()
        for player in self._busy_list:
            game = player.data['current_game']
            if game is not None and game.info.num_players() == 2:
                if time.time() - game._start_time >= 24*60*60:
                    cancel_games.add(game)

        for game in cancel_games:
            print("About to cancel {}".format(game.info.get_game_id()))
            for player in game._players:
                self.send_message_after(player.get_user_id(), 1, player.locale(time_is_over), wait=0)
                self.add_waiting(player)
                player.data['current_game'] = None

            for player in game._players:
                await game.cancel(player)
                await player.save()

        #print('START check_waiting_queue SELECTION')
        #print('Params [force_game_id={}, #selected={}, max_selected={}, has_filter={}'.format(force_game_id, 0 if selected is None else len(selected), max_selected, filter_query is not None))


        max_selected = max_selected if max_selected else int(math.floor(len(self._waiting_list) * self._game_select_pct / 100))
        waiting_list = self._waiting_list if filter_query is None else list(filter(filter_query, self._waiting_list))
        # Nothing, reschedule again with same parameters
        if not waiting_list:
            print("[/] Empty waiting list, exiting")

            if should_save:
                self.save()

            return

        selected = selected if selected else random.sample(waiting_list, max_selected)
        total = len(selected)
        print('Starting games with {} {} selected players'.format(total, list_of_ids(selected)))

        i = 0
        while i < total:
            # Check just in case it has been occupied somehow
            player = selected[i]
            if player in waiting_list:
                skip_partner = force_game_id is not None
                game_id = force_game_id

                if force_game_id is None:
                    games_not_done = ((GameInfo.ids - player.data['games_done']) | GameInfo.ids_2p | GameInfo.ids_repeat) - GameInfo.ids_skip
                    if player.data['dnd'] >= time.time():
                        games_not_done -= GameInfo.ids_2p

                    # Remove DND games
                    for game_id, timestamp in player.data['game_dnd'].items():
                        if timestamp > time.time():
                            games_not_done -= set([game_id])

                    # If it is empty, no game available (it is dnd then)
                    if not games_not_done:
                        print("No games available for {}".format(player.get_user_id()))
                        i += 1
                        continue

                    game_id = random.choice(list(games_not_done))

                game_info = GameInfo.get_info(game_id)
                print("{} > Starting {}".format(player.get_user_id(), game_id))

                i += 1

                wide_partner_check = False
                if game_info.num_players() == 2 and player.data['dnd'] >= time.time():
                    # SHOULD NEVER REACH HERE! FILTER_QUERY PREVENTS IT
                    print("WTF?")
                    wide_partner_check = True
                elif game_info.num_players() == 2 and not skip_partner:
                    try:
                        available_parterns = [i for i, partner in zip(range(i, total), selected[i:]) if partner.data['dnd'] < time.time()]
                        partner_i = random.choice(available_parterns)
                        partner = selected.pop(partner_i)
                        print("Partner selected {}".format(partner.get_user_id()))
                        total -= 1
                        self.add_event(Event.after(5, partial(self.check_waiting_queue, selected=[partner], force_game_id=game_id)))
                    except:
                        # No suitable partner, skip this player
                        print("No partner available for {} in game {}: ABORTING".format(player.get_user_id(), game_id))
                        continue
                        wide_partner_check = True

                if wide_partner_check:
                    print("Doing wide partner check")
                    self.add_event(Event.after(5, partial(self.check_waiting_queue, force_game_id=game_id, max_selected=1, filter_query=lambda p: p.data['dnd'] < time.time())))

                # Do not check for % 2
                # if game_info.num_players() == 2 and len(players) < 2:
                #     print("Found {} players game, with {} found players".format(game_info.num_players(), len(players)))
                #     continue

                if game_info.num_players() == 2:
                    if "intro_games_2_players" not in player.data['games_done']:
                        game = Game("intro_games_2_players", [player], skip_waiting=True)
                    else:
                        game = Game("intro_games_2_players_short", [player], skip_waiting=True)

                    game.custom_data['next_game'] = game_id
                    self._pending_answer.append(game)
                    should_save = True
                else:
                    game = Game(game_id, [player])

                self.add_busy(player)
                player.data['current_game'] = game
                player.data['game_dnd'][game_id] = time.time() + 60*60*24*5
                await player.save()
                self.typing_event(player.get_user_id(), 5, partial(game.perform_next_action, self, player))

                if should_save:
                    self.save()
            else:
                i += 1
        
        pass

    async def post_invitation_start_game(self, game_id, player, intro_game):
        """
        
        """
        print('post_invitation_start_game {}'.format(player.get_user_id()))
                                                                                                                                                  
        try:                                                                                                                                      
            self._pending_answer.remove(intro_game)                                                                                               
        except:                                                                                                                                   
            print('[E] had no pending answer {}'.format(player.get_user_id()))                                                                    
            pass                                                                                                                                  
                                                                                                                                                  
        ready = intro_game._answers.get('ready', 'no')                                                                                            
        print('+ answered {}'.format(ready))                                                                                                      
        if ready == 'si':
            # FLAG DND and continue
            player.data['dnd'] = time.time() + 4 * 24 * 60 * 60
            player.sync_save()

            try:
                self._pending_players[game_id] += [player]
            except:
                self._pending_players[game_id] = [player]
            
        elif ready == 'no':
            # FLAG DND and continue
            player.data['dnd'] = time.time() + 2 * 24 * 60 * 60
            player.sync_save()

            # Back to waiting, search another partner
            self.add_waiting(player)
            self.add_event(Event.after(5, partial(self.check_waiting_queue,
                                                  force_game_id=game_id,
                                                  max_selected=1,
                                                  filter_query=lambda p: p.data['dnd'] < time.time())))
            self.save()
            return

        num_players = len(self._pending_players[game_id])
        i = 0
        while num_players >= 2 and i < num_players - 1:
            players = [self._pending_players[game_id].pop(0), self._pending_players[game_id].pop(0)]
            game = Game(game_id, players)
            for player in players:
                player.data['current_game'] = game
                self.typing_event(player.get_user_id(), 5, partial(game.perform_next_action, self, player))

            i += 2
            num_players -= 2
        self.save()



    def get_user_info(self, user_id, data=None):
        """
        
        """
        try:
            info = self._users_info[user_id]                                                                                                                      
        except:             
            """                                                                                                                                                                              
            seems that user not yet in db                                                                                                                                                                
            """                                    
            hashed_user_id = hash_unhash.hash_id(user_id)
            info = UserInfo(hashed_user_id, data)                                                                                                                       
            self._users_info[hashed_user_id] = info                                                                                                                      
            info.post_init(self)
                                                                                                                                                                  
        return info                                                                                                                                               
                                                                                                                                                                  
    def add_busy(self, user_info):     
        """
        
        """
        print('add_busy {}'.format(user_info.get_user_id()))                                                                                   
        try:                                                                                                                                                      
            self._busy_list.append(user_info)                                                                                                                     
            self._waiting_list.remove(user_info)  
        except Exception as e:
            print("[E] add_busy {}: {}".format(user_info.get_user_id(), e))
            return False
        return True

    def add_waiting(self, user_info):
        """
        
        """
        print('add_waiting {}'.format(user_info.get_user_id()))

        try:
            if user_info in self._waiting_list:
                self._busy_list.remove(user_info)
                raise ValueError('User already in list')

            self._waiting_list.append(user_info)
            self._busy_list.remove(user_info)
        except Exception as e:
            print("[E] add_waiting {}: {}".format(user_info.get_user_id(), e))
            return False
        return True

    def get_one_waiting(self):
        """
        
        """
        if len(self._waiting_list) > 0:
            user_info = self._waiting_list[-1]
            self.add_busy(user_info)
            return user_info

        return None

    def add_event(self, event):
        """
        adds a triple consisting of
        event.when()             :: returns _timestamp of event
        next(self.event_counter) :: event counter current state
        event                    :: event itself
        to end of _events list
        """
        tpl = (event.when(), next(self.event_counter), event) 
        heappush(self._events, tpl) # adds triple to end of _events list
        

    async def poll_events(self): 
        """
        
        """
        while self._events:                                                                                            
            timestamp, counter, callback = self._events[0]                                                             
                                                                                                                       
            if await callback():                                                                                       
                heappop(self._events) # deletes first item in _events list                                             
                                                                                                                       
                if callback.is_recurring():                                                                            
                    self.add_event(callback.recurse())                                                                 
            else:                                                                                                      
                break                                                                                                  
                                                                                                                       
    async def loop_events(self): 
        """
        
        """
        while True:                                                                                                    
            await self.poll_events()                                                                                   
            await asyncio.sleep(0.1)                                                                                   
