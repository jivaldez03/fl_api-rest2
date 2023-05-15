from fastapi import APIRouter

router = APIRouter()

@router.get("/login/{user} {keypass}")
def login_user(user, keypass):
    resp_dict ={'status': 'OK', 'text': 'successful access'}
    return resp_dict


@router.get("/change_pass/{user} {oldkeypass} {newkeypass}")
def login_user(user, oldkeypass, newkeypass):
    resp_dict ={'status': 'OK', 'text': 'password has been updated'}
    return resp_dict