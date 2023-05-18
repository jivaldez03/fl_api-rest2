from datetime import datetime as dt
from time import sleep as sleep
from random import randint

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
