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
