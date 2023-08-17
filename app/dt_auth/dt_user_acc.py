from fastapi import APIRouter, HTTPException, status, Header #, Request, Body
from typing import Optional #, Annotated
from _neo4j.neo4j_operations import login_validate_user_pass_trx, \
                    user_change_password, neo4_log, neo4j_exec, \
                    q01
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, _getdatime_T

from datetime import datetime as dt

#models:
from app.model.md_params_auth import ForLogin, ForChangePass

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

router = APIRouter()
#import sys
#def callersfunctionname(  ):
#    return sys._getframe(2).f_code.co_name

#him = callersfunctionname()

#def login_user(user, keypass, User_Agent: Annotated[str | None, Header()] = None, userId: Annotated[str | None, Header()] = None):
#def login_user(datas: Annotated[forlogin, Body(embed=True)]):
@router.post("/login/")   # {user} {keypass}
async def login_user(datas: ForLogin):
    """
    Function to create a new session \n

    this operation needs a input structure such as {userId, password}
    """
    global session
 
    result = login_validate_user_pass_trx(session, datas.userId.lower()) # , datas.password) 

    detailmessage = ""
    messageforuser = ""
    
    if len(result) == 0:
        #print("no records - fname__name__and more:",__name__)
        log = neo4_log(session, datas.userId, 'login - invalid user or password - us', __name__, myfunctionname())
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password - us', "userId":"",  "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }        
        q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + datas.userId + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        )
        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect User or Password"
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif datas.password == result["us.keypass"]:
        #print("fname__name__and more:",__name__, myfunctionname()) #, callersfunctionname(),__file__)
        
        log = neo4_log(session, datas.userId.lower(), 'login - success access', __name__, myfunctionname())
        resp_dict ={'status': 'OK', 
                    'text': 'successful access',
                    "userId":datas.userId.lower(),
                    "username": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.nativeLang"]
                }
        q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + datas.userId + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        )
        token = funcs.return_token(data=resp_dict)

        #print(f"validating token: {funcs.validating_token(token.split(' ')[1], False)}")
        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
        return {"token": token, 
                    "user_name": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.nativeLang"]
        }
    else:
        # print("pass invalid")
        log = neo4_log(session, datas.userId.lower(), 'login - invalid user or password', __name__, myfunctionname())
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password', "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        
        q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + datas.userId.lower() + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        )
        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail ="Incorrect User or Password"
            #headers={"WWW-Authenticate": "Basic"},
        )
    print("id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return resp_dict
#

@router.post("/change_pass/")
async def user_change_pass(datas:ForChangePass, Authorization: Optional[str] = Header(None)):
    """
    Function for change the user password \n
    {
    "oldkeypass":str,
    "newkeypass":str"
    }
    """
    global session
    token=funcs.validating_token(Authorization)    

    nodes = user_change_password(session, token['userId'].lower(), datas.oldkeypass, datas.newkeypass,
                                 filename=__name__,
                                 function_name=myfunctionname())
    if len(nodes) == 0:
        #print("id: ", token['userId'], " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raiseHTTP - user / pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
        )
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': "password updated"}

@router.get("/org/")
async def get_org(Authorization: Optional[str] = Header(None)):
    """
    Function to get all categories and subcategories allowed for the user

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
        
    neo4j_statement = "with '" + userId + "' as userId " + \
                        "match (u:User {userId:userId})-[:RIGHTS_TO]->(o:Organization) \n" + \
                        "return o.idOrg as idOrg, o.name as name, o.lSource as Source, o.lTarget as Target"
    
    #print('cats-subcats:', neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)
        ndic = {'orgId': sdict["idOrg"], 'OrgName': sdict["name"]
                , 'source' : sdict["Source"], 'target': sdict["Target"]}
        listcat.append(ndic)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat

