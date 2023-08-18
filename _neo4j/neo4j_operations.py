from neo4j import Query #, GraphDatabase, Result, unit_of_work #neo4j._sync.work.result.Result
from __generalFunctions import monitoring_function
from neo4j.exceptions import SessionExpired, SessionError, ServiceUnavailable, ResultError
#Neo4j.Driver.SessionExpiredException error
from _neo4j import appNeo, session, log, connectNeo4j, timeout_const
from time import sleep
from datetime import datetime as dt
from fastapi import HTTPException, status
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

def q01(session, strtoexec= None):
    if strtoexec == None:
        q01 = 'match (n:English)-->(s:Spanish) return n.word, s.word'
    else:
        q01 = strtoexec        
    nodes = session.run(q01, timeout = timeout_const)
    return nodes

#@unit_of_work(timeout=timeout_const)  # seconds
def execution(function_name, statement, user, log):
    global appNeo, session

    # next loop exist only if we have an error about our session, it try to reconnect again
    trying = 0
    statuserror = 200
    detailmessage = ""
    messageforuser = ""
    while trying < 4:
        trying += 1        
        try:
            #print("*********************** inicia ejecución en neo4_exec " , function_name)
            #nodes = session.run(statement, timeout=timeout_const)
            nodes = session.run(Query(statement, timeout=timeout_const), name='query')
            statuserror = 200
            
            #print("*********************** finaliza ejecución en neo4_exec", function_name, type(nodes))
            break
        except SessionExpired as error:
            print(f"\nappNeo: {appNeo} \nSesion: {session}\n")
            print("**********", user, "-", log[0], "try:", trying, " -> X X X X X X X X X X X X session expired X X X X X X X X X X ")
            detailmessage="Service Unavailable - Conexion Error - 01"
            messageforuser = "Service Unavailable - Conexion Error - 01"
            reconect_neo4j(user)
            statuserror = 503
            #sleep(2)
            continue
        except SessionError as error:
            print("**********", user, "-", log[0], "try:", trying,  " ->  X X X X X X X X X X X X session error X X X X X X X X X X ")
            reconect_neo4j(user)
            detailmessage="Service Unavailable - Conexion Error - 02"
            messageforuser = "Service Unavailable - Conexion Error - 02"
            #sleep(2)
            statuserror = 503
            continue    
        except ServiceUnavailable as error:
            print("**********", user, "-", log[0], "try:", trying, " -> X X X X X X X X X X X X service unavailable X X X X X X X X X X ")
            sleep(2)
            reconect_neo4j(user)
            detailmessage="Service Unavailable - Conexion Error - 03"
            messageforuser = "Service Unavailable - Conexion Error - 03"
            statuserror = 503
            continue
        except ResultError as error:
            print("**********", user, "-", log[0], "try:", trying, " -> X X X X X X X X X X X X result error  X X X X X X X X X X ")
            sleep(2)
            reconect_neo4j()
            statuserror = 503
            detailmessage = "Service Unavailable - Conexion Error - 04"
            messageforuser = "Service Unavailable - Conexion Error - 04"
            continue
        except Exception as error:
            print("**********", user, "-", log[0], "try:", trying, " -> An error occurred executing:" , statement, "\n\nerror ", type(error).__name__, " - ", error)
            print("exception as : ", Exception)
            detailmessage = "Service Unavailable - Conexion Error - 99"
            messageforuser = "Service Unavailable - Conexion Error - 99"
            statuserror = 503
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
                    "return id(n) as idLog, n.ctInsert as dtstamp"
    #log = session.run(logofaccess)

    log = execution(function_name, logofaccess, user, log)
    ix = [dict(ix) for ix in log][0]
    idlog = ix["idLog"]
    dtstamp = ix["dtstamp"]
    #else:
    #    idlog = 1 # ix["idLog"]
    #    dtstamp = dt.now() # ix["dtstamp"]
    
    return [idlog, dtstamp]

def neo4j_exec(session, user, log_description, statement, filename= None, function_name=None):
    global appNeo

    if not function_name:
        function_name = 'null'
    #print(f"execution requested by {user} - FUNTION__NAME: {function_name}")
    # next line is the log's record for the user's execution
    if monitoring_function(function_name):
        log_description += "\n----\n" + statement
    #print("\n\n**********", user, "----> recording logs - the beginning" , function_name)
    log = [-1,""]
    log = neo4_log(session, user, log_description, filename, function_name)    

    #print("**********", user, "-", log[0], "->           inicia ejecución en neo4_exec " , function_name)

    nodes = execution(function_name, statement, user, log)
    
    #print("**********", user, "-", log[0], "->           finaliza ejecución en neo4_exec", function_name, type(nodes))
        
    #print("**********", user, "-", log[0], "-> recording logs - the end for log's at: ", str(log[1]))
    if log[0] > 0:
        statement = "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + user + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        execution(function_name, statement, user, log)
        #print("*********************** log's record - the end" , function_name)
    
    return nodes, log


def neo4j_exec_back_borrar(session, user, log_description, statement, filename= None, function_name=None):
    global appNeo

    if not function_name:
        function_name = 'null'
    
    # next line is for the log record for the user's execution
    if monitoring_function(function_name):
        log_description += "\n----\n" + statement
    
    log = [-1,""]
    trying = 0
    while trying < 4:
        trying += 1
        # recording log - the beginning of the transaction
        try:
            log = neo4_log(session, user, log_description, filename, function_name)
            #pass
        except Exception as error:
            print("An error occurred recording log:", log_description, "->",  type(error).__name__, " - ", error)
            log = [-1,""]
        # process the transaction or request
        try:
            print("*********************** inicia ejecución en neo4_exec " , function_name)
            nodes = session.run(statement)
            print("*********************** finaliza ejecución en neo4_exec", function_name, type(nodes))
            break
        except SessionExpired as error:
            print("X X X X X X X X X X X X session expired X X X X X X X X X X ")
            sleep(2)
            reconect_neo4j()
            continue
        except SessionError as error:
            print("X X X X X X X X X X X X session error X X X X X X X X X X ")
            sleep(2)
            reconect_neo4j()
            continue    
        except ServiceUnavailable as error:
            print("X X X X X X X X X X X X service unavailable X X X X X X X X X X ")
            sleep(3)
            reconect_neo4j()
            continue
        except ResultError as error:
            print("X X X X X X X X X X X X result error  X X X X X X X X X X ")
            #reconect_neo4j()
            sleep(1)
            continue
        except Exception as error:
            print("An error occurred executing:" , statement, "\n\nerror ", type(error).__name__, " - ", error)
            print("exception as : ", Exception)        
        # recording log - the end of the transaction
        print("log's values: ", log)        
        if log[0] > 0:
            q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + user + "'}) \n" + \
                        "where id(l) = " + str(log[0]) + " \n" + \
                        "set l.ctClosed = datetime() \n" + \
                        "return count(l)"
            )
        
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
def login_validate_user_pass_trx(session, login):
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
def user_change_password(session, login, old_pass, new_pass, filename=None, function_name=None):
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
    q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + login + "'}) \n" + \
                "where id(l) = " + str(log[0]) + " \n" + \
                "set l.ctClosed = datetime() \n" + \
                "return count(l)"
    )
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
