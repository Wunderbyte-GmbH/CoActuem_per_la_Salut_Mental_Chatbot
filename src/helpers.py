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
