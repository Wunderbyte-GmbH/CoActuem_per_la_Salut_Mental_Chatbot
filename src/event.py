# external libraries
import time
import datetime
import pytz

class Event(object):
    """
    A class to handle timing and recurrence of games, naming them events.
    
    Attributes
    ----------
    
    _timestamp     ::  time at which event is planned to start
    _callback      ::  performs some action, eg. check_waiting_queue in Event.recurring(60, self.check_waiting_queue, True)
    _on_done       ::  lambda function as function parameter, e.g. lambda: self.send_typing(chat_id)
    _every         ::  int (seconds)
    _recurring     ::  bool, tells if event is recurring or not
    _daytime_only  ::  bool,
    

    Methods
    -------
    __init__     :: creates new Events instance 
    __call__     :: call instance as a function
    when         :: return timestamp (when event is planned)
    is_recurring :: returns bool _recurring 
    recurse      :: sets new timestamp calculated from _every and current time
    set_every    :: sets event attribute _every and first occurrence of event (now + every)
    after        :: create event instance of event after seconds seconds
    recurring    :: create event instance of recurring event that repeats after every seconds
    
    Python time function time.time() returns the exact seconds (with many digits) since January 1, 1970, 00:00:00
    
    """

    def __init__(self, timestamp, callback, on_done=None, daytime_only=False, is_new_game=False):
        self._timestamp     = timestamp # seconds since 1970 UTC   
        self._callback      = callback  # function
        self._on_done       = on_done   # function
        self._every         = 0         # seconds that set the periodicity of the event
        self._recurring     = False     # bool, tells if event is recurring or not
        self._daytime_only  = daytime_only     # bool, 
        self._is_new_game   = is_new_game

    async def __call__(self):     
        """
        Defining a custom __call__() method in the meta-class allows the class's
        instance to be called as a function, not always modifying the instance 
        itself.
        
        returns bool:
        True:   if event is only set for daytime AND it's night
        False:  otherwise
        """
        if time.time() >= self._timestamp:   # as soon as planned time for event is reached...
            # Do nothing between 19-07
            if self._daytime_only:
                hour = int(datetime.datetime.fromtimestamp(int(time.time())).astimezone(pytz.timezone("Europe/Madrid")).strftime('%H'))
                #print("Daytime check at {}: {}".format(hour, hour > 19 or hour < 7))
                from_morning = 7
                to_evening = 21
                if hour >= to_evening or hour < from_morning:
                    # check how long it is until sunrise, postpone action until then.
                    if self._is_new_game:
                        if hour < from_morning:
                            wait_till_dawn = (from_morning+24-to_evening)*60*60#= wait until from_morning and (8-hour) and wait the time since to_evening (24-to_evening+hour)# (8-hour)*60*60 
                        elif hour >= to_evening:
                            wait_till_dawn =((24-to_evening)+from_morning+(hour-to_evening))*60*60#= wait until from_morning and (24-hour) and wait the time since to_evening (hour-to_evening)# (24-hour)*60*60
                        else:
                            wait_till_dawn = 0
                        print("waiting_till_dawn: ", wait_till_dawn)
                        time.sleep(wait_till_dawn) 
                    await self._callback()     # e.g. self._callback() = check waiting queue
                    if self._on_done:
                        await self._on_done()  # e.g. self._on_done() = lambda: self.send_typing(chat_id)
                    return True
            
            # if not _daytime_only, the bot can is allowed to launch the event: 
            await self._callback()     # e.g. self._callback() = check waiting queue
            if self._on_done:
                await self._on_done()  # e.g. self._on_done() = lambda: self.send_typing(chat_id)
            return True
        # if the time hasn't come yet: return false (if not time.time() >= self._timestamp)
        return False
    
    def when(self):
        # return timestamp of event (for when is event planned?)
        return self._timestamp

    def is_recurring(self):
        # return bool, telling if event is recurring or not
        return self._recurring

    def recurse(self):
        # returns next occurrence of event, calculated with _every from now
        self._timestamp = time.time() + self._every
        return self

    def set_every(self, every):
        # set event attribute _every and first occurrence of event (now + every)
        self._every     = every
        self._timestamp = time.time() + every      

    @staticmethod          
    def after(seconds, callback, on_done=None, daytime_only=False, is_new_game=False):
        """
        create instance of event after seconds seconds after calling this function,
        with callback and on_done functions
        """
        return Event(time.time() + seconds, callback, on_done, daytime_only=daytime_only, is_new_game= is_new_game)

    @staticmethod           
    def recurring(every, callback, daytime_only=False, on_done=None):
        """
        create instance of recurring event, possibly with daytime restriction
        with callback and on_done functions
        every :: seconds between consecutive events of this type.
        """
        event               = Event(time.time() + every, callback, on_done)
        event._every        = every
        event._recurring    = True
        event._daytime_only = daytime_only
        return event
