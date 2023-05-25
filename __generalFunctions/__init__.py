from datetime import datetime as dt
from time import sleep as sleep
from random import randint
from re import compile, match

def _getdatime():
    return str(dt.now())

def _getdatime_T():
    return str(dt.now()).replace(' ','T')

def _sleep(secs, init_range=0, end_range=10):
    if secs:
        pass
    else:
        secs = randint(init_range, end_range)
    sleep(secs)
    return secs

def get_list_element(l_elements:list, index:int):
    if len(l_elements) <= index:
        return None
    else:
        return l_elements[index]
    
def reg_exp(exp_to_evaluate, text_to_check):
    rege = compile(exp_to_evaluate)

    if rege.match(text_to_check):
        return True
    else:
        return False
    