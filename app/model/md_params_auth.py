from pydantic import BaseModel
from typing import Optional


class ForSignUp(BaseModel):
    userId  : str
    password: str
    name    : str
    email   : str
    lang    : str


class ForLogin(BaseModel):
    userId: str
    password: str

class ForChangePass(BaseModel):
    oldkeypass:str
    newkeypass:str
    
class ForResetPass(BaseModel):
    userId:str=None
    user_email:str

class ForUserReg(BaseModel):
    userId:str
    orgId: str
    name: str
    email:str
    email_alt:str=None
    native_lang:str=None
    selected_lang:str=None
    country_birth: str=None
    country_res: str=None
    kolic : str=None
    

class ForLicense(BaseModel):
    userId:str
    KoLic: str
    price_complete: float
    price_cupon : float
    cupon: str

"""    
us.userId as userId \n" + \
                        ", us.name as name \n" + \
                        ", us.birth_year as birth_year, us.month_year as month_year \n" + \
                        ", us.country_birth as country_birth, us.country_res as country_res \n" + \
                        ", us.native_lang as native_lang \n" + \
                        ", us.selected_lang as selected_lang \n" + \
                        ", toString(us.ctInsert) as us_ctInsert \n" + \
                        ", us.email as usemail, us.defaultCap as capacity \n" + \
                        ", rep.contactId as contactId \n" + \
                        ", rep.name as contactName \n" + \
                        ", rep.phone as contactPhone \n" + \
                        ", rep.email as contactEmail \n" 
"""