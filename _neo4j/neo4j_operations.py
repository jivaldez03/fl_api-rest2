from neo4j import GraphDatabase 
from __generalFunctions import monitoring_function

"""
https://neo4j.com/docs/python-manual/current/transformers/

import neo4j

pandas_df = driver.execute_query(
    "UNWIND range(1, 10) AS n RETURN n, n+1 as m",
    database_="neo4j",
    result_transformer_=neo4j.Result.to_df
)
"""
def q01(session, strtoexec= None):
    if strtoexec == None:
        q01 = 'match (n:English)-->(s:Spanish) return n.word, s.word'
    else:
        q01 = strtoexec        
    nodes = session.run(q01)
    return nodes

def neo4_log(session, user, log_description, filename= None, function_name=None):
    if not function_name:
        function_name = 'null'
    else:
        function_name = "'" + function_name + "'"
    logofaccess = 'create (n:Log {user: "' + user + '", ' + \
                    'trx: "' + log_description + '", \n' + \
                    'exec_fname: "' + filename + '", \n' + \
                    "exec_fn:" + function_name + ", \n" + \
                    "ctInsert: datetime()})" + \
                    "return id(n) as idLog, n.ctInsert as dtstamp"
    log = session.run(logofaccess)

    ix = [dict(ix) for ix in log][0]
    #idlog = [dict(ix)['idLog'] for ix in log][0]
    idlog = ix["idLog"]
    dtstamp = ix["dtstamp"]
    #print('recordlog for ', function_name ,': ', idlog, dtstamp)
    
    return [idlog, dtstamp]

def neo4j_exec(session, user, log_description, statement, filename= None, function_name=None):

    if not function_name:
        function_name = 'null'
    
    # next line is for the log record for the user's execution
    if monitoring_function(function_name):
        log_description += "\n----\n" + statement
    
    try:
        log = neo4_log(session, user, log_description, filename, function_name)
    except Exception as error:
        print("An error occurred recording log:", log_description, "\n\n",  type(error).__name__, " - ", error)
        log = [-1,""]                 
        #sleep(60) 
    #executing operation
    try:
        nodes = session.run(statement)
    except Exception as error:
        print("An error occurred executing:" , statement, "\n\n", type(error).__name__, " - ", error)
        nodes = []

    print("log's values: ", log)    
    """
    if log[0] > 0:
        q01(session, "match (l:Log {ctInsert:datetime('" + str(log[1]) + "'), user:'" + user + "'}) \n" + \
                    "where id(l) = " + str(log[0]) + " \n" + \
                    "set l.ctClosed = datetime() \n" + \
                    "return count(l)"
        )
    """
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
        print(nodedic["scat.idCat"], nodedic["scat.idSCat"], nodedic["scat.name"])
        scatdic[nodedic["scat.idSCat"]] =  nodedic["scat.name"]
    return scatdic


# login de usuario
def login_validate_user_pass_trx(session, login):
    def login_validate_user_pass(session, login):        
        query = "create (l:Log {user:$login, ctInsert:datetime(), "+ \
                        "trx:'trying login for the user', \n" + \
                        "exec_fname:'" + __name__+ "', \n"+ \
                        "exec_fn: 'login_validate_user_pass_trx'})" + \
                "with l.user as userId \n"+ \
                "match (us:User {userId: $login}) " +  \
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
    print('chagnepasswrod:', result)

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
    print(f"\nsession: {session} \n")
    tx.run("merge (ws: word_sound {word:$updateword}) set ws.binfile=$newfile,ws.actived='yes' ", 
                    updateword = word, newfile = bfield)
    
def unload_word_sound(tx, session, word):
    print(f"\nsession: {session} \n")
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
