from pydantic import BaseModel
from typing import Optional
from datetime import datetime as dt

class ForPackages(BaseModel):
    idScat: int
    package: str=None
    capacity:int=None

class ForClosePackages(BaseModel):
    package: str=None
    updtime: str=str(dt.now()).replace(' ','T')
    level: str = None
    clicksQty: int
    cardsQty: int 

 
class ForNamePackages(BaseModel):
    package: str=None
    label: str = None

class ForGames_KOW(BaseModel):
    orgId: str
    limit: int
    subcat:int
    adj: bool
    verb: bool
    pt_verb: bool
    noun: bool
    adj : bool
    adv : bool
    prep : bool

class ForGames_archive(BaseModel):
    orgId: str
    subcat:int
    words  : str
    average: float
    kogame : str
