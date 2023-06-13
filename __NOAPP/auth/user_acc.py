from fastapi import APIRouter, HTTPException, status, Header, Request
from typing import Optional, Annotated
from _neo4j.neo4j_operations import login_validate_user_pass_trx, user_change_password
from _neo4j import appNeo, session, log, user

from pydantic import BaseModel
import jwt
import json

router = APIRouter()

#def login_user(user, keypass, User_Agent: Annotated[str | None, Header()] = None, userId: Annotated[str | None, Header()] = None):
@router.get("/login/{user} {keypass}")   # {user} {keypass}
def login_user(user, keypass):
    global session
 
    result = login_validate_user_pass_trx(session, user, keypass)
    if len(result) == 0:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password - us', "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": "",

                }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif keypass == result["us.keypass"]:
        resp_dict ={'status': 'OK', 
                    'text': 'successful access', 
                    "username": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.nativeLang"]
                }
    else:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password', "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            #headers={"WWW-Authenticate": "Basic"},
        )
    return resp_dict

@router.post("/change_pass/{userId} {oldkeypass} {newkeypass}")
def user_change_pass(userId, oldkeypass, newkeypass):
    global session
    nodes = user_change_password(session, userId, oldkeypass, newkeypass)
    if len(nodes) == 0:        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            #headers={"WWW-Authenticate": "Basic"},
        )
    #print(f'nodes {nodes}')
    return {'message': "password updated"}



"""
class Items(BaseModel):
    userId : str
    name : str



@router.post("/loginNOusarjs/")
def login_userNOusarjs(items:Items):
    req_info = items

    resp_dict = {
        "status" : "SUCCESS",
        "data" : req_info
    }
    return resp_dict

@router.get("/loginNOusarjs2/")
def login_userNOusarjs2(userId:str, passw:str):

    resp_dict = {
        "status" : "SUCCESS",
        "data" : userId,
        "pass" : passw
    }
    return resp_dict

    
#def login_user(user, keypass, User_Agent: Annotated[str | None, Header()] = None, userId: Annotated[str | None, Header()] = None):
@router.get("/login_NOUSAR/{user} {keypass}")
def login_user_NOUSAR(user, keypass, User_Agent: Annotated[str, Header()]=None, userId: Annotated[str, Header()]=None):
    global session

    print(f'userId: {userId} trx_header: {User_Agent}  Header: {Header}  {str(Header)}')
    result = login_validate_user_pass_trx(session, user, keypass)
    if len(result) == 0:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password - us', "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": "",

                }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif keypass == result["us.keypass"]:
        resp_dict ={'status': 'OK', 
                    'text': 'successful access', 
                    "username": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.nativeLang"]
                }
    else:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password', "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            #headers={"WWW-Authenticate": "Basic"},
        )
    return resp_dict
"""