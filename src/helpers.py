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

def list_of_ids(players): 
    """
    extracts id of all players in list of players, returns list of ids
    
    players : list of dicts
        list of dicts with info on player    
    returns : list of strings
    
    formerly called: as_ids
    """
    return [p.get_user_id() for p in players]

def list_of_ids_as_str(players, delim=', '):
    """
    extracts id of all players in list of players, returns list of ids as string
    
    players : list of dicts
        list of dicts with info on player    
    returns : string with list of strings (without [])
    """
    return delim.join(map(str, list_of_ids(players)))
