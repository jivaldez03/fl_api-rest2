from pydantic import BaseModel
from typing import Optional

class Book(BaseModel):
    title: str
    author: str
    pages: int
    editorial: Optional[str]



