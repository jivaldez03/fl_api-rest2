from fastapi import APIRouter, HTTPException, status, Header, Request #, Body

from typing import Optional #, Annotated
from _neo4j.neo4j_operations import neo4j_exec 
                    #,  login_validate_user_pass_trx, \
                    # user_change_password, neo4_log, q01

from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, _getdatime_T, get_random_string, email_send, _getdatetime

from datetime import datetime as dt

#models:
from app.model.md_params_auth import ForSignUp, ForLogin, ForChangePass, ForUserReg

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

router = APIRouter()
#import sys
#def callersfunctionname(  ):
#    return sys._getframe(2).f_code.co_name

#him = callersfunctionname()

#def login_user(user, keypass, User_Agent: Annotated[str | None, Header()] = None, userId: Annotated[str | None, Header()] = None):
#def login_user(datas: Annotated[forlogin, Body(embed=True)]):

@router.post("/login/")   # {user} {keypass}
async def login_user(datas: ForLogin):
    """
    Function to create a new session \n

    this operation needs a input structure such as {userId, password}
    """
    global session
 
    neo4j_statement = "with '" + datas.userId.lower() +  "' as userId \n" + \
                "match (us:User {userId: userId }) \n" +  \
                "optional match (us)<-[l:LICENSE]-(kol:KoL {active:true}) \n" + \
                "return us.userId, us.name, us.keypass, us.age, us.email, us.email_alt, \n" + \
                    "us.native_lang, coalesce(us.selected_lang,'es') as selected_lang, \n" + \
                    "us.country_birth, us.country_res, us.kol as kol, us.kol_lim_date as kol_lim_date limit 1"
    nodes, log = neo4j_exec(session, datas.userId.lower(),
                        log_description="validate login user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    
    result = {}
    for elem in nodes:
        result=dict(elem) #print(f"elem: {type(elem)} {elem}")   
    #result = login_validate_user_pass_trx(session, datas.userId.lower()) # , datas.password)
    # FIN DE VIGENCIA DE LICENCIA
    kol_lim_date = str(result["kol_lim_date"])
    kol_lim_date = dt.strptime(kol_lim_date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
    #print('fechas to compare:', kol_lim_date, _getdatetime())
    if len(result) == 0:  # incorrect user
        print("no records - fname__name__and more:",__name__)
        #log = neo4_log(session, datas.userId, 'login - invalid user or password - us', __name__, myfunctionname())
        merror = 'Usuario-Password Incorrecto / Invalid User-Password'
        resp_dict ={'status': 'ERROR', 'text': merror, "userId":"",  "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }        
        
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = '" + merror + "' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description=merror
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)
        
        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=merror
            #headers={"WWW-Authenticate": "Basic"},
        )
    elif kol_lim_date < _getdatetime():
        print("\n\nKOL:", datas.userId.lower(), result["kol"], type(result["kol_lim_date"]), result["kol_lim_date"],"\n\n")
        merror = "License Permission Error"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=merror
        )
    elif datas.password == result["us.keypass"]:   # success access
        #log = neo4_log(session, datas.userId.lower(), 'login - success access', __name__, myfunctionname())
        print("\n\nKOL:", datas.userId.lower(), result["kol"], result["kol_lim_date"],"\n\n")
        
        #print(kol_lim_date, str(kol_lim_date), type(kol_lim_date))
        resp_dict ={'status': 'OK', 
                    'text': 'successful access',
                    "userId":datas.userId.lower(),
                    "username": result["us.name"], 
                    "useremail": result["us.email"],
                    "useremail_alt": result["us.email_alt"],
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.native_lang"],
                    "selected_lang" : result["selected_lang"],
                    "kol" : result["kol"],
                    "kol_lim_date" : str(kol_lim_date)
                }
        #print("resp_dict:", resp_dict)
        
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'login - success access' \n" + \
                    "return count(l)"
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description="validate login user"
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)

        token = funcs.return_token(data=resp_dict)
        return {"token": token, 
                    "user_name": result["us.name"], 
                    "age":0, 
                    "country_birth": result["us.country_birth"], 
                    "country_res": result["us.country_res"],
                    "native_lang" : result["us.native_lang"],
                    "selected_lang" : result["selected_lang"]
        }
    else: # incorrect pass
        #log = neo4_log(session, datas.userId.lower(), 'login - invalid user or password', __name__, myfunctionname())        
        merror = "Usuario-Password Incorrecto - Invalid User-Password"
        resp_dict ={'status': 'ERROR', 'text': merror, "username": "",  
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + datas.userId.lower() + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'invalid user or password - (p)' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, datas.userId.lower() ,
                        log_description=merror
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)        

        #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail =merror
            #headers={"WWW-Authenticate": "Basic"},
        )
    print("id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return resp_dict
#

@router.post("/change_pass/")
async def user_change_pass(datas:ForChangePass, Authorization: Optional[str] = Header(None)):
    """
    Function for change the user password \n
    {
    "oldkeypass":str,
    "newkeypass":str"
    }
    """
    global session
    token=funcs.validating_token(Authorization)

    neo4j_statement = "match (us:User {userId:'" + token['userId'] + "', \n" + \
                    "keypass:'" + datas.oldkeypass + "'}) \n" +  \
                    "set us.keypass = '" + datas.newkeypass + "' \n" + \
                    "return us.userId, us.keypass limit 1"

    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="update password",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    """nodes = user_change_password(session, token['userId'].lower(), datas.oldkeypass, datas.newkeypass,
                                 filename=__name__,
                                 function_name=myfunctionname())"""
    
    result = {}
    for elem in nodes:
        result=dict(elem)

    if len(result) == 0:
        #print("id: ", token['userId'], " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raiseHTTP - user / pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
        )
    else: # update pass was done
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                    ", user:'" + token['userId'] + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = 'updated password' \n" + \
                    "return count(l)"
        
        nodes, log = neo4j_exec(session, token['userId'],
                        log_description="updating password"
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': "password updated"}


@router.get("/tdt/")
async def token_data(Authorization: Optional[str] = Header(None)):
    """
    Function for get tdt\n
    {
    }
    """
    global session
    token=funcs.validating_token(Authorization)
    
    userId = token["userId"]
    name = token["username"]
    selected_lang = token["selected_lang"]

    kok = ['supp','comm', 'lics', 'clam', 'pmet', 'othr']
    if selected_lang == 'es':
        koh = ['Soporte','Comentario', 'Licencias', 'Queja', 'Métodos de Pago', 'Otro']
    else:
        koh = ['Support','Comments', 'Licenses', 'Claim', 'Payment Methods', 'Other']

    koh_k = []
    for gia, ele in enumerate(koh):
        koh_k.append({"text": ele, "value": kok[gia]})
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {"user":userId, 
            "name": name, 
            "selected_lang": selected_lang,
            "koh" : koh_k
    }


@router.post("/userreg/")
async def user_registry(datas:ForUserReg, Authorization: Optional[str] = Header(None)):
    """
    Function for change the user password \n
    {
    userId:str
    orgId:str
    name: str
    email:str
    email_alt:str
    native_lang:str
    selected_lang:str
    country_birth: str
    country_res: str
    koflic
    }
    """
    global session
    token=funcs.validating_token(Authorization)
    orgId = "DTL-01"

    dname = datas.name if not isinstance(datas.name, type(None)) else datas.userId
    demail = datas.email if not isinstance(datas.email, type(None)) else '__'
    demail_alt = datas.email_alt if not isinstance(datas.email_alt, type(None)) else 'null'
    dnative_lang = datas.native_lang if not isinstance(datas.native_lang, type(None)) else 'Español'
    dselected_lang = datas.selected_lang if not isinstance(datas.selected_lang, type(None)) else 'es'
    dcountry_birth = datas.country_birth if not isinstance(datas.country_birth, type(None)) else 'null'
    dcountry_res = datas.country_res if not isinstance(datas.country_res, type(None)) else 'null'
    dkol = datas.kolic if not isinstance(datas.kolic, type(None)) else 'UNIVERSAL'

    neo4j_statement = "merge (us:User {userId:'" + datas.userId + "'}) \n" + \
                    " on match set us.ctUpdate = datetime()  \n" + \
                    " on create set us.ctInsert = datetime(), us.keypass='"+ datas.userId+"' \n" + \
                    "set us.name = '" + dname + "', \n" + \
                    "  us.email = '" + demail + "', \n" + \
                    "  us.email_alt = '" + demail_alt + "', \n" + \
                    "  us.native_lang = '" + dnative_lang + "', \n" + \
                    "  us.selected_lang = '" + dselected_lang + "', \n" + \
                    "  us.country_birth = '" + dcountry_birth + "', \n" + \
                    "  us.country_res = '" + dcountry_res + "', \n" + \
                    "  //us.kol = '" + dkol + "', \n" + \
                    "  us.ctUpdate = datetime() \n" + \
                    "with us \n" + \
                    "match (o:Organization {idOrg:'" + orgId + "'})" + \
                    "merge (o)<-[rou:RIGHTS_TO]-(us) \n" + \
                    " on match set rou.ctUpdate = datetime()  \n" + \
                    " on create set rou.ctInsert = datetime() \n" + \
                    "return us.userId, us.name, us.native_lang, us.selected_lang, us.kol limit 1"

    #print("neo4j:", neo4j_statement)
    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="update user configure id",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
        
    result = {}
    for elem in nodes:
        result=dict(elem)
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


@router.get("/signupval/{code}")
def signup_complete(code:str):
    global appNeo
    """
    Function for reset the user password \n
    {
    "code":str
    }
    """
    neo4j_statement = "match (u:User {signup_key:'" + code + "'}) \n" + \
                    "where (u.ctInsert + duration({minutes: 60})) >=  datetime() and \n" + \
                    " u.singup_val is null \n" + \
                    "set u.ctUpdate = datetime() \n" + \
                    "return u.userId, u.email, u.selected_lang as selected_lang"
    #print('statement:', neo4j_statement)
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
        if sdict["selected_lang"] == 'es':
            msg = "Su registro en DTone ha concluído. No olvide notificar cualquier duda o comentario (en Menu/Config/Soporte)."
            msg = msg + "\n\nSu acceso a la plataforma de DTone está listo: " + \
                    appNeo.app_access_cfg.get("app_link", "https://dt-one-b7bbdf083efc.herokuapp.com/")
            msg = msg + "\n\nTe recomendamos visitar nuestro canal en youtube - " + \
                    appNeo.app_access_cfg.get("youtubechannel", "")            
            msg = msg + " donde encontrarás la guía de uso de DTone - " + \
                    appNeo.app_access_cfg.get("playlist_userguide", "") + " - para que aproveches al máximo sus beneficios."

            subj = "DTone - Notificación de Registro - " + userId
        else:
            msg = "Registration in DTone has been completed. Don't forget to access Menu/Config/Support for any doubt or comment."
            msg = msg + "\n\nYour access to DTone platform is ready: " + \
                    appNeo.app_access_cfg.get("app_link", "https://dt-one-b7bbdf083efc.herokuapp.com/")
            msg = msg + "\n\nDon't forget to visit our youtube channel - " + \
                    appNeo.app_access_cfg.get("youtubechannel", "")            
            msg = msg + "you will find the DTone's user guide - " + \
                    appNeo.app_access_cfg.get("playlist_userguide", "") + " - to understand how to use this tool."
            
            subj = "DTone - Registration Notice - " + userId        
        
        sentmail = email_send(userId, emailuser, msg, subj, appNeo)
        refmail = emailuser.split('@')


        sentmail = sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ")"
        #sentmail = sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ")"

        neo4j_statement = "match (u:User {signup_key:'" + code + "'}) \n" + \
                        "where //(u.ctInsert + duration({minutes: 60})) >=  datetime() and \n" + \
                        " u.singup_val is null \n" + \
                        "set u.signup_key = reverse(u.signup_key), \n" + \
                            "u.signup_val = datetime(), \n" + \
                            "u.ctUpdate = datetime(), \n" + \
                            "u.kol = '7-FREEPERIOD', \n" + \
                            "u.kol_lim_date = (datetime() + duration({days:7})) \n" + \
                        "return u.userId, u.email, u.selected_lang as selected_lang"
        #print('statement:', neo4j_statement)
        nodes, log = neo4j_exec(session, 'admin', 
                            log_description="sign up notification",
                            statement=neo4j_statement,
                            filename=__name__,
                            function_name=myfunctionname())
        
    else:
        sentmail = "DTone has tried to complete the process and send you an email. " + \
                    "Something was wrong, review your email. " + \
                    "Likely your process was delayed and it was cancelled, trying sign up again."
    
    return sentmail

@router.post("/signup/")   # {user} {keypass}
async def login_signup(datas: ForSignUp, request:Request):
    """
    Function to create a possible user \n

    userId  : str
    password: str
    name    : str
    email   : str
    lang    : str
    
    """
    global session

    uuserId = datas.userId.lower()
    uname = datas.name
    ukeyp = datas.password
    uemail = datas.email.lower()
    if datas.lang == 'en':
        ulang = datas.lang
    else:
        ulang = 'es'
    
    koerror = 0
    msg = ""
    # if any data is None --- error = -2
    if not uuserId or not uname or not ukeyp or not uemail or not ulang:
        koerror = -2
        msg = "Datos incompletos / Incomplete data"
    else:
        """
        match (u:User) 
        where (u.ctInsert + duration({minutes: 60})) <  datetime() 
                and not u.signup_key is null and  u.signup_val is null 
                and not exists {(u)<-[:PACKAGED]-(pkg:Package)}
        detach delete u
        //return u.userId, u.name, u.email, u.ctInsert, u.signup_key, u.signup_val
        """
        neo4j_statement = "with '" + uuserId +  "' as userId, \n" + \
                            "'" + uemail +  "' as usemail \n" + \
                    "optional match (u:User) \n" + \
                    "where (u.ctInsert + duration({minutes: 60})) <  datetime() \n" + \
                    "        and not u.signup_key is null and  u.signup_val is null \n" + \
                    "        and not exists {(u)<-[:PACKAGED]-(pkg:Package)} \n" + \
                    "        and not exists {(u)<-[raM:ARCHIVED_M]-(arcM:Archived_M)} \n" + \
                    " detach delete u \n" + \
                    "with '" + uuserId +  "' as userId, \n" + \
                            "'" + uemail +  "' as usemail \n" + \
                    "optional match (us:User {userId: userId}) " +  \
                    "optional match (usmail:User {email: usemail}) " +  \
                    "return us.userId as uuserId, us.name as uname, \n" + \
                            "usmail.userId as ususerId, usmail.email as usemail limit 1"
        nodes, log = neo4j_exec(session, datas.userId.lower(),
                            log_description="validate user and email",
                            statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
        #print("statement neo4j:", neo4j_statement)
        result = {}
        for elem in nodes:
            result=dict(elem) #
        print("****************+\nresult", result)
        if len(result) > 0:  # incorrect user
            msg = ""
            koerror = 0
            if result["uuserId"] != None: 
                msg = "Usuario no permitido / Invalid user Id" 
                koerror = -1
            if result["usemail"] != None: 
                msg = msg + (" -- " if msg != "" else "") + \
                        "Cuenta de correo no permitida / Invalid email account"
                koerror = -1
        else:
            print ("NO VALORES PARA RESULT - NO ES POSIBLE VALIDAR")
            koerror == -3   
    #print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
        
    if koerror < 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg
            #headers={"WWW-Authenticate": "Basic"},
        )
    else:

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
        
        temppass = get_random_string(50)

        method, pathcomplete, serverlnk = get_path()

        #print("mmmethod:", method)
        #print("pathcomplete:", pathcomplete)
        #print("serverlnk:", serverlnk)

        lnk_toanswer = "http://" + serverlnk + "/dt/auth/signupval/"    
    
        if ulang == 'es':
            msg = "Bienvenido a DTone.\n\nEste mensaje corresponde a su registro en DTone, " + \
                "al dar click al siguiente link su registro estará completo.\n\n " + \
                lnk_toanswer + temppass +  " \n\n" + \
                "Esta notificación no requiere respuesta."
            subj = "DTone - Notificación de Solicitud de Registro - " + uuserId
        else:
            msg = "Welcome to DTone.\n\nThis message is about your Sign Up process in DTone, " + \
                "by clicking the following link the sign up process will be complete.\n\n " + \
                lnk_toanswer + temppass +  " \n\n" + \
                "This notification does not require a response."          
            subj = "DTone - Sign Up Notification - " + uuserId

        sentmail = email_send(uuserId, uemail, msg, subj, appNeo)

        if sentmail != "False":   # email_send return an string 
            neo4j_statement = "with '" + uuserId +  "' as userId, \n" + \
                                    "'" + uemail +  "' as uemail, \n" + \
                                    "'" + ukeyp +  "' as ukeyp, \n" + \
                                    "'" + uname +  "' as uname, \n" + \
                                    "'" + ulang +  "' as ulang, \n" + \
                                    "'DTL-01' as idOrg \n" + \
                        "merge (u:User {userId:userId})  \n" + \
                        "set u.keypass = ukeyp, \n" + \
                            " u.name = uname, u.email = uemail, \n" + \
                            " u.selected_lang = ulang, \n" + \
                            " u.signup_key = '" + temppass + "', \n" + \
                            " u.ctInsert = datetime() \n" + \
                        "with u, idOrg \n" + \
                        "match (o:Organization {idOrg:idOrg})  \n" + \
                        "merge (u)-[r:RIGHTS_TO]->(o) \n" + \
                        " set r.ctInsert = datetime() \n" + \
                        "return u.userId, u.name, u.email, u.selected_lang "
            #print("statement neo4j:", neo4j_statement)

            nodes, log = neo4j_exec(session, datas.userId.lower(),
                                    log_description="insert user sign up",
                                    statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
                
            result = {}
            for elem in nodes:
                result=dict(elem) #

            refmail = uemail.split('@')
            sentmail = "<h1>DTone has tried to send you an email</h1><strong>" + \
                sentmail + " ... (" + refmail[0][:2] + "..." + refmail[0][-2:] + '@' + refmail[1] + ") </strong>"
            result["user_signup"] = "OK"
        else:
            result["user_signup"] = "Fail"
    print("========== id: ", datas.userId.lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


@router.get("/org/")
async def get_org(Authorization: Optional[str] = Header(None)):
    """
    Function to get all categories and subcategories allowed for the user

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
        
    neo4j_statement = "with '" + userId + "' as userId " + \
                        "match (u:User {userId:userId})-[:RIGHTS_TO]->(o:Organization) \n" + \
                        "return o.idOrg as idOrg, o.name as name, o.lSource as Source, o.lTarget as Target"
    
    #print('cats-subcats:', neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)
        ndic = {'orgId': sdict["idOrg"], 'OrgName': sdict["name"]
                , 'source' : sdict["Source"], 'target': sdict["Target"]}
        listcat.append(ndic)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat


@router.get("/countries_borrar/")
async def countries(Authorization: Optional[str] = Header(None)):
    """
    Function to get all countries

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
        
    neo4j_statement = "with '" + userId + "' as userId " + \
                        "match (u:User {userId:userId})-[:RIGHTS_TO]->(o:Organization) \n" + \
                        "return o.idOrg as idOrg, o.name as name, o.lSource as Source, o.lTarget as Target"
    
    #print('cats-subcats:', neo4j_statement)
    """
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)
        ndic = {'orgId': sdict["idOrg"], 'OrgName': sdict["name"]
                , 'source' : sdict["Source"], 'target': sdict["Target"]}
        listcat.append(ndic)
    """
    listcat = []
    sdict = {'country':'México'}
    sdict2 = {'country':'Costa Rica'}
    sdict3 = {'country':'United States'}
    listcat = [sdict, sdict2, sdict3]
    listcat.append({'country':'Guatemala'})
    listcat.append({'country':'Puerto Rico'})
    listcat.append({'country':'Germany'})
    listcat.append({'country':'Hungry'})
    listcat.append({'country':'El Salvador'})
    listcat.append({'country':'Belice'})
    listcat.append({'country':'Chile'})

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat


@router.get("/get_countries/")
async def get_countries(Authorization: Optional[str] = Header(None)):
    """
    Function to get all countries

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
        
    neo4j_statement = "match (cou:Country) \n" + \
                      "return distinct cou.name as name order by cou.name"
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)        
        listcat.append({'country': sdict['name']})

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat


@router.get("/get_langs/")
async def get_langs(Authorization: Optional[str] = Header(None)):
    """
    Function to get all languages

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
        
    neo4j_statement = "match (cou:Country) \n" + \
                      "return distinct cou.language as langname order by langname"
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)        
        listcat.append({'language': sdict['langname']})

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat

