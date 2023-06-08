from fastapi import APIRouter, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs # import reg_exp as rexp #  as funcs^(lev([0-9][0-9])(_)([09][0-9]))$

from app.model.md_params_oper import ForClosePackages

router = APIRouter()

@router.post("/level/")
def post_level(datas:ForClosePackages, Authorization: Optional[str] = Header(None)):
    """
    Function to record each task in the frontend

    {\n
        level:str , \n
        package:str (pkgname), \n
        upddtime: str ("2023-06-07T14:05:31.237751"), \n
        clicksQty: int (quantity of clicks) ,\n
        cardsQty : int (quantity of cards), \n
    }

    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']    

    level = datas.level
    pkgname = datas.package
    updtime = datas.updtime
    clicksQty= datas.clicksQty
    cardsQty = datas.cardsQty

    print('levelclick:', level, clicksQty, cardsQty)
    if funcs.level_seq(level, forward=False, position=True) == 1:
        clicksQty = cardsQty
    print('levelclick2:', level, clicksQty, cardsQty)
    """
    if not rexp("^(lev([0-9][0-9])(_)([09][0-9]))$", level):
        #listcat = []
        #return {'message': listcat}
        pass
    """
    #"with 'jivaldez03' as user_id,  "
                      #  "'2023-05-17T18:32:37.490051' as pkgId,  "
                      #  "'2023-05-18T14:12:30' as dtexec,  "
                      #  "'lvl01.01' as lvl, [12,8] as grade "
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', userId:'" + userId + "'}) " + \
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

