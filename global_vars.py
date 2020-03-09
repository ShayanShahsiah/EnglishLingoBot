import history_handler as hh
from definitions import Definitions
"""
Some variables are global across all files. 
This module makes sure they are declared only once
"""
history: hh.HistoryHandler
defs: Definitions
def  init():
    global history
    global defs
    defs = Definitions()
    history = hh.HistoryHandler()