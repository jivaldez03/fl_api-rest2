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

class ForUserReg(BaseModel):
    userId:str
    email:str
    name: str
    native_lang:str
    selected_lang:str
    country_birth: str
    country_res: str
    


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