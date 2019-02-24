#  Python Stream Deck Library - FilterPlugins
#      Released under the MIT license
#
#      https://github.com/Kalle-Wirsch
#

"""
Module StreamDeckFilter

StreamDeckFilter is designed to modify the callback behavior of the StreamDeck class while
hiding the internal changes to existing implementations.

Generally StreamDeck invokes the Callback-Function, whenever a key-status changed,
i.e. a key is pressed or released. The callback can be set with deck.set_key_callback(self, callback),
and looks like this:
    key_callback(self, k, new_state)
        where k is the changed key and new_state is the new key state
        (pressed = True, released = False)

Usage:
    StreamDeckFilter allows to change the callback behavior by assigning a specific Filter to each key as follows:
        deck.filter[key] = TempoFilter()

Implemented filters:
    CallBackFilter()
        Base class, that calls the callback function on each internal device read

    StateChangedFilter()
        The callback function is called only if a key k changed its state

    DebounceFilter(default_state=False, key_delay=0.003)
        the callbackfunction is called only,
        if the state did not already change within the last key_delay seconds
        Therefore filtering out fast state chenges do to "key chattering",
        i.e. fast state changes, when the key is "almost" pressed.

    TempoFilter(default_state=False, key_delay=0.003, tempo_delay=0.3)
        As Debouncefilter but returns
        - True if the key is pressed less then tempo_delay seconds
        - False if key is pressed for more than tempo-delay seconds

Extendability:
    You can simply subclass CallbackFilter (or any other of the above filter classes)
    and override CallBackFilter.map_states(self, new_state)

JSON support:
    See JSONexample.py

Known Bugs:
    Debounce filter doesn't work well with long key_delays.
    It should reset to False after key_delay seconds or at least fter some internal delay
    or clock of of an MVC View-Refresh

Future Development plans
    I will add more filters in the future e.g.

    HoldFilter
        changes the state if key is kept pressed/released for countdown_delay seconds
    CountDownFilter
        changes the state after countdown_delay time, but calls back every count_delay seconds

"""

from time import time
from functools import wraps


def manage_states(f):
    """
    decorator function for CallbackFilter.mapstates()
    registers state, time and delay of last callback
    """
    @wraps(f)       # make updater look like decorated function in traceback
    def updater(self, new_state, *args, **kwargs):
        # registere delay inside CallbackFilter.mapstates
        self._delay = time() - self._last_key_time
        rv = f(self, new_state, *args, **kwargs)   # call function
        if rv is not None:
            # register old physical state inside CallbackFilter.mapstates
            self._last_key_state = new_state
            # register old callback state inside CallbackFilter.mapstates
            self._last_cb_state = rv
            # register time inside CallbackFilter.mapstates
            self._last_key_time = time()
        return rv
    return updater


class CallBackFilter(object):
    """
    Serves as base for Filters that map physical states (True, False) to a different range, type of values
    Simply assign a filter to a specific key like this:  deck.filter[key] = StateChangedFilter()
    """

    def __init__(self, default_state=False):
        self._last_key_state = False            # last physical state callback time
        self._last_cb_state = default_state     # last state reported to callback function
        self._last_key_time = time()            # time of last callback
        self._delay = 0.0                       # delay since last callback

    @manage_states  # register states, time and delay
    def map_states(self, new_state):
        """
        - maps/filers pysical states(pressed=True, released=False) to before callback to client
        - stores old states, times and delays(since last callback)
        - in principle can be overridden to return anything e.g.
        Enum('MyStates', 'LONG_PRESS, SHORT_PRESSED, NOTPRESSED_FOR_300_MILLISECONDS, PRESSED_5_TIMES_IN_5_MINUTES, ...')
        Assumption: map_states returns None <= > no callback will be made
        """
        return new_state  # do not filter anything

    def json_serialize(self):
        """
        Serialize only non-protected, i.e. non volatile attributes.
        Designed to be part of json.Encoder.default(self, obj): -> add the following lines
            ...
            if isinstance(obj, CallBackFilter):
                return obj.json_serialize()
            ...
        """
        return {self.__class__.__name__: {k: v for k, v in self.__dict__.items() if k[:1] != '_'}}

    @classmethod
    def json_deserialize(cls, data_dict):
        """
        Creates obj and updates state.
        Add the following lines to decode a loaded object instance from native json.load to CallBackFilter
            ...
            if isinstance(x, dict):
                key, value = next(iter(x.items()))
                cbf_class = globals()[key]
                return cbf_class.json_deserialize(value)
            ...
        """
        obj = cls()  # create object
        obj.__dict__.update(data_dict)  # update native json objects
        return obj


class StateChangedFilter(CallBackFilter):
    """
    StateChangeFilter: Returns None (i.e. no callback) if stade did not change
    equals the default StreamDeck behavior
    """
    @manage_states  # register states, time and delay
    def map_states(self, new_state):
        # only return on state change
        return new_state if self._last_key_state != new_state else None


class DebounceFilter(CallBackFilter):
    """
    DebounceFilter: Returns None (i.e. no callback) if stade did not change
    or did already change within the last self.key_delay seconds
    - prevents chattering of keys.
    """
    def __init__(self, default_state=False, key_delay=0.003):
        self.key_delay = key_delay
        CallBackFilter.__init__(self, default_state)

    @manage_states
    def map_states(self, new_state):
        # only return on state change and if delay since last callbak >= key delay
        return new_state if self._last_key_state != new_state and self._delay >= self.key_delay else None


class TempoFilter(DebounceFilter):
    """
    TempoFilter: returns
    - True if key is pressed for less than tempo_delay seconds
    - False if key is pressed for more than tempo_delay seconds
    - None if key pressed for less than key_delay seconds or state did not change
    Note: In tempo mode callbacks are fired at key release time
        i.e. it results in lag/latency and is not suitable gaming keys
        like W,A,S,D, etc.
    """

    def __init__(self, default_state=False, key_delay=0.003, tempo_delay=0.3):
        self.tempo_delay = tempo_delay
        DebounceFilter.__init__(self, default_state)

    @manage_states
    def map_states(self, new_state):
        rv = None
        if self._last_key_state != new_state and self._delay >= self.key_delay:
            self._last_key_time = time()  # we always need to register last state change and time
            self._last_key_state = new_state
            if new_state is False:        # but only return a callback on key release
                rv = True if self._delay < self.tempo_delay else False
        return rv
