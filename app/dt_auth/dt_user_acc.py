from fastapi import APIRouter, HTTPException, status, Header #, Request, Body
from typing import Optional #, Annotated
from _neo4j.neo4j_operations import neo4j_exec 
                    #,  login_validate_user_pass_trx, \
                    # user_change_password, neo4_log, q01

from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, _getdatime_T

from datetime import datetime as dt

#models:
from app.model.md_params_auth import ForLogin, ForChangePass, ForUserReg

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
 
    neo4j_statement = "with '" + datas.userId.lower() +  "' as userId \n" + \
                "match (us:User {userId: userId }) " +  \
                "return us.userId, us.name, us.keypass, us.age, \n" + \
                    "us.native_lang, us.selected_lang, us.country_birth, us.country_res limit 1"
    nodes, log = neo4j_exec(session, datas.userId.lower(),
                        log_description="validate login user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    
    result = {}
    for elem in nodes:
        result=dict(elem) #print(f"elem: {type(elem)} {elem}")   
    #result = login_validate_user_pass_trx(session, datas.userId.lower()) # , datas.password) 
    if len(result) == 0:  # incorrect user
        print("no records - fname__name__and more:",__name__)
        #log = neo4_log(session, datas.userId, 'login - invalid user or password - us', __name__, myfunctionname())
        merror = 'Usuario-Password Incorrecto / Invalid User-Password'
        resp_dict ={'status': 'ERROR', 'text': merror, "userId":"",  "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }        
        
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = '" + merror + "' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description=merror
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)
        
        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=merror
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif datas.password == result["us.keypass"]:   # success access
        #log = neo4_log(session, datas.userId.lower(), 'login - success access', __name__, myfunctionname())
        resp_dict ={'status': 'OK', 
                    'text': 'successful access',
                    "userId":datas.userId.lower(),
                    "username": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.native_lang"],
                    "selected_lang" : result["us.selected_lang"]
                }
        print("resp_dict:", resp_dict)
        
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'login - success access' \n" + \
                    "return count(l)"
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description="validate login user"
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)

        token = funcs.return_token(data=resp_dict)
        return {"token": token, 
                    "user_name": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.native_lang"],
                    "selected_lang" : result["us.selected_lang"]
        }
    else: # incorrect pass
        #log = neo4_log(session, datas.userId.lower(), 'login - invalid user or password', __name__, myfunctionname())
        if result["us.selected_lang"] == 'Es':
            merror = "Usuario-Password Incorrecto"
        else:
            merror = "Invalid User-Password"
        resp_dict ={'status': 'ERROR', 'text': merror, "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'invalid user or password - (p)' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description=merror
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)        

        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail =merror
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

    neo4j_statement = "match (us:User {userId:'" + token['userId'] + "', \n" + \
                    "keypass:'" + datas.oldkeypass + "'}) \n" +  \
                    "set us.keypass = '" + datas.newkeypass + "' \n" + \
                    "return us.userId, us.keypass limit 1"

    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="update password",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    """nodes = user_change_password(session, token['userId'].lower(), datas.oldkeypass, datas.newkeypass,
                                 filename=__name__,
                                 function_name=myfunctionname())"""
    
    result = {}
    for elem in nodes:
        result=dict(elem)

    if len(result) == 0:
        #print("id: ", token['userId'], " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raiseHTTP - user / pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
        )
    else: # update pass was done
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + token['userId'] + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'updated password' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, token['userId'],
                        log_description="updating password"
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': "password updated"}


@router.post("/userreg/")
async def user_registry(datas:ForUserReg, Authorization: Optional[str] = Header(None)):
    """
    Function for change the user password \n
    {
    userId:str
    orgId:str
    name: str
    email:str
    email_alt:str
    native_lang:str
    selected_lang:str
    country_birth: str
    country_res: str
    koflic
    }
    """
    global session
    token=funcs.validating_token(Authorization)
    orgId = "DTL-01"

    dname = datas.name if not isinstance(datas.name, type(None)) else datas.userId
    demail = datas.email if not isinstance(datas.email, type(None)) else '__'
    demail_alt = datas.email_alt if not isinstance(datas.email_alt, type(None)) else 'null'
    dnative_lang = datas.native_lang if not isinstance(datas.native_lang, type(None)) else 'Español'
    dselected_lang = datas.selected_lang if not isinstance(datas.selected_lang, type(None)) else 'Sp'
    dcountry_birth = datas.country_birth if not isinstance(datas.country_birth, type(None)) else 'null'
    dcountry_res = datas.country_res if not isinstance(datas.country_res, type(None)) else 'null'
    dkol = datas.kolic if not isinstance(datas.kolic, type(None)) else 'UNIVERSAL'

    neo4j_statement = "merge (us:User {userId:'" + datas.userId + "'}) \n" + \
                    " on match set us.ctUpdate = datetime()  \n" + \
                    " on create set us.ctInsert = datetime(), us.keypass='"+ datas.userId+"' \n" + \
                    "set us.name = '" + dname + "', \n" + \
                    "  us.email = '" + demail + "', \n" + \
                    "  us.email_alt = '" + demail_alt + "', \n" + \
                    "  us.native_lang = '" + dnative_lang + "', \n" + \
                    "  us.selected_lang = '" + dselected_lang + "', \n" + \
                    "  us.country_birth = '" + dcountry_birth + "', \n" + \
                    "  us.country_res = '" + dcountry_res + "', \n" + \
                    "  us.kol = '" + dkol + "', \n" + \
                    "  us.ctUpdate = datetime() \n" + \
                    "with us \n" + \
                    "match (o:Organization {idOrg:'" + orgId + "'})" + \
                    "merge (o)<-[rou:RIGHTS_TO]-(us) \n" + \
                    " on match set rou.ctUpdate = datetime()  \n" + \
                    " on create set rou.ctInsert = datetime() \n" + \
                    "return us.userId, us.name, us.native_lang, us.selected_lang, us.kol limit 1"

    #print("neo4j:", neo4j_statement)
    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="update user configure id",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
        
    result = {}
    for elem in nodes:
        result=dict(elem)
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


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

