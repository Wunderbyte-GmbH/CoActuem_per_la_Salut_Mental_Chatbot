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
import sys
import pymongo
import copy
import asyncio
import time
import numpy as np
import telepot
from telepot import message_identifier, glance
from functools import partial

# internal libraries
from src.status import Status
from src.event import Event
from src.game import Game, GameInfo
from src.helpers import list_of_ids, list_of_ids
from src.user_info import UserInfo
from src.settings import options
from src.conversation_elements import you_are_unsubscribed, unsufficient_players, time_is_over, default_answer_msg, wrong_answer, command_other_than_baixa_o_pausa_during_dialogue
import src.hash_unhash as hash_unhash

# load clients collection from database
from __main__ import clients


class User(object):
    """
    A class to handle which messages come from and go to a user.
    Also includes editing send messages and calling game actions
    
    Attributes
    ----------
    _editor       :: loads telepot.aio.helper.Editor class with its methods that
                        allow to edit sent messages
    info          :: copy from User Info
    
    Methods
    -------
    
    #### admin methods: A telegram user can become admin #######################
    #### by typing the correct code and then send admin commands ###############
    sender_is_admin   :: returns bool: is user admin or not?
    
    # methods that execute admin commands
    admin_command_get_bot_status
    admin_command_reload_users
    admin_command_reload_games
    admin_command_remove_user_from_list_of_pending_answers
    admin_command_broadcast
    admin_command_set_interval_points_and_daytime_for_game
    admin_command_set_interval_points_and_daytime_for_game
    admin_command_update_clients_on_mongoDB
    admin_command_trigger_game_only_for_admin_and_partner
    admin_command_send_game_to_all_availabe
    admin_command_send_message_to_specific_user
    
    # command handler
    handle_admin_commands :: calls the corresponding method to each command  
    handle_text_message   ::
    handle_on_message     ::
    start_game            ::
    handle_on_callback    ::
    handle_on_close       ::

    """
    appbot = None

    def __init__(self):
        # Buttons editting, in particular to delete buttons after sending
        self._editor = None
        # Get user info
        self.info = User.appbot.get_user_info(hash_unhash.hash_id(self.id))
        # fill variable _editor with Editor class instance that allows to edit sent messages
        if self.info.data['message_id']:
            self._editor = telepot.aio.helper.Editor(self.bot, self.info.data['message_id'])
    
    def preload_all_users(appbot):
        for client in clients.find({}):
            appbot.get_user_info(client['_id'], client)
            time.sleep(1)
    
    async def sender_is_admin(self):
        """
        check if sender of text message is admin, before handling his message
        """
        is_admin = False
        if 'admin_pass' in self.info.data and self.info.data['admin_pass'] == 'put_here(some*pwd_you!like': 
            is_admin = True
        return is_admin
        
    async def admin_command_get_bot_status(self, tokens):                                    
        """                                                                                  
        reaction on admin command "/status"
        inform admin on number of pending players and games
        """
        # get current state of user_info
        wait     = User.appbot._waiting_list
        busy     = User.appbot._busy_list
        pending  = User.appbot._pending_answer
        awaiting = User.appbot._pending_players
        who      = self.info if len(tokens) == 1 else User.appbot.get_user_info(int(tokens[1]))

        # send status to admin
        await self.send_message('Waiting ({}): [{}]'.format(len(wait), list_of_ids(wait)))
        await self.send_message('Busy ({}): [{}]'.format(len(busy), list_of_ids(busy)))
        await self.send_message('Pending: [{}]'.format(', '.join(map(str, [g._players[0].get_user_id() for g in pending]))))
        for game_id, players in awaiting.items():
            await self.send_message('Awaiting {}: [{}]'.format(game_id, list_of_ids(players)))
        await self.send_message('user.Status: ' + str(who.data['status']))
        await self.send_message('user.Game: ' + str(who.data['current_game']))
    
    async def admin_command_reload_users(self, tokens):                                               
        """                                                                                           
        reaction on admin command "/reload_users"                                                     
        """                                                                                           
        #force = False if len(tokens) == 1 else bool(int(tokens[1]))
        #await User.appbot.reload_users(force)
        #****** W A R N I N G *** Use only with extreme care (if at all) ****
        pass
    
    async def admin_command_reload_games(self):
        """
        reaction on admin command "/reload_games"
        reloads game data from mongodb, after overwriting GameInfo.storage
        ****** W A R N I N G *** Use only with extreme care (if at all) ****
        """          
        await User.appbot.reload_games()                            
    
    async def admin_command_remove_user_from_list_of_pending_answers(self, tokens):
        """
        reaction on admin command "/clear"
        for consecutive users in _busy_list: remove current_game
                                            remove user from list of pending answers
                                            add to waiting list
        call by "/clear" to clear all active or "clear <user_id>" to clear one                                
        """                                                              
        if len(tokens) == 1: # clear all active users
            while User.appbot._busy_list:                                
                player = User.appbot._busy_list[0]   # take first from busy_list
                player.data['current_game'] = None   # clear current game                    
                User.appbot.clear_user(player)       # remove user from list of pending answers
                User.appbot.add_waiting(player)      # add user to waiting list                    
            for player in User.appbot._waiting_list:                     
                player.data['current_game'] = None   # clear current game 
                User.appbot.clear_user(player)       # remove user from list of pending answers                    
                await player.save()                  # user_info function save
                
        else: # clear only specified user
            player = User.appbot.get_user_info(tokens[1])
            User.appbot.clear_user(player)
            User.appbot.add_waiting(player)
            await player.save()
        User.appbot.save() # this is the bot.py function save(self)
                                                                                                                   
    async def admin_command_broadcast(self, tokens, msg_text):                                                             
        """                                                                                                        
        reaction on admin command "/broadcast"                                                                     
        send message that follows after /broadcast to all somehow active users                                     
        """                                                                                                        
        if len(tokens) > 1: # supress empty messages                                                               
            # get message part of command                                                                          
            broadcast_msg = ' '.join(msg_text.split()[1:])                                                         
            # gather whom to address
            list_of_active_users = User.appbot._busy_list + User.appbot._waiting_list
            # forward message from admin to all
            for player in list_of_active_users:
                await User.appbot.send_message(player.get_user_id(), broadcast_msg)
            
    async def admin_command_set_interval_points_and_daytime_for_game(self, tokens):
        """
        reaction on admin command "/set"
        sets general game event attributes for all games at once
        """      
        if len(tokens) == 4:
            if tokens[1] == 'game':
                if tokens[2] == 'interval':
                    User.appbot.set_game_event(interval=int(tokens[3]))
                elif tokens[2] == 'pct':
                    User.appbot.set_game_event(pct=int(tokens[3])) # apparently has no effect on gamesInfoDB
                elif tokens[2] == 'daytime':
                    User.appbot.set_game_event(daytime=bool(int(tokens[3])))
                    
    async def admin_command_update_clients_on_mongoDB(self, tokens):                                                      
        """                                                                                                               
        reaction on admin command "/save"                                                                                 
        """                                                                                                               
        if len(tokens) == 1:                                                                                              
            # gather whom is active                                                                                       
            list_of_active_users = User.appbot._busy_list + User.appbot._waiting_list                                     
            # saves client data for users in busy_list and waiting_list to mongoDB.clients                                
            for player in list_of_active_users:                                                                           
                player.sync_save()                                                                                        
            print("sync-saved busy users")
                
    async def admin_command_trigger_game_only_for_admin_and_partner(self, tokens, tokens_sensitive):
        """
        reaction on admin command "/jugar"
        """ 
        if len(tokens) >= 2:
            if self.info.data['status'] != Status.INBOT:
                await self.send_message(player.locale(you_are_unsubscribed))
                return

            try:
                User.appbot.add_busy(self.info)
                game_id = tokens_sensitive[1]
                game_info = GameInfo.get_info(game_id)
                players = [self.info]

                if game_info.num_players() >= 2:
                    if len(tokens) > 2:
                        other = User.appbot.get_user_info(tokens[2])
                        User.appbot.add_busy(other)
                    else:
                        other = User.appbot.get_one_waiting()

                    if other is None:
                        await self.send_message(player.locale(unsufficient_players) )
                        User.appbot.add_waiting(self.info)
                        print(list_of_ids(User.appbot._busy_list))
                        print(list_of_ids(User.appbot._waiting_list)) 
                        return

                    players += [other]

                print(list_of_ids(players))

                game = Game(game_id, players)
                for player in players:
                    player.data['current_game'] = game
                    await player.data['current_game'].perform_next_action(User.appbot, player)
            except Exception as e:
                print('Read exception: {}'.format(e))
                User.appbot.add_waiting(self.info)
                await self.send_message('No t\'he entés')     
                
                
    async def admin_command_send_game_to_all_availabe(self, tokens, tokens_sensitive):                                                           
        """                                                                                                                                      
        reaction on admin command "/global"                                                                                                      
        """ 
        print("WAITING LIST ", User.appbot._waiting_list, "BUSY :", User.appbot._busy_list)
        if len(tokens) == 2:                                                                                                                     
            game_id = tokens_sensitive[1]                                                                                                        
                                                                                                                                                 
            ## 1. CANCEL ALL GAMES PENDING FOR MORE THAN 24h                                                                                      
            #cancel_games = set()                                                                                                                 
            #for player in User.appbot._busy_list:                                                                                                
            #    if game_id not in player.data['games_done']:
            #        game = player.data['current_game']
            #        if game is not None:
            #            if time.time() - game._start_time >= 24*60*60:
            #                cancel_games.add(game)
            #
            #for game in cancel_games:
            #    print("About to cancel {}".format(game.info.get_game_id()))
            #    for player in game._players:
            #        User.appbot.send_message_after(player.get_user_id(), 1, self.info.locale(time_is_over), wait=0)
            #        User.appbot.add_waiting(player)
            #        player.data['current_game'] = None
            #
            #    for player in game._players:
            #        await game.cancel(player)
            #        await player.save()

            # 2. SEND GAME TO ALL FREE PLAYERS
            #print("send game to all free players")
            try:
                game_info = GameInfo.get_info(game_id)
                print("num players:", game_info.num_players())
                if  game_info.num_players() >= 2: # why >= here????
                    await self.send_message('No pot ser un joc de 2 jugadors')
                else:
                    skip = []
                    player = User.appbot.get_one_waiting()
                    while player is not None:
                        if game_id in player.data['games_done']:
                            skip += [player]
                        else:
                            game = Game(game_id, [player])
                            player.data['current_game'] = game
                            #await player.data['current_game'].perform_next_action(User.appbot, player)
                            
                            User.appbot.typing_event(player.get_user_id(), 2, partial(player.data['current_game'].perform_next_action, User.appbot, player))
                        player = User.appbot.get_one_waiting()
                    for player in skip:
                            User.appbot.add_waiting(player)
            except Exception as e:
                print('Read exception: {}'.format(e))
                User.appbot.add_waiting(self.info)
                await self.send_message('No t\'he entés')
                
    async def admin_command_send_message_to_specific_user(self, tokens):                                                     
        """                                                                                                                  
        reaction on admin command "/msg"                                                                                     
        """                                                                                                                  
        if len(tokens) >= 3:                                                                                                 
            await User.appbot.send_message(int(tokens[1]), ' '.join(tokens[2:]))                                             
                                                                                                                             
                                                                                                                             
    async def handle_admin_commands(self, msg_text, tokens, tokens_sensitive):                                    
        """                                                                                                                  
        handles commands from admin (a telegram user that has entered the admin pwd correctly)                               
        msg_text         :: message as received from a bot user                                                              
        tokens           :: list of split message words, case-unsensitive
        tokens_sensitive :: list of split message words, case-sensitive
        
        The command are typed by the admin into the chat with the bot.
        """
    
        # call corresponding function for each command
        if tokens[0]   == '/status':
            await self.admin_command_get_bot_status(tokens)
        elif tokens[0] == '/reload_users':
            await self.admin_command_reload_users()
        elif tokens[0] == '/reload_games':
            await self.admin_command_reload_games(tokens)
        elif tokens[0] == '/clear':
            await self.admin_command_remove_user_from_list_of_pending_answers(tokens)
        elif tokens[0] == '/broadcast':
            await self.admin_command_broadcast(tokens, msg_text)
        elif tokens[0] == '/set':
            await self.admin_command_set_interval_points_and_daytime_for_game(tokens)
        elif tokens[0] == '/save':
            await self.admin_command_update_clients_on_mongoDB(tokens)
        elif tokens[0] == '/jugar':
            await self.admin_command_trigger_game_only_for_admin_and_partner(tokens, tokens_sensitive)
        elif tokens[0] == '/global':
            await self.admin_command_send_game_to_all_availabe(tokens, tokens_sensitive)
        elif tokens[0] == '/msg':
            await self.admin_command_send_message_to_specific_user(tokens)
        
        await self.send_message('Done')
        
                                                                                                                                              
    async def handle_text_message(self, msg_text, sender):                                                                                    
        
        # list of admin commands
        list_admin_commands = ['/status', '/reload_users', '/reload_games', '/clear', '/broadcast', '/set', '/save', '/jugar', '/global', '/msg']
        # list of always avaible commands (also in current game), lower-case.
        list_of_unsubscribe_commands = ["baixa", "baja", "unsubscribe", "abmelden", '/baixa', '/baja', '/unsubscribe', "/abmelden"]
        list_of_pause_commands   = ["pausar", "pausar", "pause", "pausieren", "/pausar", "/pause", "/pausieren"]
        list_of_resume_commands   = ["reprendre", "reanudar", "resume", "fortsetzen", "/reprendre", "/reanudar", "/resume", "/fortsetzen"]
        list_always_available_user_commands  = list_of_unsubscribe_commands + list_of_pause_commands + list_of_resume_commands
        # list of user configuration commands
        list_user_config_commands   = ['/delete_games_done', '/freq', '/sociodem', '/world', '/lang', '/dia']
        # list of general users commands
        list_user_command = list_always_available_user_commands + list_user_config_commands
        list_all_commands = list_admin_commands + list_user_command
        
        # append message to message history in user info instance
        self.info.data['message_history'].append(msg_text)
        
        # save, but never react on input from banned user or user that has quit
        if self.info.data['status'] == Status.OUT:
            return
        
        # split message into words, call them tokens; first token is command indentifier
        tokens           = msg_text.lower().split()
        tokens_sensitive = msg_text.split() # Game names must be entered case-sensitively
        
         # exclude empty messages
        if len(tokens) < 1: 
            return
        
        # start
        if self.info.data['status'] == Status.START and tokens[0] == "/start": 
            """if self.info not in User.appbot._busy_list:
                User.appbot.add_busy(self.info)
                # Update info
                if options.dev:
                    welcome = Game('welcome', [self.info])#Game('welcome_dev', [self.info])
                else: 
                    welcome = Game('welcome', [self.info])
                #welcome.callback['legal_yes'] = self.on_welcome_ended_yes
                #welcome.callback['legal_no'] = self.on_welcome_ended_no
                self.info.data['current_game'] = welcome
                await self.info.data['current_game'].perform_next_action(User.appbot, self.info)
            """
            await self.start_game("welcome", add_busy=True, skip_status=False, skip_waiting=False)

        # move up ESSENTIAL commands, like baja, alta. Make sure game isn't deleted with "Baja", complete Baja list below.
        if len(tokens) == 1 and tokens[0] in list_of_pause_commands:
            if self.info.data['status'] == Status.INBOT:
                # set user status to 2. The user can return to status 1 by subcribing again (e.g. writing ALTA)
                self.info.data['status'] = Status.DOWN

                if self.info.data['current_game']:
                    # First, copy the game
                    game = self.info.data['current_game']
                    players = game.get_players()

                    # Remove buttons from current game in users chat
                    for player in players:
                        if player.data['current_game']:
                            await player.data['current_game'].cancel(player)

                    # games need to be deleted from clients db
                    for player in players:
                        player.data['current_game'] = None
                 
                    # Finally, for games with more than one player, send a notification to the other player
                    if len(players)>1:
                        other = players[1]
                        if other == self.info:
                            other = players[0]

                        await other.start_game("on_other_abandoned")
                
                # remove user from pending, busy and waiting list
                User.appbot.remove_user(self.info)
                # start unsubscribe dialogue, to inform user on how to resume again
                await self.start_game("pause", add_busy=False, skip_status=True, skip_waiting=True)
                return
        
        if len(tokens) == 1 and tokens[0] in list_of_unsubscribe_commands:
            # first, delete current games
            if self.info.data['current_game']:
                    # First, copy the game
                    game = self.info.data['current_game']
                    players = game.get_players()

                    # Remove buttons from current game in users chat
                    for player in players:
                        if player.data['current_game']:
                            await player.data['current_game'].cancel(player)

                    # games need to be deleted from clients db
                    for player in players:
                        player.data['current_game'] = None
                 
                    # Finally, for games with more than one player, send a notification to the other player
                    if len(players)>1:
                        other = players[1]
                        if other == self.info:
                            other = players[0]

                        await other.start_game("on_other_abandoned")

            # then, start unsubscribe dialogue, to ask user whether she is sure that she wants to unsubscribe
            await self.start_game("unsubscribe", add_busy=False, skip_status=True, skip_waiting=True)
            return

        # if current_game is sociodem and current message is set to receive input
        print(self.info.get_user_id())
        user_id = self.info.get_user_id()
        if self.info.data['current_game'] != None:
            # only in a couple of games we allow for text input from users (for ethical reasons). Otherwise the user receives some fixed message.
            if self.info.data['current_game'].get_game_id() in ["sociodem_coact"]:
                User.appbot.add_busy(self.info)
                game  = self.info.data.get('current_game', {})
                await Game.react_on_sociodem_written_input(game, User.appbot, self.info, tokens_sensitive)
                return
            elif self.info.data['current_game'].get_game_id() == "world":
                User.appbot.add_busy(self.info)
                game  = self.info.data.get('current_game', {})
                await Game.react_on_world_written_input(game, User.appbot, self.info, tokens_sensitive)
                return
            else:
                if not tokens[0] in list_always_available_user_commands + list_admin_commands + ["/start"]:
                    if tokens[0] in list_all_commands:
                        await self.send_message(self.info.locale(command_other_than_baixa_o_pausa_during_dialogue))
                    else:                            
                        await self.send_message(self.info.locale(wrong_answer))
        
        # ignore non-command-type messages (that don't start with an identifier)
        elif not tokens[0] in list_admin_commands + list_user_command + ['/admin', '/start']:
            await self.send_message(self.info.locale(default_answer_msg))
            return         

        if await self.sender_is_admin():
            if tokens[0]  == '/admin':
                await self.send_message('You are already admin')
                return
            elif tokens[0] in list_admin_commands:
                await self.handle_admin_commands(msg_text, tokens, tokens_sensitive) 
                return
            elif tokens[0] in list_user_command:
                # jump to below general user command handling
                print("admin typed user command")        
        
        # all users get here (admin and users), except of admin sending admin commands
        if len(tokens) == 2 and tokens[0] == '/admin':
            # anybody can enter an admin password like this within the Telegram bot conversation
            self.info.data['admin_pass'] = tokens[1]
            await self.send_message('Done')
            
        if tokens[0][0] == '/' and tokens[0] not in list_user_command:
            return

                        
        elif self.info.data['status'] == Status.INBOT:

            if len(tokens) == 1 and (tokens[0] == '/delete_games_done'):
                # clear users game history (apart from welcome)
                # to be able to play the same games over and over again, WORKING (in developer mode only)
                if options.dev:
                    await UserInfo.delete_games_done(self.info)
            
            elif len(tokens) == 1 and (tokens[0] == '/world'):
                if self.info not in User.appbot._busy_list:
                    # send game world to user
                    # move from waiting list to busy list
                    User.appbot.add_busy(self.info)
                    # get frequency game
                    game = Game('world', [self.info])
                    # set current game of this user to world
                    self.info.data['current_game'] = game
                    # run dialogue with user
                    await self.info.data['current_game'].perform_next_action(User.appbot, self.info)
                       
            elif len(tokens) == 1 and (tokens[0] == '/freq'):
                if self.info not in User.appbot._busy_list:
                    # send game frequencia_relats to user
                    # move from waiting list to busy list
                    User.appbot.add_busy(self.info)
                    # get frequency game
                    game = Game('frequencia_relats', [self.info])
                    # set current game of this user to frequencia_relats
                    self.info.data['current_game'] = game
                    # run dialogue with user
                    await self.info.data['current_game'].perform_next_action(User.appbot, self.info)
            
            elif len(tokens) == 1 and (tokens[0] == '/dia'):
                if self.info not in User.appbot._busy_list:
                    # send game hour to user
                    # move from waiting list to busy list
                    User.appbot.add_busy(self.info)
                    # get hour game
                    game = Game('hour', [self.info])
                    # set current game of this user to hour
                    self.info.data['current_game'] = game
                    # run dialogue with user
                    await self.info.data['current_game'].perform_next_action(User.appbot, self.info)

            elif len(tokens) == 1 and (tokens[0] == '/lang'):
                if self.info not in User.appbot._busy_list:
                    # send game lang to user
                    # move from waiting list to busy list
                    User.appbot.add_busy(self.info)
                    # get language game
                    game = Game('lang', [self.info])
                    # set current game of this user to frequencia_relats
                    self.info.data['current_game'] = game
                    # run dialogue with user
                    await self.info.data['current_game'].perform_next_action(User.appbot, self.info)

            elif self.info.data['current_game'] and self.info.data['current_game'].accepting(self.info):
                await self.info.data['current_game'].wait_for_next_action(User.appbot, self.info, msg_text)
            else:
                print("A case that is not yet in the if else tree for INBOT appeared, ")
                print("tokens[0] = ", tokens[0])
                print("self.info.data['current_game'] = ", self.info.data['current_game'])
                
            
        elif self.info.data['status'] == Status.DOWN:
            if len(tokens) == 1 and (tokens[0] in list_of_resume_commands):
                self.info.data['status'] = Status.INBOT
                await self.start_game("resume", skip_status=True)
  
  
    async def handle_on_message(self, content_type, msg_text, sender):                                                          
        """                                                                                                                     
        handle incoming messages from users                                                                                     
        (callbacks are handled by handle_on_callback() below)                                                                   
        """
        print((self.info.get_user_id(), content_type, msg_text)) 
        if content_type == 'text':
            await self.handle_text_message(msg_text, sender)
        
            


    async def start_game(self, game_id, timeout=5, add_busy=True, skip_status=False, skip_waiting=False):
        """
        mark user as busy
        update current_game field in runtime user dict
        send typing event and start 
        """
        if add_busy:
            User.appbot.add_busy(self.info)

        if not self.info.data['current_game']:
            self.info.data['current_game'] = Game(game_id, [self.info], skip_status=skip_status, skip_waiting=skip_waiting)
            try:
                User.appbot.typing_event(self.info.get_user_id, timeout, lambda: self.info.data['current_game'].perform_next_action(User.appbot, self.info))
                await self.info.save()                  # user_info function save
            except:
                print(self.info.get_user_id, " typing event and performing next action could not be done.")

    async def handle_on_callback(self, query_data):
        """                                                                                                                          
        in telepot, answers to inline buttons have the flavor callback.                                                              
        So all answers to our games will be of this type.                                                                            
        """                                                                                                                          
        # log incoming answer (by user preesing one of the buttons)                                                                  
        print((self.info.get_user_id(), 'callback', query_data)) 
        # stores content of callback data of button event in runtime user_info instance
        self.info.data['message_history'].append(query_data)
        # check if query is part of an ongoing game
        if self.info.data['current_game']:
            # pass to next step in current game, if any.
            await self.info.data['current_game'].wait_for_next_action(User.appbot, self.info, query_data)
        else: # if not, report to commandline
            print("user with id {} has no current game stored - where did this query callback come from?".format(self.info.get_user_id())) 
            
    
    async def handle_on_close(self, ex):                                                                                                  
        """                                                                                                                               
        saves user info with user_info.py save function: updates mongoDB                                                                  
        """                                                                                                                               
        if isinstance(ex, telepot.exception.BadFlavor):
            try:
                Tele_id_kicked = ex.offender["chat"]["id"] # has type int
                print("user with Tele id ", Tele_id_kicked, " stopped the bot or tried to start it while still being in DB.")
            except:
                print("[E] Telegram id could not be retrieved from BadFlavor error message.")
        
        print("Closing user: {}".format(ex))                                                                                              
        await self.info.save()
