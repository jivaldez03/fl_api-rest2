#from typing import Union
#import smtplib
#from email.message import EmailMessage
import stripe
from fastapi import Request, APIRouter, Header # FastAPI, 
from typing import Optional

from starlette.responses import RedirectResponse

from app.model.md_params_auth import ForResetPass, ForLicense

from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session
from _neo4j.config import kodb

from __generalFunctions import myfunctionname, get_random_string \
                                , email_send, validating_token, _sleep \
                                , bcrypt_pass

import random
from string import ascii_letters

from asyncio import sleep as awsleep

router = APIRouter()

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

    userId = "pub_user"

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
    newencripass=bcrypt_pass(temppass)
    newencripass=newencripass.decode('utf-8')

    neo4j_statement = "match (u:User {temp_access:'" + code + "'}) \n" + \
                    "where (u.temp_access_dt + duration({minutes: 10})) >=  datetime() \n" + \
                    "set u.keypass = '" + newencripass + "', \n" + \
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
            subj = "DTone - Notificación de Modificación de Password (usuario: " + userId + ")"
        else:
            msg = "Password has been updated, your new password is: " + temppass
            subj = "DTone - Notification of Password Updated (user: " + userId + ")"
        sentmail = email_send(userId, emailuser, msg, subj, appNeo)
        refmail = emailuser.split('@')
        sentmail = sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ")"
    else:
        sentmail = "Something was wrong, review your email."    
    return sentmail

def s_getapi():
    if kodb() == 1:
        s_api_key = appNeo.app_access_cfg.get("sk_test", "")
    elif kodb() == 2:
        s_api_key = appNeo.app_access_cfg.get("sk_live", "")
    else:
        s_api_key = 'error on s_api_key'
    s_api_key = s_api_key.replace("JAIV03","")
    return s_api_key

def s_checkout_session(cs):  # obtiene la lista de pagos procesados en stripe general o desde un punto (cs)
    stripe.api_key = s_getapi()    
    #"sk_test_51NmjkxL7SwRlW9BCVBKVANME2kkwita0vUn4adcey8Tu3MpC9RtOg3dLdvDM6sFCzIS08MaZzuTw7B3nOwE8FKMV00e5mQH9BE"
    if cs:
        resultsconfirmplink = stripe.checkout.Session.list(
                        limit=100
                        , ending_before=cs
                        ) 
    else:
        resultsconfirmplink = stripe.checkout.Session.list(
                        limit=100
                        ) 

    datas = resultsconfirmplink["data"]
    ldatas = []
    for gia, data in enumerate(datas[:]):
        if data["status"] == "complete" \
            and  data["status"] == "complete" \
            :
                for giaCF, cf in enumerate(data["custom_fields"]):
                    if cf["key"] == 'userId':
                        userIdINDAT = cf["text"]["value"].lower().strip()
                useremailINDAT = data["customer_details"]["email"].lower().strip()
                sdict = {"csId" : data["id"],
                         "userId" : userIdINDAT,
                         "email" : useremailINDAT,
                        "paym_st" : data["payment_status"],
                        "checkS" : data["status"],
                        "amount_stot" : data["amount_subtotal"],
                        "amount_total" : data["amount_total"],
                        "curr" : data["currency"],
                        "plink" : data["payment_link"],
                        "pintent" :data["payment_intent"],
                        "created" : data["created"]
                }
                ldatas.append(sdict)
    return ldatas  # resultsplink, 


def s_prices(sApiKey):
    stripe.api_key = sApiKey
    prices = stripe.Price.list(
                    limit=100
            )
    #print("\n\npricess:", prices)
    return prices

def s_products(sApiKey):
    stripe.api_key = sApiKey
    products = stripe.Product.list(
                    limit=100
                ) 
    #print("\n\nproductos:", products)
    return products

def s_paymentslink(sApiKey):  # obtiene la lista de los paymentslink en strip - solo activos
    stripe.api_key = sApiKey
    paymlinks = stripe.PaymentLink.list(
                    limit=100
                    ) 
    datas = paymlinks["data"]
    ldatas = []
    
    for gia, data in enumerate(datas[:]):
        if data["active"] == True:
            for giaCF, cf in enumerate(data["custom_fields"]):                    
                userIdINDAT = cf["key"]

            for gia, ac in enumerate(data["after_completion"]):
                #print("after_complettion:", ac)
                if ac == 'redirect':
                    redirectINDAT = data["after_completion"]["redirect"]["url"]
            
            #useremailINDAT = data["customer_details"]["email"]
            sdict = {"plId" : data["id"],
                        "url"  : data["url"],
                        "status" : True, 
                        "keyUserId" : userIdINDAT, 
                        "allow_promotion_codes" : data["allow_promotion_codes"],
                        "curr" : data["currency"] #"created" : data["created"]
            }
            ldatas.append(sdict)

    return len(paymlinks) \
            , ldatas

def search_pl_actives_plinks(pl, pl_actives):  # busca si existe pl en la lista de paymentslinks activos - true si existe
    print("\n\n******************pl:", pl, "plactives:", len(pl_actives))
    for gia, pl_ac in enumerate(pl_actives):
        if pl_ac["plId"] == pl:
            return True
    return False


#@router.get("/s_paymlink/")
#async 
def s_paymlink(): #Authorization: Optional[str] = Header(None)):
    # obtiene la lista de paymlinks activos en stripe ejecutando la función s_paymentslinks que es la que realiza
    # la conexión y lectura a stripe

    s_api_key = s_getapi()
    lenpl, paymlinks = s_paymentslink(s_api_key)

    return lenpl, paymlinks

@router.get("/s_available_products/")
async def s_available_products(Authorization: Optional[str] = Header(None)):

    #print('\n\n *********************** \nauthorization', Authorization)
    token=validating_token(Authorization)
    userId = token['userId']
    sdict = {
                "title": {
                    "es": "La vigencia de acceso ha concluído",
                    "en": "Your license period has finished"
                },
                "title02": {
                    "es": "Lo invitamos a continuar con nosotros, le ofrecemos las siguientes opciones",
                    "en": "We invite you to continue with us, you have some fantastic options"
                },
                "label01": { 
                    "es": "Productos disponibles",
                    "en": "Available products"
                },
                "Options": [ 
                    {
                    "KoLic": "01M",
                    "value": {
                        "es": "01M - 1 MES DE ACCESO",
                        "en": "01M - ACCESING FOR 1 MONTH"
                    },
                    "description": {
                        "es": "Por lanzamiento obten 50% de descuento",
                        "en": "50% Free"
                    },
                    "cupon": "RIGHTNOW",
                    "price": 60,
                    "price_cupon": 30
                    },
                    {
                    "KoLic": "03M",
                    "value": {
                        "es": "03M - 3 MESES DE ACCESO",
                        "en": "03M - ACCESING FOR 3 MONTHS"
                    },
                    "description": {
                        "es": "Por lanzamiento obten 50% de descuento",
                        "en": "50% Free"
                    },
                    "cupon": "RIGHTNOW",
                    "price": 170,
                    "price_cupon": 85
                    },
                    {
                    "KoLic": "06M",
                    "value": {
                        "es": "06M - 6 MESES DE ACCESO",
                        "en": "06M - ACCESING FOR 6 MONTHS"
                    },
                    "description": {
                        "es": "Por lanzamiento obten 50% de descuento",
                        "en": "50% Free"
                    },
                    "cupon": "RIGHTNOW",
                    "price": 320,
                    "price_cupon": 160
                    },
                    {
                    "KoLic": "12M",
                    "value": {
                        "es": "12M - 12 MESES DE ACCESO",
                        "en": "12M - ACCESING FOR 12 MONTHS"
                    },
                    "description": {
                        "es": "Por lanzamiento obten 50% de descuento",
                        "en": "50% Free"
                    },
                    "cupon": "RIGHTNOW",
                    "price": 550,
                    "price_cupon": 275
                    },
                    {
                    "KoLic": "00U",
                    "value": {
                        "es": "00U - NO LIMITADA",
                        "en": "00U -UNLIMMITED ACCESS"
                    },
                    "description": {
                        "es": "Por lanzamiento obten 50% de descuento",
                        "en": "50% Free"
                    },
                    "cupon": "RIGHTNOW",
                    "price": 600,
                    "price_cupon": 300
                    }
                ]
    }
    return sdict

@router.get("/s_pay_validation/{code}")
async def s_pay_validation(code:str):
    """
    class ForLogin(BaseModel):
        userId: str
        KoLic: str
    """
    global appNeo
    
    send = "processing pay with code:" + code + " ... wait a minute please..."
    send = send + f"\n\nupdating new license for user ..."

    neo4j_statement = "match (pc:PaymentsConfirmed) \n" + \
                    "return pc.csId as csId, pc.created as created \n" + \
                    "order by created desc \n" + \
                    "limit 1"
    #print("nneo4j: ", neo4j_statement)
    awsleep(0)

    nodes, log = neo4j_exec(session, 'admin',
                        log_description="getting the last pay inserted ",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())    
    ldict = []
    for node in nodes:
        ldict.append(dict(node))    

    print("sending:", send)
    print("csID initial :", ldict[0]["csId"])

    awsleep(0)
    if len(ldict) > 0:
        paidscompleted = s_checkout_session(ldict[0]["csId"])
    else:
        paidscompleted = s_checkout_session(None)

    """

                sdict = {"csId" : data["id"],
                         "userId" : userIdINDAT,
                         "email" : useremailINDAT,
                        "paym_st" : data["payment_status"],
                        "checkS" : data["status"],
                        "amount_stot" : data["amount_subtotal"],
                        "amount_total" : data["amount_total"],
                        "curr" : data["currency"],
                        "plink" : data["payment_link"],
                        "pintent" :data["payment_intent"],
                        "created" : data["created"]
                }

    """
    for gia, paid in enumerate(paidscompleted[::-1]):
        print(f"paid {gia + 1}: {paid}")
        neo4j_statement = "match (ulink:UserLicPayReq {userId:'" + paid["userId"] + "', \n" + \
                        "   plId:'"+ paid["plink"] + "'})-[rreqPL:UPAYREQUEST_PLINK]->\n" + \
                        "(plink:PaymentsLink {plId:'"+ paid["plink"] + "'}) \n" + \
                        "where not exists {(pc:PaymentsConfirmed {csId:'" + paid["csId"] + "'})} \n" + \
                        " and not exists {(pc:PaymentsConfirmed)-[:CONFIRMED_PAY]->(ulink)} \n" + \
                        "with ulink order by ulink.ctInsert desc limit 1 \n" + \
                        "merge (pc:PaymentsConfirmed {csId:'" + paid["csId"] + "', \n" + \
                                    "userId:'" + paid["userId"] + "'}) \n" + \
                        "on create set pc.ctInsert = datetime() " + \
                        "on match set pc.ctUpdate = datetime() " + \
                        "set pc.email = '" + paid["email"] + "',  \n" + \
                        "   pc.KoLic = ulink.KoLic, \n" + \
                        "   pc.paym_st = '"+ paid["paym_st"] + "',  \n" + \
                        "   pc.checkout_st = '"+ paid["checkS"]+ "',  \n" + \
                        "   pc.amount_stot = "+ str(paid["amount_stot"]) + ",  \n" + \
                        "   pc.amount_total = "+ str(paid["amount_total"]) + ",  \n" + \
                        "   pc.curr = '"+ paid["curr"] + "',  \n" + \
                        "   pc.plink = '"+ paid["plink"] + "',  \n" + \
                        "   pc.pintent = '"+ paid["pintent"] + "',  \n" + \
                        "   pc.created = "+ str(paid["created"]) + "  \n" + \
                        "with ulink, pc \n" + \
                        "/* set ulink.paym_st = pc.paym_st,  \n" + \
                        "   ulink.checkout_st = pc.checkout_st,  \n" + \
                        "   ulink.amount_stot = pc.amount_stot, \n" + \
                        "   ulink.amount_total = pc.amount_total,  \n" + \
                        "   ulink.curr = pc.curr,  \n" + \
                        "   ulink.csId = pc.csId, \n" + \
                        "   ulink.ctUpdate_paid = datetime() \n */" + \
                        "where not pc.KoLic is null \n" + \
                        "match (pr:Product {KoLic:pc.KoLic}) \n" + \
                        "optional match (u:User {userId:pc.userId}) \n" + \
                        " set u.ctUpdate = datetime(), \n" + \
                            "u.kol = pc.KoLic, \n" + \
                            "u.kol_lim_date = case when u.kol_lim_date > datetime() \n" + \
                                                "then (u.kol_lim_date + duration({months:pr.months})) \n" + \
                                                "else (datetime() + duration({months:pr.months})) \n" + \
                                            "end, \n" + \
                            "u.update_lic = datetime() \n" + \
                        "with ulink, pc, u \n" + \
                        "merge (ulink)<-[r:CONFIRMED_PAY]-(pc) \n" + \
                        "set r.ctInsert = datetime() \n" + \
                        "with pc, u \n" + \
                        "merge (pc)-[rlic:CONFIRMED_LIC]->(u) \n" + \
                        "set rlic.ctInsert = datetime() \n" + \
                        "return pc.csId as csId, pc.KoLic as KoLic, u.userId as userId, pc.ctInsert as ctInsert " 
        # "with pl, pc \n" + \
        # "merge (pl)<-[r:CONFIRMED_LINK]-(pc) \n" + \
        # "set r.ctInsert = datetime() \n" + \
        print("neo4j_statement:", neo4j_statement)
        awsleep(0)

        nodes, log = neo4j_exec(session, 'admin',
                            log_description="recording confirmed payment and updating user ",
                            statement=neo4j_statement,
                            filename=__name__,
                            function_name=myfunctionname())    
        ldict = []
        for node in nodes:
            ldict.append(dict(node))    
            

    _sleep(1)
    
    #url = f'https://dt-one-b7bbdf083efc.herokuapp.com/#/sign-in'
    url = appNeo.app_access_cfg.get("app_link", "https://dt-one-b7bbdf083efc.herokuapp.com/")
    response = RedirectResponse(url=url)
    return response #send

@router.post("/stripe_checkout/")
async def stripe_checkout(datas:ForLicense, request:Request
                     , Authorization: Optional[str] = Header(None)):
    """
    class ForLogin(BaseModel):
        userId: str
        KoLic: str
        price_complete: float
        price_cupon : float
        cupon: str
    """
    # ESTE PROCESO BUSCA EN LA DTL001 SI EXISTE UN PAYLINK PARA EL PRODUCTO
    # SELECCIONADO Y LO COMPARA CON LOS PAYLINKS ACTIVOS EN STRIPE
    # SI ESTÁ ACTIVO, REGRESA ESE URL AL USUARIO DE LO CONTRARIO GENERA UN NUEVO PAYLINK

    #print('\n\n *********************** \nauthorization STRIPE : ', Authorization)
    token=validating_token(Authorization)
    userId = token['userId']

    # lista de productos declarados en STRIPE
    product = None
    s_api_key = s_getapi()
    sproducts = s_products(s_api_key)["data"]
    sprices = s_prices(s_api_key)["data"]  # no se usa
    price_default = None
    for gia, product in enumerate(sproducts):
        if product["active"] == True:
            if datas.KoLic.strip() == product["name"].strip():
                price_default = product["default_price"].strip()
    product = price_default

    """
    if kodb() == 1:
        if datas.KoLic == '01M':
            product = 'price_1NtD1qL7SwRlW9BCB8ABhCH0' # price_1NtD1qL7SwRlW9BCB8ABhCH0
        elif datas.KoLic == '03M':
            product = 'price_1NtXe0L7SwRlW9BCmIjLsK3J'
        elif datas.KoLic == '06M':
            product = 'price_1NtXp0L7SwRlW9BCrXchRTAu'
        elif datas.KoLic == '12M':
            product = 'price_1NtXquL7SwRlW9BCvHCNVoxA'
        elif datas.KoLic == '00U':
            product = 'price_1NtXylL7SwRlW9BCf5m9HwSZ'
    elif kodb() == 2:
        if datas.KoLic == '01M':
            product = 'price_1NyLg9L7SwRlW9BC1MlEUdeD' # price_1NtD1qL7SwRlW9BCB8ABhCH0
        elif datas.KoLic == '03M':
            product = 'price_1NyLvmL7SwRlW9BCd1owCOeA'
        elif datas.KoLic == '06M':
            product = 'price_1NyLvwL7SwRlW9BC4BQT0yOh'
        elif datas.KoLic == '12M':
            product = 'price_1NyLw6L7SwRlW9BCqIbyn5ZI'
        elif datas.KoLic == '00U':
            product = 'price_1NyLwFL7SwRlW9BCxw0v71wn'
    else:
        s_api_key = 'error on s_api_key'
    """
        
    neo4j_statement = "match (pl:PaymentsLinks) \n" + \
                    "where pl.KoLic = '" + datas.KoLic + "' \n" + \
                    "return pl.KoLic as KoLic, pl.plId as plId, pl.redirect as plredirect, \n" + \
                        "pl.url as url, pl.product as product, elementId(pl) as eleId \n" + \
                    "order by pl.ctInsert desc"    
    #print("nneo4j: ", neo4j_statement)
    awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting payments links created before",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())    
    ldict = []
    for node in nodes:
        ldict.append(dict(node))
    
    url, pl, eleId, lnk_toanswer = None, None, None, None

    if len(ldict) > 0:
        for gia, plink in enumerate(ldict):
            if plink["KoLic"] == datas.KoLic: 
                url = plink["url"]
                pl = plink["plId"]
                eleId = plink["eleId"]
                lnk_toanswer = plink["plredirect"]
                break            
    
    if pl: # si ya existe un paymenLink declarado buscará si está activo, si no lo lo está creará uno
        lenplinks, plinks_actives = s_paymentslink(s_api_key)  # se extraen los paymentslinks creados y activos en stripe
        if not search_pl_actives_plinks(pl, plinks_actives): #si no esta activo se deberá crear uno nuevo
            pl = None

    if not pl:   # significa que no existe un paymentLink declarado y activo, se deberá crear uno nuevo
        def get_path():  # para obtener el nombre del dominio y server donde se ejecuta
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
        
        # PROCESO para CREAR UN PAYMENT LINK
        stripe.api_key = s_api_key
        #print("parametros de strip:", product, lnk_toanswer)
        stripeLink = stripe.PaymentLink.create(
                #line_items=[{"price": '{{25.99}}', "quantity": 1}],
                line_items=[{"price": product, "quantity": 1}],
                after_completion={"type": "redirect", "redirect": {"url": lnk_toanswer}},
                allow_promotion_codes=True,   
                custom_fields=[{
                    "key": "userId",
                    "label": {"type": "custom", "custom": "Usuario en DTone (DTone's UserId)"},
                    "type": "text"
                }
                ],
        )
        awsleep(0)
        sdict = {'eleId': 'abc'}
        #if not lnk_toanswer.__contains__(":5000"):  # NO SE CREA EN BASE DE DATOS SI ES LOCALHOST
        neo4j_statement = "create (plink:PaymentsLinks {KoLic:'" + datas.KoLic +"', \n" + \
                            " url:'" + stripeLink['url'] + "', plId:'" + stripeLink["id"] + "'}) \n" + \
                        "set plink.ctInsert = datetime(), \n" + \
                            "plink.product = '" + product + "', \n" + \
                        "   plink.redirect = '" + lnk_toanswer + "' \n" + \
                        "return plink.url as url, elementId(plink) as eleId, plink.plId as plId"                    
        #print("neo4j_statement: ", neo4j_statement )

        nodes, log = neo4j_exec(session, 'admin', 
                            log_description="paymenlink saving",
                            statement=neo4j_statement,
                            filename=__name__,
                            function_name=myfunctionname())            
        for node in nodes:
            sdict = dict(node)    
        #url = stripeLink["url"]
        url = stripeLink['url']
        eleId = sdict["eleId"]
        pl = stripeLink["id"]

    # SE CREA registro de la solicitud de pago de liciencia con el usuario que corresponden token.userId
    neo4j_statement = "create (ulink:UserLicPayReq {userId:'" + userId + "', \n" + \
                        " KoLic:'" + datas.KoLic +"', \n" + \
                        " plId:'" + pl + "', \n" + \
                        " product:'" + product + "', \n" + \
                        " url:'" + url + "'}) \n" + \
                    "set ulink.ctInsert = datetime(), \n" + \
                    "   ulink.redirect = '" + lnk_toanswer + "' \n" + \
                    "with ulink \n" + \
                    "match (u:User {userId:'" + userId + "'}) \n" + \
                    "match (plink:PaymentsLinks {KoLic:'" + datas.KoLic + "', plId:ulink.plId}) \n" + \
                    "merge (u)<-[rul:USER_PAYREQUEST]-(ulink) \n" + \
                    "merge (ulink)-[rreqPL:UPAYREQUEST_PLINK]->(plink) \n" + \
                    "return u.userId as userId, ulink.url as url, elementId(ulink) as eleId"
    print("neo4j_statement: ", neo4j_statement )
    await awsleep(0)
    nodes, log = neo4j_exec(session, 'admin', 
                        log_description="user paymenlink request saving",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())            
    lsdict = []
    for node in nodes:
        sdict = dict(node)
        lsdict.append(sdict)

    if len(lsdict) != 1: 
        print(str(len(lsdict)) + " RECORDS, FATAL ERROR TRYING TO GET NEW LINK FOR USER PAYMENT LICENSE REQUEST - CHECK WITH SYSADMIN " + userId)
        url = 'www.delthatech.com'
    
    print("*************************\nStripeLink: ", userId, url, lnk_toanswer, eleId)
    return {"stripe_url":url, "redirect_url": lnk_toanswer, "eleId":eleId} # , "stripe_completeseq": stripeLink}
