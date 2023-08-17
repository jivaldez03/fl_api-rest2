from neo4j import GraphDatabase
from .config import Config as cfg, Configp as cfgp, get_pass, kodb

class App:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()
    """
    def create_friendship(self, person1_name, person2_name):
        print('create friendship')
        with self.driver.session(database="neo4j") as session:
            # Write transactions allow the driver to handle retries and transient errors
            print('with ----------------')
            result = session.execute_write(
                self._create_and_return_friendship, person1_name, person2_name)
            for row in result:
                print("Created friendship between: {p1}, {p2}".format(p1=row['p1'], p2=row['p2']))

    @staticmethod
    def _create_and_return_friendship(tx, person1_name, person2_name):
        # To learn more about the Cypher syntax, see https://neo4j.com/docs/cypher-manual/current/
        # The Reference Card is also a good resource for keywords https://neo4j.com/docs/cypher-refcard/current/
        query = (
            "CREATE (p1:Person { name: $person1_name }) "
            "CREATE (p2:Person { name: $person2_name }) "
            "CREATE (p1)-[:KNOWS]->(p2) "
            "RETURN p1, p2"
        )
        result = tx.run(query, person1_name=person1_name, person2_name=person2_name)
        try:
            return [{"p1": row["p1"]["name"], "p2": row["p2"]["name"]}
                    for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

    def find_person(self, person_name):
        with self.driver.session(database="neo4j") as session:
            result = session.execute_read(self._find_and_return_person, person_name)
            for row in result:
                print("Found person: {row}".format(row=row))

    @staticmethod
    def _find_and_return_person(tx, person_name):
        query = (
            "MATCH (p:Person) "
            "WHERE p.name = $person_name "
            "RETURN p.name AS name"
        )
        result = tx.run(query, person_name=person_name)
        return [row["name"] for row in result]

    """

""" def create_neo4j_app():
    app = App(cfg.URI, cfg.USERNAME, cfg.SECRET_KEY)
    return app, app.driver.session(database="neo4j")
 """

def create_neo4j_app():
    if kodb() == 1:
        SECRET_KEY = get_pass(cfg.USERNAME)
        #print(SECRET_KEY, cfg.URI, cfg.USERNAME, SECRET_KEY)
        #input ("cr to continue Ctrl to interrupt")
        app = App(cfg.URI, cfg.USERNAME, SECRET_KEY)
    elif kodb() == 2: 
        SECRET_KEY = get_pass(cfgp.USERNAME)
        #print(SECRET_KEY, cfgp.URI, cfgp.USERNAME, SECRET_KEY)
        #input ("cr to continue Ctrl to interrupt")
        app = App(cfgp.URI, cfgp.USERNAME, SECRET_KEY)
    #print(f'creating objet Neo4j App:  {app}')
    return app, app.driver.session(database="neo4j")

def connectNeo4j(user, description):
    #uri = 'neo4j://localhost:7687'
    #driver = GraphDatabase.driver(uri, auth=('neo4j', 'sistemas'))
    #session = driver.session()
    app,session = create_neo4j_app()
    logofaccess = "create (n:Log {user: '" + user + "', trx: '" + description + "'}) " \
                            "set n.ctInsert = datetime() " \
                            "return n"
    log = session.run(logofaccess)
    #input ("you can review the log record for user admin - cr to continue Ctrl to interrupt")
    #print('type-log:', type(log))
    #for x in log:
    #    print('log:', x)
    return app, session, log

#app = create_neo4j_app() # create_app()

print(f"\n\n************************\nconexión a neo4j\n************************")
user = 'admin'
#print("\n\n========== kodb: ", kodb(), "\n\n")
#input ("cr to continue Ctrl-c to interrupt ")

appNeo, session, log = connectNeo4j(user, 'starting session')
timeout_const = 300


