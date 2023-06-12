from fastapi import APIRouter, HTTPException, status, Header #, Request, Body
from typing import Optional #, Annotated
from _neo4j.neo4j_operations import login_validate_user_pass_trx, user_change_password, neo4_log, q01
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname

from datetime import datetime as dt

#models:
from app.model.md_params_auth import ForLogin, ForChangePass


router = APIRouter()
#import sys
#def callersfunctionname(  ):
#    return sys._getframe(2).f_code.co_name

#him = callersfunctionname()

#def login_user(user, keypass, User_Agent: Annotated[str | None, Header()] = None, userId: Annotated[str | None, Header()] = None):
#def login_user(datas: Annotated[forlogin, Body(embed=True)]):
@router.post("/login/")   # {user} {keypass}
def login_user(datas: ForLogin):
    """
    Function to create a new session \n

    this operation needs a input structure such as {userId, password}
    """
    global session
 
    result = login_validate_user_pass_trx(session, datas.userId) # , datas.password) 

    if len(result) == 0:
        print("no records - fname__name__and more:",__name__)
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password"
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif datas.password == result["us.keypass"]:
        #print("fname__name__and more:",__name__, myfunctionname()) #, callersfunctionname(),__file__)
        
        log = neo4_log(session, datas.userId, 'login - success access', __name__, myfunctionname())
        resp_dict ={'status': 'OK', 
                    'text': 'successful access',
                    "userId":datas.userId,
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
        return {"token": token, 
                    "user_name": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.nativeLang"]
        }
    else:
        print("pass invalid")
        log = neo4_log(session, datas.userId, 'login - invalid user or password', __name__, myfunctionname())
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password', "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        
        q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + datas.userId + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password -"
            #headers={"WWW-Authenticate": "Basic"},
        )    
    return resp_dict
#

@router.post("/change_pass/")
def user_change_pass(datas:ForChangePass, Authorization: Optional[str] = Header(None)):
    """
    Function for change the user password \n
    {
    "oldkeypass":str,
    "newkeypass":str"
    }
    """
    global session
    token=funcs.validating_token(Authorization)    

    nodes = user_change_password(session, token['userId'], datas.oldkeypass, datas.newkeypass,
                                 filename=__name__,
                                 function_name=myfunctionname())
    if len(nodes) == 0:        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
        )
    return {'message': "password updated"}

"""
@router.get("/validatetoken/")
def validate_token(Authorization: Optional[str] = Header(None)):    
    #print(f'Authorization: {Authorization}')
    #print('now:', dt.now())
    packofAutorization=funcs.validating_token(Authorization)  #jwt.endode({},'secret',algorithm="HS256") 
    #print(f"packof 02 ...: {packofAutorization}")
    return packofAutorization

@router.get("/validatetoken2/")
def validate_token2(Authorization:str):    
    print(f'Authorization: {Authorization}')
    print('now:', dt.now())
    packofAutorization=funcs.validating_token(Authorization)  #jwt.endode({},'secret',algorithm="HS256") 
    print(f"packof 02 ...: {packofAutorization}")
    return packofAutorization
"""
"""
#def login_user(user, keypass, User_Agent: Annotated[str, Header()]=None, userId: Annotated[str, Header()]=None):
#global session

#data = datas
results = datas

print(f"data: {results}, {type(results)}")
print(results.userId, results.password)

#print(f'userId: {userId} trx_header: {User_Agent}  Header: {Header}  {str(userId)}')
#print(f'Authorization: {Authorization}')

#print(f'Authorization: {Authorization["userId"]}')

#encoded_jwt=jwt.endode({},'secret',algorithm="HS256") 
#packofAutorization = jwt.decode(Authorization, 'secret', algorithms=["HS256"])
#print(f"packof...: {packofAutorization}")
#aut_js = json.loads(packofAutorization)
#print(f"userId : {packofAutorization['userId']}")
global session

result = login_validate_user_pass_trx(session, datas.userId, datas.password) #  user, keypass)
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
elif datas.password == result["us.keypass"]:
    resp_dict ={'status': 'OK', 
                'text': 'successful access', 
                "username": result["us.name"], 
                "age":0, 
                "country_birth": result["us.country_birth"], 
                "country_res": result["us.country_res"],
                "native_lang" : result["us.nativeLang"]
            }
    token = funcs.return_token(data=resp_dict)

    #print(f"validating token: {funcs.validating_token(token.split(' ')[1], False)}")
    return token

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