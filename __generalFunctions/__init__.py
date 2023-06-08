from datetime import datetime as dt, timedelta
from time import sleep as sleep
from random import randint
from re import compile, match

from jwt import encode, decode
#import jwt
from jwt import DecodeError, ExpiredSignatureError
from flask import jsonify
from dotenv import load_dotenv
from os import getenv
from fastapi import HTTPException, status

load_dotenv()

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
    
def expiration_datetime(mins:int=30):
    dtexp = dt.utcnow() + timedelta(minutes=mins)
    #print('expirationdate: ', dtexp)
    return dtexp

def return_token(data:dict, mins_for_expiration_token:int=int(getenv("MINS_FOR_TOKEN_EXPIRATION"))):
    #print('getenv', getenv("SEC_KEY")) # getenv("SEC_KEY") 
    #token = encode(payload={**data, "exp":expiration_datetime(mins_for_expiration_token)}, key=getenv("SEC_KEY"), algorithm="HS256")
    #, "exp": dt.now() + timedelta(minutes=mins_for_expiration_token) datetime.utcnow()
    print("mins_for_expiration_token: ", mins_for_expiration_token)
    token = encode(payload={**data, "exp": expiration_datetime(mins_for_expiration_token)}
                   , key=getenv("SEC_KEY"), algorithm="HS256")
    #print("new token:", token)
    return token # .encode("UTF-8")

def validating_token(token):
    try:
        #print(f'getenv: {getenv("SEC_KEY")}, {token}')                
        return decode(token, key=getenv("SEC_KEY"), algorithms=["HS256"])
    except DecodeError:
        print("error por token decodeerror")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            #headers={"WWW-Authenticate": "Basic"},
        )
    except ExpiredSignatureError:
        print("error por token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired - Invalid Token"
        )

def level_seq(level, forward=False, position=False):
    llevel = (getenv("LEVEL_SEQUENCE")).split(',')    
    if llevel.__contains__(level):
        ix = llevel.index(level)
        if position:
            return ix
        elif forward:
            return(llevel[ix+1])
        else:            
            return(llevel[ix-1])
    return level
    




