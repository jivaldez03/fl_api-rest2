from fastapi import APIRouter
from _neo4j.neo4j_operations import login_validate_user_pass_trx
from _neo4j import appNeo, session, log

router = APIRouter()

@router.get("/login/{user} {keypass}")
def login_user(user, keypass):
    result = login_validate_user_pass_trx(session, user, keypass)
    if len(result) == 0:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password - us'}
    elif keypass == result["us.keypass"]:
        resp_dict ={'status': 'OK', 'text': 'successful access'}
    else:
        resp_dict ={'status': 'ERROR', 'text': 'invalid user or password'}
    return resp_dict


@router.post("/change_pass/{user} {oldkeypass} {newkeypass}")
def login_user(user, oldkeypass, newkeypass):
    resp_dict ={'status': 'OK', 'text': 'password has been updated'}
    return resp_dict