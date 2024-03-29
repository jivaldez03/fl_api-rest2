from fastapi import APIRouter, HTTPException, status, Header, Request #, Body

from typing import Optional #, Annotated
from _neo4j.neo4j_operations import neo4j_exec 
                    #,  login_validate_user_pass_trx, \
                    # user_change_password, neo4_log, q01
from _neo4j.config import convert_pass as decodestring

from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, _getdatime_T, get_random_string \
                , email_send, _getdatetime \
                , bcrypt_pass_compare, bcrypt_pass

from asyncio import sleep as awsleep

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
    duserId = datas.userId
    duserId = duserId.lower().strip().replace("'","_").replace('"','_')

    neo4j_statement = "with '" + duserId +  "' as userId \n" + \
                "match (us:User {userId:userId}) \n" +  \
                "optional match (us)<-[l:LICENSE]-(kol:KoL {active:true}) \n" + \
                "return us.userId, us.name, us.keypass, us.age, us.email, us.email_alt, \n" + \
                    "us.native_lang, coalesce(us.selected_lang,'es') as selected_lang, \n" + \
                    "us.country_birth, us.country_res, us.kol as kol, us.kol_lim_date as kol_lim_date limit 1"
    nodes, loglogin = neo4j_exec(session, duserId,
                        log_description="validate login user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    await awsleep(0)

    result = {}
    for elem in nodes:
        result=dict(elem) #print(f"elem: {type(elem)} {elem}")   
    #result = login_validate_user_pass_trx(session, duserId) # , datas.password)
    # FIN DE VIGENCIA DE LICENCIA
    if len(result) == 0:  # incorrect user
        print("no records for ",duserId)
        #log = neo4_log(session, duserId, 'login - invalid user or password - us', __name__, myfunctionname())
        merror = 'Usuario-Password Incorrecto / Invalid User-Password'
        resp_dict ={'status': 'ERROR', 'text': merror, "userId":"",  "username": "", 
                    "age":0, 
                    "country_birth": "", 
                    "country_res": ""
                }        
        
        neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(loglogin[1]) + "')\n" + \
                    ", user:'" + duserId + "'}) \n" + \
                    "where elementId(l) = '" + loglogin[0] + "' \n" + \
                    "set l.ctClosed = datetime(), l.additionalResult = '" + merror + "' \n" + \
                    "return count(l)"
        await awsleep(0)
        nodes, log = neo4j_exec(session, duserId,
                        log_description=merror
                        , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                        , recLog=False)
        
        #print("========== id: ", duserId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=merror
            #headers={"WWW-Authenticate": "Basic"},
        )
    else:
        #passdecode = decodestring(datas.password) #decode()
        #print("befodecode:", passdecode)        
        #passdecode = passdecode.decode('utf-8')
        #print("dp_cfg:", passdecode)
        passtocompare = datas.password
        realpass = bytes(result["us.keypass"], 'utf-8')
        if len(result["us.keypass"]) < 30:
            passaccess = False
        else:
            passaccess = bcrypt_pass_compare(bytes(passtocompare, 'utf-8'), realpass)
        if not passaccess: #  passdecode != result["us.keypass"]:
            if passtocompare == result["us.keypass"]:
                newencripass=bcrypt_pass(passtocompare)
                #print("newencpass bef byte:", newencripass)
                newencripass=newencripass.decode('utf-8')
                #print("newencpass:", newencripass)
                neo4j_statement = "match (u:User {userId:'" + duserId + "'}) \n" + \
                        "set u.keypass = '" + newencripass + "' \n" + \
                        "return u.userId"                        
                await awsleep(0)
                nodes, log = neo4j_exec(session, duserId,
                                log_description='update decodepass'
                                , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                                , recLog=False)
                passaccess = True            

        #if datas.password == result["us.keypass"]:
        if not result["kol_lim_date"] is None \
            and passaccess: #passtocompare == result["us.keypass"]:   # success access
            #log = neo4_log(session, duserId, 'login - success access', __name__, myfunctionname())
            kol_lim_date = str(result["kol_lim_date"])
            kol_lim_date = dt.strptime(kol_lim_date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            print("\n\nKOL:", duserId, result["kol"], result["kol_lim_date"],"\n\n")
            
            #print(kol_lim_date, str(kol_lim_date), type(kol_lim_date))
            resp_dict ={'status': 'OK', 
                        'text': 'successful access',
                        "userId": duserId,
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
            
            token = funcs.return_token(data=resp_dict)
            result_tk = {"token": token, 
                        "user_name": result["us.name"], 
                        "age":0, 
                        "country_birth": result["us.country_birth"], 
                        "country_res": result["us.country_res"],
                        "native_lang" : result["us.native_lang"],
                        "selected_lang" : result["selected_lang"]
            }
            if kol_lim_date < _getdatetime():
                print("\n\nKOL:", duserId, result["kol"], type(result["kol_lim_date"]), result["kol_lim_date"],"\n\n")
                merror = "License Permission Error"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=result_tk
                )
            neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(loglogin[1]) + "')\n" + \
                        ", user:'" + duserId + "'}) \n" + \
                        "where elementId(l) = '" + loglogin[0] + "' \n" + \
                        "set l.ctClosed = datetime(), l.additionalResult = 'login - success access' \n" + \
                        "return count(l)"
            await awsleep(0)

            nodes, log = neo4j_exec(session, duserId,
                            log_description="validate login user"
                            , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                            , recLog=False)
            
            """
            {"token": token, 
                        "user_name": result["us.name"], 
                        "age":0, 
                        "country_birth": result["us.country_birth"], 
                        "country_res": result["us.country_res"],
                        "native_lang" : result["us.native_lang"],
                        "selected_lang" : result["selected_lang"]
            }
            """
            return  result_tk
        
        else: # incorrect pass
            #log = neo4_log(session, duserId, 'login - invalid user or password', __name__, myfunctionname())        
            merror = "Usuario-Password Incorrecto - Invalid User-Password"
            resp_dict ={'status': 'ERROR', 'text': merror, "username": "",  
                        "age":0, 
                        "country_birth": "", 
                        "country_res": ""
                    }
            neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(loglogin[1]) + "')\n" + \
                        ", user:'" + duserId + "'}) \n" + \
                        "where elementId(l) = '" + loglogin[0] + "' \n" + \
                        "set l.ctClosed = datetime(), l.additionalResult = 'invalid user or password - (p)' \n" + \
                        "return count(l)"
            await awsleep(0)
            nodes, log = neo4j_exec(session, duserId,
                            log_description=merror
                            , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                            , recLog=False)        

            #print("========== id: ", duserId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raise_HttpException-user/pass")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,            
                detail =merror
                #headers={"WWW-Authenticate": "Basic"},
            )
    print("id: ", duserId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return resp_dict
#kol_lim_date datas.userId

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

    neo4j_statement = "match (us:User {userId:'" + token['userId'] + "'}) \n" + \
                    "return us.userId, us.keypass limit 1"

    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="verify old pass to update",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())    
    result = {}
    for elem in nodes:
        result=dict(elem)

    if len(result) > 0:
        realpass = bytes(result["us.keypass"], 'utf-8')
        passaccess = bcrypt_pass_compare(bytes(datas.oldkeypass, 'utf-8'), realpass)

        if passaccess:
            newencripass=bcrypt_pass(datas.newkeypass)
            newencripass=newencripass.decode('utf-8')
            neo4j_statement = "match (us:User {userId:'" + token['userId'] + "'}) \n" +  \
                            "set us.keypass = '" + newencripass + "', \n" + \
                            "   us.ctUpdate = datetime() \n" + \
                            "return us.userId, us.keypass limit 1"
            nodes, log = neo4j_exec(session, token['userId'],
                                log_description="update password",
                                statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
            result = {}
            for elem in nodes:
                result=dict(elem)

            if len(result) == 1: #update pass was done
                neo4j_statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "')\n" + \
                            ", user:'" + token['userId'] + "'}) \n" + \
                            "where elementId(l) = '" + log[0] + "' \n" + \
                            "set l.ctClosed = datetime(), l.additionalResult = 'updated password' \n" + \
                            "return count(l)"
                await awsleep(0)
                nodes, log = neo4j_exec(session, token['userId'],
                                log_description="updating password"
                                , statement=neo4j_statement, filename=__name__, function_name=myfunctionname()
                                , recLog=False)        
        else: # oldpass is wrong
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user or password",
            )
    else: #if len(result) == 0:
        #print("id: ", token['userId'], " dt: ", _getdatime_T(), " -> ", myfunctionname(), " - raiseHTTP - user / pass")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
        )
        
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

    kok = ['supp','comm', 'lics', 'clam', 'pmet', 'dacc', 'othr']
    if selected_lang == 'es':
        koh = ['Soporte','Comentario', 'Licencias', 'Queja', 'Métodos de Pago', 'Eliminar Cuenta', 'Otro']
    else:
        koh = ['Support','Comments', 'Licenses', 'Claim', 'Payment Methods', 'Drop Account', 'Other']

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
                    " on create set us.ctInsert = datetime() \n" + \
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
    await awsleep(0)

    nodes, log = neo4j_exec(session, token['userId'],
                        log_description="update user configure id",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
        
    result = {}
    for elem in nodes:
        result=dict(elem)
        
    print("========== id: ", token['userId'].lower(), " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


@router.get("/signupval/{code}")
async def signup_complete(code:str):
    global appNeo
    """
    Function for reset the user password \n
    {
    "code":str
    }
    """
    neo4j_statement = "match (u:User {signup_key:'" + code + "'}) \n" + \
                    "where (u.ctInsert + duration({minutes: 3600})) >=  datetime() and \n" + \
                    " u.singup_val is null \n" + \
                    "set u.ctUpdate = datetime() \n" + \
                    "return u.userId, u.email, u.selected_lang as selected_lang"
    #print('statement:', neo4j_statement)
    await awsleep(0)
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
            
            msg = msg + "\n\nLa secuencia general es muy simple:"
            msg = msg + "\n0. Crear paquete nuevo de palabras"
            msg = msg + "\n1. Aprender. Tarjeta superior (Inglés) - Tarjeta Inferior (Español)"
            msg = msg + "\n2. Relacionar tarjetas por Visualización y Audición"
            msg = msg + "\n3. Relacionar tarjetas por Audición"
            msg = msg + "\n4. Activa todos tus sentidos - Visualización - Audición - Memoria"
            msg = msg + "\n5. Activa todos tus sentidos - con más tajertas (opcional)"
            msg = msg + "\n6. Archivar paquete"
            msg = msg + "\n7. Practicar en los juegos - todos ellos, cada juego exige más que el anterior"
            

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
                        "where //(u.ctInsert + duration({minutes: 3600})) >=  datetime() and \n" + \
                        " u.singup_val is null \n" + \
                        "set u.signup_key = reverse(u.signup_key), \n" + \
                            "u.signup_val = datetime(), \n" + \
                            "u.ctUpdate = datetime(), \n" + \
                            "u.kol = '7-FREEPERIOD', \n" + \
                            "u.kol_lim_date = (datetime() + duration({days:7})) \n" + \
                        "return u.userId, u.email, u.selected_lang as selected_lang"
        #print('statement:', neo4j_statement)
        await awsleep(0)

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

    uuserId = datas.userId.lower().strip()
    uname = datas.name.strip()
    ukeyp = datas.password.strip()
    uemail = datas.email.lower().strip()
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
    elif '"' in uuserId + uname + ukeyp + uemail or \
        "'" in uuserId + uname + ukeyp + uemail:
        koerror = -3
        msg = "Uso de carácteres no permitidos / Use of no allowed characters"
    else:
        """
        match (u:User) 
        where (u.ctInsert + duration({minutes: 3600})) <  datetime() 
                and not u.signup_key is null and  u.signup_val is null 
                and not exists {(u)<-[:PACKAGED]-(pkg:Package)}
        detach delete u
        //return u.userId, u.name, u.email, u.ctInsert, u.signup_key, u.signup_val
        """
        neo4j_statement = "with '" + uuserId +  "' as userId, \n" + \
                            "'" + uemail +  "' as usemail \n" + \
                    "optional match (u:User) \n" + \
                    "where (u.ctInsert + duration({minutes: 3600})) <  datetime() \n" + \
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
        await awsleep(0)
        nodes, log = neo4j_exec(session, uuserId, #datas.userId.lower(),
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
            msg = "Bienvenido a DTone.\n\nEste mensaje corresponde a su solicitud de registro en DTone, " + \
                "el siguiente link tiene validez por sólo 24 horas (podrá crear otra solicitud si lo desea). " + \
                "Al dar click en él su registro estará completo.\n\n " + \
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

        newencripass=bcrypt_pass(ukeyp)
        ukeyp=newencripass.decode('utf-8')

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
            await awsleep(0)
            nodes, log = neo4j_exec(session, uuserId, #datas.userId.lower(),
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
    await awsleep(0)
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
    await awsleep(0)
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
    await awsleep(0)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting organization for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)        
        listcat.append({'language': sdict['langname']})

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listcat

