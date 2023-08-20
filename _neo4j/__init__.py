from neo4j import GraphDatabase #, TrustAll
from .config import Config as cfg, Configp as cfgp, get_pass, kodb
from datetime import datetime as dt, timedelta as delta
from time import sleep
from __generalFunctions import _getenv_function

class App:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password)
                                           #, trusted_certificates=TrustAll()
                                           , max_connection_lifetime = 3600  # segundos 1  horas
                                           , max_connection_pool_size = 12      # workers - workstation
                                           , max_transaction_retry_time = timeout_const
                                           , keep_alive=True
                                        )

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
    global timeforneo4jdriver
    if kodb() == 1:
        SECRET_KEY = get_pass(cfg.USERNAME)
        app = App(cfg.URI, cfg.USERNAME, SECRET_KEY)
    elif kodb() == 2: 
        SECRET_KEY = get_pass(cfgp.USERNAME)
        app = App(cfgp.URI, cfgp.USERNAME, SECRET_KEY)
    timeforneo4jdriver = dt.now() + delta(minutes=int(_getenv_function('MINS_FOR_RECONNECT')))
    session = app.driver.session(database="neo4j")
    return app, session

def connectNeo4j(user, description):
    app,session = create_neo4j_app()
    logofaccess = "create (n:Log {user: '" + user + "', trx: '" + description + "'}) " \
                            "set n.ctInsert = datetime() " \
                            "return n"
    log = session.run(logofaccess)
    return app, session, log

#app = create_neo4j_app() # create_app()

print(f"\n\n************************\nconexión a neo4j\n************************")
user = 'admin'
timeout_const = 120
timeforneo4jdriver = dt.now() + delta(minutes=int(_getenv_function('MINS_FOR_RECONNECT')))
sleep(2)
appNeo, session, log = connectNeo4j(user, 'starting session with reconnect at ', timeforneo4jdriver)




