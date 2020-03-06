from history_handler import HistoryHandler
"""
Some variables are global across all files. 
This module makes sure they are declared only once
"""
def  init():
    global history
    history = HistoryHandler()