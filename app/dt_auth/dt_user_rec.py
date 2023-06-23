from typing import Union
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Request

from app.model.md_params_auth import ForResetPass
from fastapi import APIRouter

from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user

from __generalFunctions import myfunctionname

import random
from string import ascii_letters

#from dotenv import load_dotenv
from os import getenv

router = APIRouter()


def get_random_string(length):
    # choose from all lowercase letter
    letters = ascii_letters # string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)
    return result_str


def email_send(target_userId, target_email, message):
    edom = "delthatech"
    #email_pass = "Delthatech_2023"

    email_ad = "dtl@" +  edom + "." + "com"
    email_ps = edom.title()  + "_2023"
    #print ("_____________", email_ad, email_ps)
    ##email_ad = getenv("email_address")
    #email_ps = getenv("email_pass")

    #get_random_string(8)

    # imap.secureserver.net
    #dtl@delthatech.com - Delthatech_2023  
    # (esta cuenta de email es del hosting de godaddy)

    #print("email hosted by: ", email_ad, email_ps)

    msg = EmailMessage()
    msg["Subject"] = "Password reset"
    msg["From"] = email_ad
    msg["To"] = target_email
    #print("tempasssss: ", message)
    msg.set_content(message)

    outgoingsemails="smtpout.secureserver.net" # imap.secureserver.net
    outgoingsport = 465 # 993
    with smtplib.SMTP_SSL(host=outgoingsemails, port=outgoingsport) as smtp:
        smtp.login(email_ad, email_ps)
        smtp.send_message(msg)
    return "email has been sent to " + target_userId


@router.post("/reset_pass_notification/")
def user_change_pass_notification(datas:ForResetPass):
    """
    Function for reset the user password \n
    {
    "userId":str,
    "user_email":str"
    }
    """
    userId = datas.userId
    useremail = datas.user_email

    temppass = get_random_string(random.randint(30,50))

    neo4j_statement = "match (u:User {email:'" + useremail + "'}) \n" + \
                    "set u.temp_access = '" + temppass + "', \n" + \
                    "u.temp_access_dt = datetime() \n" + \
                    "return u.userId, u.email limit 1"
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="sending reset password notification",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    sdict = {}
    for node in nodes:
        sdict = dict(node)
    emailuser = sdict.get("u.email", "")
    userIdtoChange = sdict.get("u.userId", "")

    if datas.user_email == emailuser:
        msg = "Este mensaje (es válido por 10 minutos) fue a solicitud expresa del usuario en DTL, " + \
            "al dar click al siguiente link su password seŕa renovado, y " + \
            "recibirá un nuevo correo electrónico con instrucciones de acceso " + \
            "- http://localhost:3000/dt/auth/reset_pass/" + temppass

        sentmail = email_send(userId, datas.user_email, msg)
    else:
        sentmail = "email has been sent to " + userId

    #print("ssssssentmail", sentmail)
    return sentmail


@router.get("/reset_pass/{code}")
def user_change_pass(code:str):
    """
    Function for reset the user password \n
    {
    "code":str
    }
    """
    temppass = get_random_string(random.randint(8, 12))

    neo4j_statement = "match (u:User {temp_access:'" + code + "'}) \n" + \
                    "where (u.temp_access_dt + duration({minutes: 10})) >=  datetime() \n" + \
                    "set u.keypass = '" + temppass + "', u.ctUpdate = datetime() \n" + \
                    "return u.userId, u.email"
    
    nodes, log = neo4j_exec(session, 'admin', 
                        log_description="reset password notification",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    sdict = {}
    for node in nodes:
        sdict = dict(node)    
    
    userId = sdict.get("u.userId", "")
    emailuser = sdict.get("u.email", "")
    
    if emailuser != "":
        msg = "Su password ha sido renovado, nuevo password: "+ temppass
        sentmail = email_send(userId, emailuser, msg)
    else:
        sentmail = "something was wrong"
    #print("ssssssentmail to user", userId, emailuser, sentmail)
    return sentmail
