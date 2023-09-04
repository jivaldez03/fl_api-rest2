from pydantic import BaseModel
from typing import Optional
from datetime import datetime as dt

class ForPackages(BaseModel):
    idScat: int
    package: str
    capacity:int

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


class ForGames_puzzle(BaseModel):
    org: str    #"DTL-01"
    ulevel:str      # A1,A2,B1,B2,C
    kog: str        # "puzzlewords"
    hms: int        # how many sentences
    words: str      # "['abc','cde','fgh']"
    avg: float      # avg result - post exercise
    setlevel: bool       # save or not

class ForLevelEval(BaseModel):
    orgId   : str
    starton : int
    limit   : int
    word    : str
    setlevel: bool


class ForAskSupport(BaseModel):
    classification  : str
    subject         : str
    longdescription : str
