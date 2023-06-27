from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs # import reg_exp as rexp #  as funcs^(lev([0-9][0-9])(_)([09][0-9]))$
from __generalFunctions import myfunctionname, _getdatime_T

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

    #validating if level is valid, if it isn't valid the raise and error 406 raise HTTPException HTTP_406_NOT_ACCEPTABLE
    levelSeqPosition = funcs.validating_exist_level(level)
    if levelSeqPosition == 1:  # level in position 1 is equal to lvl_10_01, if it is.... clickqty = cardsqty
        clicksQty = cardsQty
    if clicksQty < cardsQty:
        clicksQty = cardsQty * 2
    gradeval = (float(clicksQty) / cardsQty - 1) * 100  # 10 / 8 = 1.25 - 1 = .25 * 100 = 25
        
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', userId:'" + userId + "'}) " + \
                    "create (pkgS:PackageStudy {studing_dt:datetime('" + updtime + "')})-[rs:STUDY]->(pkg) " + \
                    "set pkgS.level = '" + level + "', \n" + \
                        "pkgS.grade = [" + str(clicksQty) + "," + str(cardsQty) + "], \n" + \
                        "pkgS.ptgerror = " + str(gradeval) + " \n" + \
                    "return pkg.packageId as packageId, pkgS.studing_dt, \n" + \
                         "pkgS.level as level, pkgS.grade as grade, pkgS.ptgerror as ptgerror"
    nodes, log = neo4j_exec(session, userId,
                        log_description="updating activity on package = '" + pkgname + "'\nlevel = '" + level + "'" + \
                                    "\npkgS.grade = [" + str(clicksQty) + "," + str(cardsQty) + "]",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    listcat = []
    for node in nodes:
        sdict = dict(node)
        if sdict.get("ptgerror",100) <= 15: 
            sdict["status"] = True
            sdict["message"] = ""
        else:
            sdict["status"] = False
            sdict["message"] = ""
        listcat.append(sdict)
        
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())        
    return {'message': listcat}

