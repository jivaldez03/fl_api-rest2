from neo4j import Query #, GraphDatabase, Result, unit_of_work #neo4j._sync.work.result.Result
from __generalFunctions import monitoring_function, email_send \
                , _getdatime_T, _getdatetime, _getenv_function
from neo4j.exceptions import SessionExpired, SessionError \
            , ServiceUnavailable, ResultError, WriteServiceUnavailable \
            , CypherSyntaxError, CypherTypeError

from _neo4j import appNeo, session, log, connectNeo4j, timeout_const, timeforneo4jdriver
from datetime import timedelta as delta
from time import sleep
from fastapi import HTTPException, status
from .config import kodb


"""
https://neo4j.com/docs/python-manual/current/transformers/

import neo4j

pandas_df = driver.execute_query(
    "UNWIND range(1, 10) AS n RETURN n, n+1 as m",
    database_="neo4j",
    result_transformer_=neo4j.Result.to_df
)
"""

def reconect_neo4j(user):
    global appNeo, session, log
    
    while True:
        try:
            if user == None:
                user = 'admin'
            appNeo, session, log = connectNeo4j(user, 'starting session')
            break
        except: 
            sleep(2)
            continue

    return

def q01_borrar(session, strtoexec= None):
    if strtoexec == None:
        q01 = 'match (n:English)-->(s:Spanish) return n.word, s.word'
    else:
        q01 = strtoexec        
    nodes = session.run(q01, timeout = timeout_const)
    return nodes

def recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser):
    global timeforneo4jdriver

    if kodb() == 1: 
        serviceActive = 'dev'
    else:
        serviceActive = 'prod'
    rmail = email_send(user, None, _getdatime_T() + "\n\n" + detailmessage + "\n\n" + messageforuser
                        , 'Neo4j Execution Error - ' + user + ' - ' + serviceActive )
    if rmail == "False":
            print("Exception:", rmail)
            errorlog = neo4_log(session, user, "smtplib.SMTP_SSL.smtp.send_message"
                                , "ERROR: " + rmail, 'email_send')
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n") 
            nodes = []

    #print("enviado email - ", rmail)
    #appNeo, session, log = connectNeo4j(user, 'starting session')
    return _getdatetime()
    
#@unit_of_work(timeout=timeout_const)  # seconds
def execution(function_name, statement, user, log_exec):
    global appNeo, session, log, timeforneo4jdriver

    # next loop exist only if we have an error about our session, it try to reconnect again
    trying = 0
    statuserror = 200
    detailmessage = ""
    messageforuser = ""
    while trying < 5:
        trying += 1

        print('temporal variables:' , _getdatetime(), timeforneo4jdriver)
        if _getdatetime() > timeforneo4jdriver:
                #print('temporal variables:' , _getdatetime(), timeforneo4jdriver)
                appNeo.close()
                #print("enviando email - FOR RECONNECTION")
                if kodb() == 1: 
                    serviceActive = 'dev'
                else:
                    serviceActive = 'prod'
                msgreconnect=_getdatime_T() + '\n\nRE-START CONNECTION\n\n'
                appNeo, session, log = connectNeo4j(user, 'starting session')                

                if session: 
                    timeforneo4jdriver = _getdatetime() + delta(minutes=int(_getenv_function('MINS_FOR_RECONNECT')))

                print(msgreconnect, "\nNEW TIME FOR RECONNECTION ->", timeforneo4jdriver)

                #print("msgreconnect", msgreconnect)
                try:
                    rmail = email_send(user, None, msgreconnect
                                    , 'Neo4j RESTART CONNECTION - ' + serviceActive )
                except Exception as error:
                    print("error enviando mensaje de reconección", type(error).__name__, error)
                    sleep(1)
        try:
            #print("*********************** inicia ejecución en neo4_exec " , function_name)
            """
            print("intentando por vez ", trying)
            input  ('espere..... ')
            if trying == 1:
                raise SessionExpired            
            elif trying == 2:
                raise WriteServiceUnavailable
            elif trying == 3:
                raise SessionError
            elif trying == 4:
                raise ServiceUnavailable
            elif trying == 5:
                raise ResultError
            elif trying == 6:
                raise Exception
            """
            nodes = session.run(Query(statement, timeout=timeout_const), name='query')

            statuserror = 200            
            #print("*********************** finaliza ejecución en neo4_exec", function_name, type(nodes))
            break
        except CypherSyntaxError as error:
            print("Exception:", type(error).__name__, error)
            statuserror = 502
            errorlog = neo4_log(session, user, statement, "ERROR: " + type(error).__name__, function_name)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n") 
            nodes = []
            break
        except SessionExpired as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")            

            messageforuser = f"********** {user} try: {trying} -> X X X X X X X X X X X X Session Expired X X X X X X X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 01"
            messageforuser += "\n\ndetail message: " + detailmessage
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)
            continue
        except WriteServiceUnavailable as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")

            messageforuser = f"********** {user} try: {trying} -> X X X X X X X X X X X WriteServiceUnavailable X X X X X X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 01-5"
            messageforuser += "\n\ndetail message: " + detailmessage    
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)
            continue
        except SessionError as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")
            messageforuser = f"********** {user} try: {trying} -> X X X X X X X X X X X X Session Error X X X X X X X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 02"
            messageforuser += "\n\ndetail message: " + detailmessage   
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)          
            continue
        except ServiceUnavailable as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")
            messageforuser = f"********** {user} try: {trying} -> X X X X X X X X X X X X Service Unavailable X X X X X X X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 03"
            messageforuser += "\n\ndetail message: " + detailmessage
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)
            continue        
        except ResultError as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")
            messageforuser = f"********** {user} try: {trying} -> X X X X X X X X X X X X Result Error X X X X X X X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 04"
            messageforuser += "\n\ndetail message: " + detailmessage
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)
            continue
        except Exception as error:
            appNeo.close()
            print("Exception:", type(error).__name__, error)
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")
            messageforuser = f"********** {user} try: {trying} -> X X X X X An error occurred executing X X X X"
            messageforuser = type(error).__name__ + "\n\n" + str(type(error)) + "\n\n" + messageforuser
            detailmessage="Service Unavailable - Conexion Error - 99"
            messageforuser += "\n\ndetail message: " + detailmessage
            sleep(2)
            timeforneo4jdriver = recovery_from_neo4jexception(user, statuserror, detailmessage, messageforuser)
            continue
    if statuserror != 200:
        print("====> SERVICE UNAVAILABLE")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detailmessage            
        )
    return nodes

def neo4_log(session, user, log_description, filename= None, function_name=None, log=[0,""]):
    #if True == False:
    if not function_name:
        function_name = 'null'
    else:
        function_name = "'" + function_name + "'"
    #print(f"lllog_description: {log_description}")
    log_description = log_description.replace('"', '')
    logofaccess = 'create (n:Log {user: "' + user + '", ' + \
                    'trx: "' + log_description + '", \n' + \
                    'exec_fname: "' + filename + '", \n' + \
                    "exec_fn:" + function_name + ", \n" + \
                    "ctInsert: datetime()})" + \
                    "return elementId(n) as idLog, n.ctInsert as dtstamp"
    # "return id(n) as idLog, n.ctInsert as dtstamp"
    #log = session.run(logofaccess)

    log = execution(function_name, logofaccess, user, log)
    ix = [dict(ix) for ix in log][0]
    idlog = ix["idLog"]
    dtstamp = ix["dtstamp"]
    #else:
    #    idlog = 1 # ix["idLog"]
    #    dtstamp = dt.now() # ix["dtstamp"]
    
    return [idlog, dtstamp]

def neo4j_exec(session, user, log_description, statement, filename= None, function_name=None, recLog=True):
    global appNeo

    if not function_name:
        function_name = 'null'
    #print(f"execution requested by {user} - FUNTION__NAME: {function_name}")
    # next line is the log's record for the user's execution

    #print("\n\n**********", user, "----> recording logs - the beginning" , function_name)
    log = [None,""]
    if monitoring_function(function_name):
        log_description += "\n----\n" + statement[0:15] + " ... " + statement[-15:] + "\n----\n"
        if recLog:
            log = neo4_log(session, user, log_description, filename, function_name)    
    #print("**********", user, "-", log[0], "->           finaliza ejecución en neo4_exec", function_name, type(nodes))

    nodes = execution(function_name, statement, user, log)
    
    #print("********** recording the end of transaction", user, "-", log[0] -> ", str(log[1]))
    if log[0]:
        statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + user + "'}) \n" + \
                    "where elementId(l) = '" + log[0] + "' \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        execution(function_name, statement, user, log)
        #print("*********************** log's record - the end" , function_name)
    
    return nodes, log

def get_sugcategories(session, user):
    ne04j_statement = "match (scat:SubCategory) return scat.idCat, scat.idSCat, scat.name"    
    nodes, log = neo4j_exec(session, user,
                            log_description='getting subcategories',
                            statement=ne04j_statement
                            )
    scatdic = {}
    for node in nodes:
        nodedic = dict(node)
        #print(nodedic["scat.idCat"], nodedic["scat.idSCat"], nodedic["scat.name"])
        scatdic[nodedic["scat.idSCat"]] =  nodedic["scat.name"]
    return scatdic


# login de usuario
def login_validate_user_pass_trx_borrar(session, login):
    def login_validate_user_pass(session, login):        
        query = "create (l:Log {user:$login, ctInsert:datetime(), ctClosed: datetime(), "+ \
                        "trx:'trying login for the user', \n" + \
                        "exec_fname:'" + __name__+ "', \n"+ \
                        "exec_fn: 'login_validate_user_pass_trx'}) " + \
                "with l.user as userId \n" + \
                "match (us:User {userId: userId }) " +  \
                "return us.userId, us.name, us.keypass, us.age, \n" + \
                    "us.nativeLang, us.country_birth, us.country_res limit 1"
        nodes = session.run(query, login=login)
        return nodes

    resp = login_validate_user_pass(session, login)
    #print(f"resp: {type(resp)} {resp}")
    result = {}
    for elem in resp:
        result=dict(elem) #print(f"elem: {type(elem)} {elem}")        
    return result 

# chage user password
def user_change_password_borrar(session, login, old_pass, new_pass, filename=None, function_name=None):
    def change_pass(session, login, old_pass, new_pass):        
        query = "match (us:User {userId: $login, keypass: $oldpass}) \n" +  \
                "set us.keypass = $newpass \n" + \
                "return us.userId, us.keypass limit 1"
        
        nodes = session.run(query, login=login, oldpass = old_pass, newpass = new_pass)
        return nodes

    resp = change_pass(session, login, old_pass, new_pass)
    result = {}
    for elem in resp:
        #print(f"elem: {type(elem)} {elem}")     
        result=dict(elem)
    #print('chagnepasswrod:', result)

    if len(result) == 0:
        trx = "Incorrect user or password"
    else:
        trx = "Password updated"
    
    log = neo4_log(session, login, "Updating password - " + trx, filename, function_name)
    """
    q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + login + "'}) \n" + \
                "where id(l) = " + str(log[0]) + " \n" + \
                "set l.ctClosed = datetime() \n" + \
                "return count(l)"
    )
    """
    return result

def create_new_word_sound(tx, session, word, bfield):
    #print(f"\nsession: {session} \n")
    tx.run("merge (ws: word_sound {word:$updateword}) set ws.binfile=$newfile,ws.actived='yes' ", 
                    updateword = word, newfile = bfield)
    
def unload_word_sound(tx, session, word):
    #print(f"\nsession: {session} \n")
    tx.run("match (ws: word_sound {word:$updateword}) return ws.binfile", 
                updateword = word) #, newfile = bfield)
    

def transaction_newsound(app, word, bfield):
    with app.driver.session() as session:
        session.write_transaction(create_new_word_sound, session, word, bfield)

def transaction_unloadsound(app, word):
    with app.driver.session() as session:
        session.write_transaction(unload_word_sound, session, word)
        

def main():
    pass

if __name__ == main:
    pass

"""
examples:
trans_forexec = []
for i in range(0,10):
	neo4jstatement = “create (t:Label {t_id:” + str(i)  + “, name:” + lname + “})”
	trans_forexec.append(neo4jstatement)

def execute_trans(transcommands):
	dbconnection = graphDatabase.driver(url = ‘’, auth=(‘neo4j’, ‘password’))
	session = dbconnection.session()
	for i in transcommands:
		session.run(i)

execute_trans(trans_forexec)
"""
