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
    level: str 
    clicksQty: int
    cardsQty: int 

