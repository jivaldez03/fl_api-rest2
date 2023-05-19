from fastapi import APIRouter
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
#import __generalFunctions as funcs

router = APIRouter()


@router.post("/level/{user_id} {pkgname} {updtime} {level} {clicksQty} {cardsQty}")
def post_level(user_id, pkgname:str, updtime:str, level:str, clicksQty:int, cardsQty:int):
    global appNeo, session, log, user
    #"with 'jivaldez03' as user_id,  "
                      #  "'2023-05-17T18:32:37.490051' as pkgId,  "
                      #  "'2023-05-18T14:12:30' as dtexec,  "
                      #  "'lvl01.01' as lvl, [12,8] as grade "
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', userId:'" + user_id + "'}) " + \
                    "merge (pkgS:PackageStudy {studing_dt:datetime('" + updtime + "')})-[rs:STUDY]->(pkg) " + \
                    "set pkgS.level = '" + level + "', pkgS.grade = [" + str(clicksQty) + "," + str(cardsQty) + "]" + \
                    "return pkg.packageId as packageId, pkgS.studing_dt, pkgS.level as level, pkgS.grade as grade"
    nodes, log = neo4j_exec(session, user,
                        log_description="updating package study level",
                        statement=neo4j_statement)
    listcat = []
    for node in nodes:
        listcat.append(dict(node))
    return {'message': listcat}

