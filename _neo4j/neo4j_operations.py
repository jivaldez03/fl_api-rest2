from neo4j import GraphDatabase

def q01(session):
    q01 = 'match (n:English)-->(s:Spanish) return n.word, s.word'
    nodes = session.run(q01)
    #print(type(nodes))
    #for node in nodes:
    #    print(node, type(node))
    return nodes

def neo4j_exec(session, user, log_description, statement):
    logofaccess = 'create (n:Log {user: "' + user + '", trx: "' + \
                    log_description + '"}) set n.ctInsert = datetime() return n'
    log = None # session.run(logofaccess)
    # print('neo4jStatement: ', statement)
    nodes = session.run(statement)
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
def login_validate_user_pass_trx(session, login, keypass):
    def login_validate_user_pass(session, login):        
        query = "match (us:User {userId: $login}) " +  \
                "return us.userId, us.name, us.keypass, us.age,  us.country_birth, us.country_res limit 1"
        """
        session.run("CREATE (a:Person {name: $name})", parameters("name", name));
        result = tx.run(query, {"name": "Alice", "age": 33})
        result = tx.run(query, {"name": "Alice"}, age=33)
        result = tx.run(query, name="Alice", age=33)
        """
        nodes = session.run(query, login=login)
        return nodes

    resp = login_validate_user_pass(session, login)
    #print(f"resp: {type(resp)} {resp}")
    result = {}
    for elem in resp:
        result=dict(elem) #print(f"elem: {type(elem)} {elem}")        
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
