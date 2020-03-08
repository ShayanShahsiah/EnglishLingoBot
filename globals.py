from history_handler import HistoryHandler
from lessons import Lessons
from definitions import Definitions
"""
Some variables are global across all files. 
This module makes sure they are declared only once
"""
history: HistoryHandler
lessons: Lessons
defs: Definitions
def  init():
    global history
    global lessons
    global defs
    lessons = Lessons()
    defs = Definitions()
    history = HistoryHandler()