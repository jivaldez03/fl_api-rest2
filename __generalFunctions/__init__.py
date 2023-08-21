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
from fastapi import HTTPException, status #, Request

import smtplib
from email.message import EmailMessage

import inspect
myfunctionname = lambda: str(inspect.stack()[1][3])

load_dotenv()

myConjutationLink = lambda verb, lang: (getenv("CONJUGATION_VERBS_LINK")) + verb if lang == 'English' else 'https://www.ingles.com/verbos/' + verb


def _getdatetime():
    return dt.now()


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

def get_list_elements(l_elements:list, index:int):
    if len(l_elements) <= index:        
        return l_elements
    else:
        return l_elements[:index]
    
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
        print("====> TOKEN DECODE ERROR")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="====> INVALID TOKEN",
            #headers={"WWW-Authenticate": "Basic"},
        )
    except ExpiredSignatureError:
        print("====> EXPIRED TOKEN ERROR")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="====> EXPIRED TOKEN ERROR"
        )

def level_seq(level, forward=False, position=False):
    """
    forward = True, return the next level,
    forward = False, return the previous level
    position = True, return the position of the level into the sequence
    """
    llevel = (getenv("LEVEL_SEQUENCE")).split(',')   
    #print('lllleeeevel:', llevel, level, llevel.__contains__(level)
    # , 'forward: ', forward, 'position:', position) 
    if llevel[1:].__contains__(level):    # llevel[0] = None
        ix = llevel.index(level)
        #print('ixxxxxxxxxxxxxxxx:', ix)
        if position:
            return ix
        elif forward:
            return(llevel[ix+1])
        else:            
            return(llevel[ix-1])      
    elif not level:
        return llevel[0]  
    return -1
    
def validating_exist_level(level):
    levelSeqPosition = level_seq(level, forward=False, position=True)
    if levelSeqPosition > 0:
        pass
    else:
        if level == None:
            level = "None"
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,   #HTTP_401_UNAUTHORIZED,
            detail="level (" + level + ") is a wrong format or data"            
            #headers={"WWW-Authenticate": "Basic"},
        )
    return levelSeqPosition

def monitoring_function(functiontovalidate):
    """
    
    """
    #print("log-active:", getenv('LOG_ACTIVE'), type(getenv('LOG_ACTIVE')) )
    if getenv('LOG_ACTIVE') == 'True':
        lfunctions = (getenv("MONITORING_FUNCTIONS")).split(',\n')    
        #print('functionsvalidate: ', functiontovalidate, lfunctions, type(functiontovalidate))
        # if lfunctions.__contains__(functiontovalidate):

        if functiontovalidate in lfunctions:
            return True
        else:
            return False
    else:
        return False


def _getenv_function(env_variable):
    """
    
    """
    return getenv(env_variable)



def email_send(target_userId, target_email, message, subject):
    edom = "delthatech"
    #email_pass = "Delthatech_2023"

    email_ad = "dtl@" +  edom + "." + "com"
    email_ps = edom.title()  + "_2023"

    if target_email == None:
        target_email = 'dtl@delthatech.com'
        
    #print ("_____________", email_ad, email_ps)
    ##email_ad = getenv("email_address")
    #email_ps = getenv("email_pass")

    #get_random_string(8)

    # imap.secureserver.net
    #dtl@delthatech.com - Delthatech_2023  
    # (esta cuenta de email es del hosting de godaddy)

    #print("email hosted by: ", email_ad, email_ps)

    msg = EmailMessage()
    if subject == None:
        msg["Subject"] = "Password reset"
    else:
        msg["Subject"] = subject

    msg["From"] = email_ad
    msg["To"] = target_email
    #print("tempasssss: ", message)
    msg.set_content(message)
    msg_error = ""
    #"""
    try:
        outgoingsemails="smtpout.secureserver.net" # imap.secureserver.net
        outgoingsport = 465
        with smtplib.SMTP_SSL(host=outgoingsemails, port=outgoingsport) as smtp:
            smtp.login(email_ad, email_ps)
            smtp.send_message(msg)
    except Exception as error:
        print('message error sending smtp mail: ', type(error).__name__, error)
        msg_error = f"execption error: {type(error).__name__} - {error}"
        return "False"    
    #"""    
    return "email has been sent to " + target_userId +  msg_error

