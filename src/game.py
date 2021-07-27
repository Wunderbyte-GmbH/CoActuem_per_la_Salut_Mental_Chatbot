# external libraries
import pymongo
import sys
import copy
import uuid
import random 
import time
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from functools import partial

# internal libraries
from src.event import Event
from src.status import Status
from src.helpers import list_of_ids
from src.settings import options
from src.conversation_elements import wrong_answer

# load gamesInfo collection from database
from __main__ import gamesInfo
# load clients collection from database
from __main__ import clients
# load bot collection from database
from __main__ import bot


default_freq            = 3*8 # in unit time_unit_of_field_freq  (right now: 3min)
time_unit_of_field_freq = 60*60# a quarter of a minute #0.125*60 # an eighth of a minute # 60*60  # time unit in seconds, i.e. 1h

"""
Block with actions that can be triggered in certain games
"""
def from_freq_to_rhythm(freq):
    """
    takes freq and time_unit_of_field_freq and returns integer in seconds
    """
    rhythm = int(freq*time_unit_of_field_freq)
    return rhythm

async def on_welcome_ended_yes(appbot, user_info, game):
    print("A participant said yes to the IC")
    # change player status to INBOT
    game._players[0].data['status'] = Status.INBOT
    # check waiting queue 
    #appbot.add_event(Event.after(5, lambda: appbot.check_waiting_queue(game._players)))
    
async def on_update_rhythm(appbot, user_info, game):
    user_id = user_info.data['_id']
    # get user choice on frequency
    new_rhythm = from_freq_to_rhythm(int(user_info.data.get('freq', default_freq)))
    # update rhythm in which user receives C+T relats 
    clients.update({"_id": user_id}, {"$set": {'rhythm': str(new_rhythm)}}, upsert=True)
    # update local memory 
    user_info.data['rhythm'] = str(new_rhythm)
    
    
async def on_welcome_ended_no(appbot, user_info, game):
    pass

async def on_unsubscribe_user(appbot, user_info, game):
    # set user status to 2. The user can return to status 1 by subcribing again (e.g. writing ALTA)
    game._players[0].data['status'] = Status.OUT
    # remove user from pending, busy and waiting list
    appbot.remove_user(user_info)
    return

async def on_2p_answer(appbot, user_info, game):
    await appbot.post_invitation_start_game(game.custom_data.get('next_game', 
                                                                 'Col·laboració_2'),
                                      game._players[0],
                                      game)
""" # old code that allows people to activate themselves
async def on_desactivar_mati(appbot, user_info, game):
    # change player status to INBOT
    game._players[0].data['status'] = Status.INBOT
    # check waiting queue 
    appbot.add_event(Event.after(5, lambda: appbot.check_waiting_queue(game._players)))

async def on_activar_mati(appbot, user_info, game):
    # change player status to INBOT
    game._players[0].data['status'] = Status.DOWN
    
async def on_desactivar_total(appbot, user_info, game):
    # change player status to INBOT
    game._players[0].data['status'] = Status.DOWN
"""

# which functions to call when these button answers are received
callbacks = {
    'legal_yes'        : on_welcome_ended_yes,
    'legal_no'         : on_welcome_ended_no,
    '2p_answer'        : on_2p_answer,
    'update_rhythm'    : on_update_rhythm,
    'unsubscribe_final': on_unsubscribe_user#, 
    #'activar_mati'    : on_activar_mati   ,
    #'desactivar_mati' : on_desactivar_mati,
    #'desactivar_total': on_desactivar_total
}

######### calculate timing of next C+T after restart of bot

def when_is_next_CT_according_to_user_rhythm(user_info):
    """
    gets rhythm (or freq) of user and calculates seconds until next event should happen
    """
    #get seconds between consecutive C+T relatos, as user set with /freq
    default_frequency = int(user_info.data.get('freq', default_freq))
    default_rhythm = from_freq_to_rhythm(default_frequency)
    rhythm = int(user_info.data.get('rhythm', default_rhythm))
    # get UTC timestamp of when user finished last C+T game              
    last_CT_finished = user_info.data.get('end_of_last_game_of_type_CT', time.time())
    time_now = time.time()
    if last_CT_finished + rhythm < time_now: # if event should actually already have happened
        return random.randrange(3, 60) # (3, 60*60) send next game within now and the next hour (at random, so not the bot isn't overwhelmed after restart)
    else: 
        return (last_CT_finished + rhythm) - time_now


################################################################################

class GameInfo(object):
    """
    Replicate of mongoDb collection gamesInfo with 
    global variables
    ----------------
    storage    :: copy of gamesInfo
    ids        :: set of all available games
    ids_2p     :: set of all games with 2 players
    ids_1p     :: set of all games with only one player
    ids_skip   :: set of all games that should be skipped
    ids_repeat :: some games are repeatable, e.g. asking for current mood
    
    Attributes
    ----------
    data  :: copy of item in mongoDb collection gamesInfo    

    Methods
    -------
    __init__    :: load game info from mongoDB.gamesInfo (if not already there)
    get_game_id :: return game identifier
    num_players :: gets number of players in game from number of initial messages in game
    get_info    :: get info on game, from insatnce or from mongoDB
    """
    storage    = {}
    ids        = set()    # set of all available games
    ids_2p     = set()    # set of all games with 2 players
    ids_1p     = set()    # set of all games with only one player
    ids_skip   = set()    # set of all games that should be skipped
    ids_repeat = set()    # some games are repeatable, e.g. asking for current mood

    def __init__(self, game_id, data=None):
        # loads game data from mongoDB
        self.data = data if data else gamesInfo.find_one({'_id': game_id})
        # load messages for this game successively
        for message_id, message in self.data['messages'].items():
            message['_id'] = message_id

    def get_game_id(self): 
        """
        return string with game identifier 
        """
        return self.data['_id']

    def num_players(self):
        """ 
        calculates number of games that can play game self, 
        (relatos type 1 and 2: 1 player, relatos type 3: 2 players)
        from the length of the initial messages field of the game
        """
        return len(self.data['initial_messages'])

    @staticmethod
    def get_info(game_id, data=None):
        """
        gets GameInfo from Game dict, load from mongoDB
        """
        if game_id in GameInfo.storage.keys(): # if game loaded to object instance
            return GameInfo.storage[game_id]   # return this info
        else:
            info = GameInfo(game_id, data)     # load Game info from MongoDB
            GameInfo.storage[game_id] = info   # store in object instance
            return info


class Game(object):
    """
    A class that serves as short memory for the games in the bot. 
    collects info on the game a player is currently playing or has played.
    in mongoDB: stored at first in current_game and then in game_history of each player (db.clients)
    Contains more info than mongoDB collection gamesInfo, which are first stored
    current_game of a bot user and then cast to the game history of the user.
    
    storage     ??
    
    Attributes
    ----------
    _players        ::  list of players
    _answers        ::  dict with answers given during game play
    _ended          ::  list of players for this game is completed
    _start_time     ::  current time when Game instance is created
    _end_time       ::  current time when Game instance is finished
    _skip_status    ::  bool, 
    _skip_waiting   ::

    custom_data     :: can hold ID of next game to be played (for 2 player games and respective invitation) 
    _editor         :: allows to edit buttons later
    _edit_msg_ident :: allows to work with message further
    _id             :: random Universial Unique IDentifier for game instance
    _last_message   :: dict with complete message info as given in gamesInfo
    _ignore         ::
    _ca_complete    ::
    info            :: data og corresponding GameInfo instance
    _message_ids    ::
    
    Methods
    -------
    __init__             :: 
    get_game_id          :: return game identifier (by calling method with same name from GamInfo)
    __str__              :: custom str method for debugging
    get_players          :: 
    start_game           :: update waiting list and busy list and set "current_game" of user, then start game
    perform_next_action  ::
    end_game             :: schedule next game, update parameters after end of game
    accepting            ::
    wait_for_next_action ::
    on_sent              ::
    cancel               :: Remove buttons of last message with buttons from dialogue with user
    resume               :: resume game where it was interrupted, e.g. after restart of bot
    to_game_dict         ::
    from_game_dict       ::
                         
    _message_ids registers the id of the (currently send?) message within the game
    """
    storage = {}

    def __init__(self, game_id, player_infos, answers=None, timestamps_answers=None, skip_status=False, skip_waiting=False):
        self._players             = player_infos
        self._answers             = answers if answers else {}
        self._timestamps_answers  = timestamps_answers if timestamps_answers else {}
        self._ended               = []
        self._start_time          = time.time() # get current time in sec
        self._end_time            = 0           # get current time in sec
        self._skip_status         = skip_status
        self._skip_waiting        = skip_waiting

        # Next game storage
        self.custom_data     = {} 

        # Buttons
        self._editor         = {} # allows to delete sent messages, e.g. Buttons
        self._edit_msg_ident = {}

        # more game data
        self._id             = str(uuid.uuid4()) # crate random Universial Unique IDentifier for the "played game instance"
        self._last_message   = {}                # dict of last messages (to the one or several player(s))
        self._ignore         = dict(zip(self._players, [True] * len(player_infos))) # dict with telegram ID(s) and corresponding ignore status true
        self._ca_complete    = dict(zip(self._players, [False] * len(player_infos))) # dict with telegram ID(s) and corresponding _ca_complete status false

        # load general static game info as stored in gamesInfo mongoDB
        self.info            = GameInfo.get_info(game_id)
        self._message_ids    = dict(zip(self._players, self.info.data['initial_messages']))
        
        # log game initiation
        print("Game {} created with players: {}".format(game_id, [p.get_user_id() for p in player_infos]))
        
    def preload_all_games():
        """
        load documents from the mongoDB collection gamesInfo
        into a GameInfo object instance
        """
        for game in gamesInfo.find({}): # for all documents in mongodb collection
            print(game["_id"])
            # load game_id and document into GameInfo sict storage
            GameInfo.storage[game['_id']] = GameInfo.get_info(game['_id'], game)

        GameInfo.ids        = set([game_id for game_id in GameInfo.storage.keys()])
        GameInfo.ids_2p     = set([game_id for game_id, game in GameInfo.storage.items() if game.num_players() == 2])
        GameInfo.ids_1p     = set([game_id for game_id, game in GameInfo.storage.items() if game.num_players() == 1])
        GameInfo.ids_skip   = set([game_id for game_id, game in GameInfo.storage.items() if game.data.get('skip', False)])
        GameInfo.ids_repeat = set([game_id for game_id, game in GameInfo.storage.items() if game.data.get('repeatable', False)])

    def get_game_id(self):
        """
        return string with game identifier
        """
        return self.info.get_game_id()

    def get_message_id(self, user_info):
        """
        return string with game identifier
        """
        print("self._message_ids", self._message_ids)
        return self._message_ids[user_info]

    def __str__(self):
        """
        custom str method of Game object: 
        prints current status for debugging puposes,
        called by print(myGame) where myGame is the instance
        """
        info_string = "\n"
        info_string += "    game._id: {}\n".format(self.get_game_id())
        info_string += "    game.players: {}\n".format([p.get_user_id() for p in self._players])
        info_string += "    game.ignore: {}\n".format({p.get_user_id(): i for p, i in self._ignore.items()})
        info_string += "    game.answers: {}\n".format(self._answers)
        info_string += "\n"
        return info_string

    def get_players(self):
        """
        return list of user_ids that play this game
        """
        return self._players
    
    async def start_game(self, appbot, game_id, user_id):
        """
        First, update waiting list and busy list and set "current_game" of user, then start game
        """
        # get user info corresponding to user id
        player  = appbot.get_user_info(user_id)
        # remove from waiting list and add to busy list
        appbot.add_busy(player)
        # load game info
        game = Game(game_id, [player])
        # set current game for this user
        player.data['current_game'] = game
        # warn equip OS which game we play next
        if options.dev:
            await appbot.send_message(user_id, 'Hola equipo, the next dialogue is called: <b>' + str(game_id) + "</b>. ")
        # start the game with the user
        await player.data['current_game'].perform_next_action(appbot, player)        


    async def perform_next_action(self, appbot, user_info, inputs=None):
        """
        1) get message, set _last message
        2) if game has ended, end game
        3) if user is DOWN, return
        4) text ' message text in user languag
        5) display field for 2players games
        6) buttons, img, pdf --> send message
        7) get button editor (to be able to delete buttons in next step)
        8) ?
        9) Save new state in user_info
        
        message types: 
        'NA' : no answer
        'SA' : select answer
        'CA' : compare games: presoner 1,2,3 y snowdrift
        'WA' : wait answer (await answer message type without buttons, no next message given)
        """
        
        # get message content and update _last_message 
        if self._message_ids[user_info]:
            # get the current message content from GameInfo for user
            message = self.info.data['messages'][self._message_ids[user_info]]
            # update _last_message
            self._last_message[user_info] = message
        else:
            # get the last message content from Game for user
            message = self._last_message[user_info]

        # If game has ended for this user, stop!
        if user_info.get_user_id() in self._ended:
            # cast game from current game to game history, update points:
            await self.end_game(appbot, user_info, message)
            return

        if not (user_info.data['status'] == Status.INBOT 
                or user_info.data['status'] == Status.START) and not self._skip_status:
            # if user is DOWN don't play games
            return
        
        #print("self._answers: " + str(self._answers))

        # get message text in the correct language
        text = user_info.locale(message['text'])

        # alter message text in case it has special formatting set by the display field in gamesInfo
        # where variables can be replaced by given answers
        
        if 'display' in message: # display field in game jsons allows to evaluate the button results of players and adapt the answer accordingly
            variables           = copy.copy(self._answers) # get a copy of the dict that contains all button callbacks = answers given by the players during the game
            #variables['points'] = self._players[0].data['points'] OBSOLETE?
            #variables['time']   = time.time()                     OBSOLETE?
            for name, calc in message['display'].items(): # name :: dict key, calc :: entry values conating ternary operator = if else statements
                variables[name] = eval(calc.format(**variables), {"__builtins__": None}, {'int': int, 'str': str, 'float': float})
            try:
                text = text.format(**variables) # try to replace variables in the output text with evaluated button results 
            except Exception as e:
                # if text can't be adapted, don't adapt text 
                print('[E] {} in formatting {} with {}, raised {}'.format(user_info.get_user_id(), text, variables, e))
                text = text

        ### get other message objects like buttons, images or pdfs
        buttons = None
        pdf     = None
        img     = None
        if 'vars' in message:
            for var in message['vars']:
                if type(var) == dict: 
                    if   'type' in var and var['type']  == 'button':
                        # join button texts and callback values in 
                        buttons = [(user_info.locale(text), value) for text, value in zip(var['texts'], var['values'])]
                    elif 'type' in var and var['type']  == 'pdf'   :
                        # dinstinguish between language specific pdf and general pdf
                        pdf = var['file_name'].get(user_info.data['language'], var['file_name'])
                    if  'type2' in var and var['type2'] == 'img'   :
                            img = var['file_name']
        
        # send message with all gathered objects/items
        sent = await appbot.send_message(user_info.get_user_id(), text, img=img, buttons=buttons, pdf=pdf)
        
        # get necessary info to edit sent messages to delete buttons
        if buttons is not None and sent is not None:
            # get button editor (so buttons can be deleted later)
            self._editor[user_info]         = telepot.aio.helper.Editor(appbot.bot, sent)
            # get message_identifier (argument of deleteMessage())
            self._edit_msg_ident[user_info] = telepot.message_identifier(sent)

        # Go to next message unless current message is WA
        if not message['type'] == 'WA':
            next_id = message['next']
            # if message['next'] is a string, it is the id of the next game
            if type(next_id) != dict:
                self._message_ids[user_info] = next_id
            
            
            if (message['type'] == 'NA') and next_id: # if "NA" simply wait_for_next_action
                await self.wait_for_next_action(appbot, user_info, force=True)
            elif message['type'] == 'SA' or message['type'] == 'CA': # else do not ignore any more
                self._ignore[user_info] = False

            if next_id is None:
                self._end_time = time.time() # get current time in sec
                self._ended += [user_info.get_user_id()]
                await self.end_game(appbot, user_info, message)

        # Save new state in user_info of all players of this game instance
        for player in self._players:
            await player.save()


    async def end_game(self, appbot, user_info, message): 
        """
        This function is called by perform next action in case 
        the game is ended, indicated by self._ended
        This functions stores info from current_game to game_histoy 
        in the clients collection in mongoDB
           
        1) if game was of type C or T, schedule next game of type C or T
        2) move current_game to game_history, add to games done
        3) add user to waiting list
        4) perform next action (as defined in callbacks dicts)
        5) update points of user
        6) save user info
        """
        # log entry
        print("Game {} finished with players: {}".format(self.info.get_game_id(), [p.get_user_id() for p in self._players]))

        # update end_of_last_game_of_type_CT so that after bot was restarted, the new time can be calculated
        user_info.data['end_of_last_game_of_type_CT'] = time.time()
        
        ### schedule next game of type C+T
        # if game was of type C or T (compartir vivencias, Trobar Solucions Junts)
        if user_info.data['current_game'] is not None:
            # get game type
            game_name = self.get_game_id()
            # if story in sequence of stories list, schedule next game from list
            ordered_list_of_games = bot.find_one({"_id": 'objects_to_be_sent'})["list_relatosCT_plus"]
            if game_name in ordered_list_of_games + ["resume"]: # after a player resumed the bot, the sequence should start where it ended.
                # timing of next game equals rhythm of this user
                rhythm = int(user_info.data.get("rhythm", str(from_freq_to_rhythm(default_freq))))
                # schedule next event
                user_info.set_next_relats_event_from_list(appbot, rhythm)
        
        # move info from current_game to game_history, and mark game as done (so it won't be played again)
        if user_info.data['current_game'] is not None:
            user_info.data['game_history'].append(user_info.data['current_game'].to_game_dict(False))
            user_info.data['current_game'] = None
            if not self.info.get_game_id() in ['lang', "dia", 'frequencia_relats', 'world']:
                user_info.data['games_done'].add(self.info.get_game_id())
        
        # if _skip_waiting=False, the user is appended to the waiting list
        if not self._skip_waiting:
            appbot.add_waiting(user_info)

        # actions stored in gamesInfo DB: "2p_answer", "legal_yes", "legal_no", 
        # see gloabl variable callbacks in game.py:
        # actions are called
        if 'action' in message and message['action'] in callbacks:
            await callbacks[message['action']](appbot, user_info, self)

        
        # iterates through points as given in gamesInfo, e.g. ["1"] or ["5", "5"]
        # updates points of user
        if 'points' in self.info.data:
            for i, points_calc in enumerate(self.info.data['points']):
                if self._players[i] == user_info:
                    pts = eval(points_calc.format(**self._answers), {"__builtins__": None}, {'int': int, 'str': str, 'float': float})
                    user_info.data['points'] += pts

        # Save new state in user_info
        await user_info.save()

    def accepting(self, user_info):
        """
        """
        return not self._ignore[user_info]
      
    async def react_on_sociodem_written_input(self, appbot, user_info, tokens): 
        user_id = user_info.get_user_id()
        print("Waiting to check message id..", self._message_ids[user_info])
        message_id_in_sociodem = self._message_ids[user_info]
        if message_id_in_sociodem in ["p_3", "p_3-2"]:
            self._answers["area"] = ' '.join(tokens).replace("'", "’")
            user_info.data[self._last_message[user_info]['save']] = ' '.join(tokens).replace("'", "’")
            # Save new state in user_info
            await user_info.save()
            # set the next message id 
            if message_id_in_sociodem == "p_3":
                self._message_ids[user_info] = "p_3c"
            elif message_id_in_sociodem == "p_3-2":
                self._message_ids[user_info] = "p_3c-2"
           # make this message get to the other player
            await self.perform_next_action(appbot, user_info)
        elif message_id_in_sociodem in ["p_4", "p_4-2"]:
            self._answers["codi"] = ' '.join(tokens).replace("'", "’")
            user_info.data[self._last_message[user_info]['save']] = ' '.join(tokens).replace("'", "’")
            # Save new state in user_info
            await user_info.save()
            # set the next message id 
            if message_id_in_sociodem == "p_4":
                self._message_ids[user_info] = "p_4c"
            if message_id_in_sociodem == "p_4-2":
                self._message_ids[user_info] = "p_4c-2"
            # make this message get to the other player
            await self.perform_next_action(appbot, user_info)
            
    def has_correct_time_format(self, token):
        """
        user should enter the time in format hh:mm. otherwise return False
        """
        hctf = False
        if len(token) == 5 and token[0].isdigit() and token[1].isdigit() and token[3].isdigit() and token[4].isdigit() and token[2] in [":", ",", ".", ";"]:
            if int(token[0:2]) < 24 and int(token[3:5]) < 60:
                hctf = True
        return hctf               
        
            
    async def react_on_world_written_input(self, appbot, user_info, tokens): 
        user_id = user_info.get_user_id()
        print("Waiting to check message id..", self._message_ids[user_info])
        message_id_in_world = self._message_ids[user_info]
        if message_id_in_world in ["3si", "3si_else"]:
            token = ' '.join(tokens)
            self._answers["time"] = "'"+' '.join(tokens)+"'" # extra 's to avoid evaluate function
            user_info.data[self._last_message[user_info]['save']] = ' '.join(tokens).replace("'", "’")
            # Save new state in user_info
            await user_info.save()
            # set the next message id accoding to whether input has format hh:mm
            hcf = self.has_correct_time_format(token)
            if token == "NO":
                self._message_ids[user_info] = "3si_nvr"
            elif hcf: 
                self._message_ids[user_info] = "3si_c"
            else: 
                self._message_ids[user_info] = "3si_else"
            # make this message get to the other player
            await self.perform_next_action(appbot, user_info)
        

    async def wait_for_next_action(self, appbot, user_info, inputs=None, force=False, scheduled=False):
        if user_info not in self._last_message:
            print("{} < Ignored due to not having last message".format(user_info.get_user_id()))
            print("{} < Ignored due to not having last message".format(self._last_message))
            return

        if self._ignore[user_info] and not scheduled and not force:
            print("{} < Ingored due to flagged to ignore".format(user_info.get_user_id()))
            return
        self._ignore[user_info] = True
        
        # local variable that checkes if message of type "CA" was handled completed
        # ca_incomplete is a local variable
        # _ca_complete is an iformation stored with each user in the current game        
        ca_incomplete = False
        # if one user answers a 'CA' message, and the othe user has not completed
        # his 'CA' message the first user get's a wait message telling him to wait for the answer
        if self._last_message[user_info]['type'] == 'CA':
            self._ca_complete[user_info] = True # set users "CA" message as complete
            force = inputs is not None
            # check if the other player has an unanswered "CA"
            for player in self._players:
                if not player == user_info: # get id of the other user
                    if not self._ca_complete[player]: # if the other users "CA" emssage is not completed
                        ca_incomplete = True
                        # send wait message 
                        wait_msg = self._last_message[user_info].get('waiting_text', None)
                        if wait_msg:
                            appbot.send_message_after(user_info.get_user_id(), 1, user_info.locale(wait_msg), wait=0)
            # force is TRUE if not: force is False and ca_incomplete is True
            force = force or not ca_incomplete
        """
        if self._last_message[user_info]['type'] == 'SA' and len(self._players) == 2:
            for player in self._players:
                if not player == user_info:
                    if not self._last_message[player]['type'] == 'WA':
                        self._ignore[user_info] = True
                        appbot.add_event(Event.after(1, lambda: self.wait_for_next_action(appbot, user_info, inputs, force, True)))
                        return
        """
        

            

        if self._last_message[user_info]['type'] == 'SA' or force: 
            """
            ::: self._last_message[user_info]['type'] == 'SA'
            ::: force
            """
            if 'vars' in self._last_message[user_info]:
                user_vars = self._last_message[user_info]['vars']

                for var in user_vars:
                    # Clear buttons if any
                    if type(var) == dict:
                        if 'type' in var and var['type'] == 'button':
                            found = False
                            inputs = inputs.lower()
                            for text, val in zip(var['texts'], var['values']):
                                text = user_info.locale(text)
                                if inputs == text.lower() or inputs == val.lower():
                                    found = True
                                    inputs = val
                                    break

                            if not found:
                                appbot.send_message_after(user_info.get_user_id(), 2, user_info.locale(wrong_answer), wait=0)
                                self._ignore[user_info] = False
                                return

                            await self._editor[user_info].editMessageReplyMarkup(reply_markup=None)
                            self._editor[user_info] = None
                            self._edit_msg_ident[user_info] = None


                        # Create variable
                        var_name = var['name']
                        new_var = dict(zip([var_name], [inputs]))

                        all_vars = copy.copy(self._answers)
                        all_vars.update(new_var)
                        all_vars['points'] = self._players[0].data['points']
                        all_vars['time'] = time.time()

                        if 'condition' in var and var['condition']:
                            try:
                                passes = eval(var['condition'].format(**all_vars), {"__builtins__": None}, {'int': int, 'str': str, 'float': float})
                            except Exception as e:
                                print("Error in condition {} with vars {}: {}".format(var['condition'], all_vars, e))
                                passes = False

                            if not passes:
                                appbot.send_message_after(user_info.get_user_id(), 2, user_info.locale(wrong_answer), wait=0)
                                self._ignore[user_info] = False
                                return
                    else:
                        # Create variable
                        var_name = var
                        new_var = dict(zip([var_name], [inputs]))

                    # Save to _answers
                    self._answers.update(new_var)
                    
                    # update _timestamps_answers
                    time_now = time.time()
                    new_time = dict(zip([str(time_now)], [var_name]))
                    self._timestamps_answers.update(new_time)
                    
            # Save inputs if any
            if 'save' in self._last_message[user_info] and inputs:
                # the user might decide, not to change the configuration. Then the stored value shouldnt be overwritten.
                if not inputs == 'dontsave':
                    user_info.data[self._last_message[user_info]['save']] = inputs

            # next_id, can be string or dict
            next_id = self._last_message[user_info]['next']
            print("next_id", next_id)
            # next_id is a dict, when the next message to be sent depends 
            # on former or current users answers
            while type(next_id) == dict:
                # when next_id depends on an answer given somewhat earlier in the game: field replace_variable in game json
                if "replace_variable" in next_id:
                    key = next_id["replace_variable"] 
                    if self._answers == {}: # wait until other person answered
                        print("self._answers is an empty dict")
                    else:
                        answer_with_same_key = copy.copy(self._answers)[key]
                        next_id = next_id[key][answer_with_same_key] # next_id = next_id[key][self._answers[answer_with_same_key]]
                else: # if next_id depends the answer given in the current message
                    key = list(next_id.keys())[0]
                    next_id = next_id[key][self._answers[key]]
                self._message_ids[user_info] = next_id

            # Trigger message for the other user in a 2player games
            if not ca_incomplete and 'triggers' in self._last_message[user_info]:
                # get the other players id
                for player in self._players:
                    if not player == user_info:
                        # set the other players message id to the message triggered by users answer
                        self._message_ids[player] = self._last_message[user_info]['triggers']
                        # make this message get to the other player
                        await self.perform_next_action(appbot, player, inputs)


            if not ca_incomplete:
                if self._last_message[user_info]['wait']:
                    wait_time = self._last_message[user_info]['wait']
                else:
                    try:
                        wait_time = len(user_info.locale(self.info.data['messages'][self._message_ids[user_info]]['text'])/100)
                        print(" I was here and waited even", wait_time)
                        if wait_time > 20:
                            wait_time = min(wait_time, random.uniform(12, 20))
                    except:
                        wait_time = random.uniform(4, 6)

                #print("{} > Waiting: {}s".format(user_info.get_user_id(), wait_time))


                # print('Waiting {} secs'.format(wait_time))
                appbot.typing_event(user_info.get_user_id(), wait_time, lambda: self.perform_next_action(appbot, user_info, inputs))

        # Save new state of al users that play this game
        for player in self._players:
            await player.save()

    async def on_sent(self, user_info):
        """
        """
        pass

    async def cancel(self, user_info):
        """
        Remove buttons of last message with buttons from dialogue with user
        """
        print("Canceling {} for {}".format(self.info.get_game_id(), user_info.get_user_id()))

        if user_info in self._editor and self._editor[user_info]:
            try:
                await self._editor[user_info].editMessageReplyMarkup(reply_markup=None)
            except:
                print("Failed at removing buttons!")

            self._editor[user_info] = None
            self._edit_msg_ident[user_info] = None


    async def resume(self, appbot, user_info):
        """
        Try to resume game where it was interrupted
        """   
        if hasattr(self, '_last_message') and user_info in self._last_message and 'type' in self._last_message[user_info]:
            if self._last_message[user_info]['type'] == 'NA':
                if user_info.get_user_id() in self._ended:
                    await self.perform_next_action(appbot, user_info, None)
                else:
                    await self.wait_for_next_action(appbot, user_info, force=True)
        
            elif self._last_message[user_info]['type'] == 'SA' and self._ignore[user_info]:
                await self.perform_next_action(appbot, user_info, None)
        
            elif self._last_message[user_info]['type'] == 'CA' and self._ignore[user_info]:
                await self.wait_for_next_action(appbot, user_info, None, force=True)
        else:
            await self.perform_next_action(appbot, user_info, None)        

    def to_game_dict(self, all_data=True):
        """
        Join all info on the current game in a dict.
        This is currently stored below clients.current_game and is overwritten once the 
        game is finished 
        """
        game_dict = {
            'gameId': self.info.get_game_id(),
            'players': list_of_ids(self._players),
            'answers': self._answers,
            'timestamps_answers': self._timestamps_answers,
            'ended': self._ended,
            'start_time': self._start_time,
            'end_time': self._end_time,
            'ignore': None if not all_data else {info.get_user_id(): status for info, status in self._ignore.items()},
            'messages_ids': None if not all_data else {info.get_user_id(): message_id for info, message_id in self._message_ids.items()},
            'last_message': None if not all_data else  {info.get_user_id(): None if not msg else msg['_id'] for info, msg in self._last_message.items()},
            'ca_complete': None if not all_data else {info.get_user_id(): status for info, status in self._ca_complete.items()},
            'edit_msg_ident': None if not all_data else {info.get_user_id(): msg for info, msg in self._edit_msg_ident.items()},
            'skip_status': self._skip_status,
            'skip_waiting': self._skip_waiting,
            'custom_data': self.custom_data
        }
        if hasattr(self, '_id'):
            game_dict['_id'] = self._id
        return game_dict


    @staticmethod
    def from_game_dict(game_dict, appbot):
        """
        
        """
        try:
            return Game.storage[game_dict['_id']]
        except:
            players = [appbot.get_user_info(user_id) for user_id in game_dict['players']]

            # If it is a 2p game, it might have been added in-between to the storage
            try:
                return Game.storage[game_dict['_id']]
            except:
                pass

            game = Game(game_dict['gameId'], players, game_dict['answers'], game_dict.get('timestamps_answers', {}))

            # Build player dependant statuses
            for player in game.get_players():
                player_id = str(player.get_user_id())
                game._message_ids[player]    = game_dict['messages_ids'].get(player_id, None)
                game._ignore[player]         = game_dict['ignore'].get(player_id, False)
                game._last_message[player]   = game.info.data['messages'].get(game_dict['last_message'].get(player_id, None))
                game._ca_complete[player]    = game_dict['ca_complete'].get(player_id, False)
                game._edit_msg_ident[player] = game_dict['edit_msg_ident'].get(player_id, None)
                game._editor[player]         = None if game._edit_msg_ident[player] is None else telepot.aio.helper.Editor(appbot.bot, tuple(game._edit_msg_ident[player]))

            # Status flags
            game._ended        = game_dict['ended']
            game._skip_status  = game_dict['skip_status']
            game._skip_waiting = game_dict['skip_waiting']
            game._start_time   = game_dict.get('start_time', 0)
            game._end_time     = game_dict.get('end_time', 0)            
            game.custom_data   = game_dict.get('custom_data', {})

            # Load ID, store and return
            game._id = game_dict['_id']
            Game.storage[game_dict['_id']] = game
            return game
    
