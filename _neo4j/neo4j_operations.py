from neo4j import GraphDatabase
from _neo4j import create_neo4j_app as App


def connectNeo4j(user, description):
    #uri = 'neo4j://localhost:7687'
    #driver = GraphDatabase.driver(uri, auth=('neo4j', 'sistemas'))
    #session = driver.session()
    app,session = App()
    logofaccess = "create (n:Log {user: '" + user + "', trx: '" + description + "'}) " \
                            "set n.ctInsert = datetime() " \
                            "return n"
    log = session.run(logofaccess)
    #print('type-log:', type(log))
    #for x in log:
    #    print('log:', x)
    return app, session, log

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
