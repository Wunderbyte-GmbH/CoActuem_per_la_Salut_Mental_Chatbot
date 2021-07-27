# external libraries
from enum import Enum # Enum: Base class for creating enumerated constants. 

class Status(Enum): 
    # status of a user
    START = 0 # starting value of any user, triggers welcome/welcome_dev game
    INBOT = 1 # user still willing to receive/ receiving messages
    DOWN  = 2 # user paused the bot
    OUT   = 3 # user quit or was banned

    def __int__(self): 
        # returns integer that represents status
        return self.value
