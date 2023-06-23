from pydantic import BaseModel
from typing import Optional

class ForLogin(BaseModel):
    userId: str
    password: str

class ForChangePass(BaseModel):
    oldkeypass:str
    newkeypass:str
    
class ForResetPass(BaseModel):
    userId:str
    user_email:str