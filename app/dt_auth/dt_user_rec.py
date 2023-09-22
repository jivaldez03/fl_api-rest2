#from typing import Union
#import smtplib
#from email.message import EmailMessage
import stripe
from fastapi import Request, APIRouter # FastAPI, 

from app.model.md_params_auth import ForResetPass, ForLicense

from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session

from __generalFunctions import myfunctionname, get_random_string, email_send

import random
from string import ascii_letters

from asyncio import sleep as awsleep

router = APIRouter()

def get_random_string_borrar(length):
    # choose from all lowercase letter
    letters = ascii_letters # string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)
    return result_str

"""
def email_send(target_userId, target_email, message):
    edom = "delthatech"
    #email_pass = "Delthatech_2023"

    email_ad = "dtl@" +  edom + "." + "com"
    email_ps = edom.title()  + "_23"

    if target_email == None:
        target_email = 'dtl@delthatech.com'
        
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
"""

@router.post("/reset_pass_notification/")
async def user_change_pass_notification(datas:ForResetPass, request:Request):
    global appNeo
    """
    Function for reset the user password \n
    {
    "userId":str,
    "user_email":str"
    }
    """
    def get_path():
        met  =  request.scope['method'] 
        path =  request.scope['root_path'] + request.scope['route'].path
        #encoding = 'utf-8'
        serverlnk = ""
        for elehead in request.scope['headers']:
            #print('eeeelehead:', elehead, type(elehead))
            val=str(elehead[0],'utf-8')
            if val == 'host':
                serverlnk = str(elehead[1], 'utf-8')
        #print(str(request.scope['headers'])) # , 'utf-8')

        #print('eeeelehead severlink:', serverlnk)
        #serverlnk = str(request.scope['headers'][0][1], 'utf-8')        
        return met, path, serverlnk
    
    userId = datas.userId
    useremail = datas.user_email

    temppass = get_random_string(random.randint(30,50))

    method, pathcomplete, serverlnk = get_path()    

    #print("mmmethod:", method)
    #print("pathcomplete:", pathcomplete)
    #print("serverlnk:", serverlnk)
    awsleep(0)

    lnk_toanswer = "http://" + serverlnk + "/dt/auth/reset_pass/"
    
    neo4j_statement = "match (u:User {email:'" + useremail + "'}) \n" + \
                    "set u.temp_access = '" + temppass + "', \n" + \
                    "u.temp_access_dt = datetime() \n" + \
                    "return u.userId, u.email, u.selected_lang as selected_lang limit 1"
    
    #print("nneo4j: ", neo4j_statement)

    nodes, log = neo4j_exec(session, userId,
                        log_description="sending reset password notification",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    sdict = {}
    #lnk_toanswer 
    for node in nodes:
        sdict = dict(node)
    emailuser = sdict.get("u.email", "")
    userIdtoChange = sdict.get("u.userId", "")
    #print("\n\nnneo4j despude de ejecución: - solo FALTA ENVIAR MAIL")

    if datas.user_email == emailuser:
        if sdict["selected_lang"] == 'es':
            msg = "Este mensaje (es válido por 10 minutos) fue a solicitud expresa del usuario en DTone, " + \
                "al dar click al siguiente link su password seŕa renovado, y " + \
                "recibirá un nuevo correo electrónico con instrucciones de acceso \n\n " + \
                lnk_toanswer + temppass +  " \n\n" + \
                "Esta notificación no requiere respuesta."
            subj = "DTone - Notificación de Solicitud de Cambio de Password"
        else:
            msg = "This message (valid for 10 minutes) was at the express request of the user in DTOne, " + \
                "by clicking the following link your password will be renewed, and " + \
                "you will receive a new email with access instructions \n\n " + \
                lnk_toanswer + temppass +  " \n\n" + \
                "This notification does not require a response."          
            subj = "DTone - Notification of Renewed Password Request"

        sentmail = email_send(userId, datas.user_email, msg, subj, appNeo)
        refmail = datas.user_email.split('@')
        sentmail = sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ")"
    else:
        sentmail = "email has been sent to " + userId

    return sentmail


@router.get("/reset_pass/{code}")
async def user_change_pass(code:str):
    global appNeo
    """
    Function for reset the user password \n
    {
    "code":str
    }
    """
    temppass = get_random_string(random.randint(8, 12))

    neo4j_statement = "match (u:User {temp_access:'" + code + "'}) \n" + \
                    "where (u.temp_access_dt + duration({minutes: 10})) >=  datetime() \n" + \
                    "set u.keypass = '" + temppass + "', \n" + \
                        "u.temp_access = reverse(u.temp_access), \n" + \
                        "u.ctUpdate = datetime() \n" + \
                    "return u.userId, u.email, u.selected_lang as selected_lang"
    
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
    
    awsleep(0)

    if emailuser != "":
        if sdict["selected_lang"] == 'es':
            msg = "Su password ha sido renovado, su nuevo password es: " + temppass
            subj = "DTone - Notificación de Modificación de Password"
        else:
            msg = "Password has been updated, your new password is: " + temppass
            subj = "DTone - Notification of Password Updated"        
        sentmail = email_send(userId, emailuser, msg, subj, appNeo)
        refmail = emailuser.split('@')
        sentmail = sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ")"
    else:
        sentmail = "Something was wrong, review your email."
    
    return sentmail


@router.get("/s_pay_validation/{code}")
async def s_pay_validation(code:str):
    """
    class ForLogin(BaseModel):
        userId: str
        KoLic: str
    """
    send = "processing pay with code:" + code + " ... wait a minute please..."
    awsleep(3)
    return send

@router.post("/stripe_checkout/")
async def stripe_checkout(datas:ForLicense, request:Request):
    """
    class ForLogin(BaseModel):
        userId: str
        KoLic: str
        price_complete: float
        price_cupon : float
        cupon: str
    """

    def get_path():
        met  =  request.scope['method'] 
        path =  request.scope['root_path'] + request.scope['route'].path
        #encoding = 'utf-8'
        serverlnk = ""
        for elehead in request.scope['headers']:
            #print('eeeelehead:', elehead, type(elehead))
            val=str(elehead[0],'utf-8')
            if val == 'host':
                serverlnk = str(elehead[1], 'utf-8')  
        return met, path, serverlnk
    
    userId = datas.userId

    temppass = get_random_string(random.randint(45,60))

    method, pathcomplete, serverlnk = get_path()    

    lnk_toanswer = "https://" + serverlnk + "/dt/auth/s_pay_validation/" + temppass

    # Set your secret key. Remember to switch to your live secret key in pr
    # oduction.   
    # See your keys here: https://dashboard.stripe.com/apikeys
    stripe.api_key = "sk_test_51NmjkxL7SwRlW9BCVBKVANME2kkwita0vUn4adcey8Tu3MpC9RtOg3dLdvDM6sFCzIS08MaZzuTw7B3nOwE8FKMV00e5mQH9BE"
    #stripeLink = {"url":lnk_toanswer}    
    #"""
    stripeLink = stripe.PaymentLink.create(
            #line_items=[{"price": '{{25.99}}', "quantity": 1}],
            line_items=[{"price": 'price_1NtD1qL7SwRlW9BCB8ABhCH0', "quantity": 1}],
            after_completion={"type": "redirect", "redirect": {"url": lnk_toanswer}},
             allow_promotion_codes=True, 
             #automatic_tax={"enabled": True},
            # "https://www.delthatech.com"
    )
    #"""
    awsleep(0)
    #            after_completion={"type": "redirect", "redirect": {"url": "https://www.delthatech.com"}},
    """
    custom_fields=[
                    {
                    "key": "datas.userId",
                    "label": {"type": "license", "custom": str(_getdatetime())},
                    "type": "license XYZ"
                },
            ]
    """
    print("*************************\nStripeLink: ", stripeLink, "\n", stripeLink["url"])
    return {"stripe_url":stripeLink["url"], "redirect_url": lnk_toanswer, "stripe_completeseq": stripeLink}
