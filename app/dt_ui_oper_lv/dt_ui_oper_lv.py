from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs # import reg_exp as rexp #  as funcs^(lev([0-9][0-9])(_)([09][0-9]))$
from __generalFunctions import myfunctionname, _getdatime_T, _getdatetime
#from dt_ui_oper_gr.dt_ui_oper_bs import get_w_SCat
from ..dt_ui_oper_gr.dt_ui_oper_bs import get_w_SCat

from app.model.md_params_oper import ForClosePackages

from asyncio import sleep as awsleep

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

router = APIRouter()

@router.post("/level/")
async def post_level(datas:ForClosePackages, Authorization: Optional[str] = Header(None)):
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
    
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', status:'open', \n" + \
                        "userId:'" + userId + "'}) \n" + \
                    "create (pkgS:PackageStudy {studing_dt:datetime('" + updtime + "')})-[rs:STUDY]->(pkg) \n" + \
                    "set pkgS.level = '" + level + "', \n" + \
                        "pkgS.grade = [" + str(clicksQty) + "," + str(cardsQty) + "], \n" + \
                        "pkgS.ptgerror = " + str(gradeval) + ", \n" + \
                        "pkgS.ctInsert = datetime() \n" + \
                    "set pkg.ctUpdate = datetime() \n" + \
                    "return pkg.packageId as packageId, pkgS.studing_dt, \n" + \
                         "pkgS.level as level, pkgS.grade as grade, pkgS.ptgerror as ptgerror"
    
    await awsleep(0)

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


async def set_archived_package(packagename, userId):
    """
    Function to closed and add package words to the user's learned words
    """
    # getting the internal code for subcat 
    wSCat = get_w_SCat (userId, packagename)
    wSCat, source, target = wSCat  # subcategoria w_SC_10000053, source, target del paquete
    #source = wSCat[1]

    dtimenow = _getdatetime()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = dtimenow.strftime("%W") # , status:'open'

    neo4j_statement = "with '" + packagename + "' as pkgname, \n" + \
                        "'" + userId + "' as userId, \n" + \
                        str(yearr) + " as yearr, \n" + \
                        str(monthh) + " as monthh, \n" + \
                        str(weekk) + " as weekk, \n" + \
                        "'" + source + "' as psource \n" + \
                        "match (sc:SubCategory)<-[:PACK_SUBCAT]-\n" + \
                        "(p:Package {packageId:pkgname, userId:userId, status:'open'}) \n" + \
                        "-[:PACKAGED]->(u:User {userId:userId}) \n" + \
                        "set p.status = 'closed', p.ctUpdate = datetime(), \n" + \
                        "  p.ctArchived = datetime(), \n" + \
                        "  p.ctArchivedYear = yearr, \n" + \
                        "  p.ctArchivedMonth = monthh, \n" + \
                        "  p.ctArchivedWeekYear = weekk \n" + \
                        "merge (rofArc:Archived_W:" + source + ":"+ target + " " + \
                            "{userId:u.userId, year:yearr, month:monthh, week:weekk, " + \
                                "source:'" + source + "', target:'" + target + "', \n" + \
                                    "idCat:p.idCat, idSCat:p.idSCat}) \n" + \
                        "on create set rofArc.week_qty = 0, rofArc.words=[], rofArc.ctInsert = datetime() \n" + \
                        "on match set rofArc.ctUpdate = datetime() \n" + \
                        "set rofArc.words = rofArc.words + [ele in p.words where not ele in rofArc.words] \n" + \
                        "set rofArc.week_qty = size(rofArc.words) \n" + \
                        "merge (u)<-[rArc:ARCHIVED_W]-(rofArc) \n" + \
                        "on create set rArc.ctInsert = datetime() \n" + \
                        "on match set rArc.ctUpdate = datetime() \n" + \
                        "merge (p)-[rArcP:PACK_ARCHIVED_W]->(rofArc) \n" + \
                        "on create set rArcP.ctInsert = datetime() \n" + \
                        "on match set rArcP.ctUpdate = datetime() \n" + \
                        "merge (sc)<-[rArcS:SUBCAT_ARCHIVED_W]-(rofArc) \n" + \
                        "on create set rArcS.ctInsert = datetime() \n" + \
                        "on match set rArcS.ctUpdate = datetime() \n" + \
                        "merge (ArcM:Archived_M:" + source + ":"+ target + " " + \
                            "{userId:u.userId, year:yearr, month:monthh, " + \
                                "source:'" + source + "', target:'" + target + "', \n" + \
                                    "idCat:p.idCat, idSCat:p.idSCat}) \n" + \
                        "on create set ArcM.month_qty = 0, ArcM.words=[], ArcM.ctInsert = datetime() \n" + \
                        "on match set ArcM.ctUpdate = datetime() \n" + \
                        "set ArcM.words = ArcM.words + [ele in p.words where not ele in ArcM.words] \n" + \
                        "set ArcM.month_qty = size(ArcM.words) \n" + \
                        "merge (rofArc)-[rWM:WEEK_MONTH]->(ArcM) \n" + \
                        "merge (sc)<-[rSArcM:SUBCAT_ARCHIVED_M]-(ArcM) \n" + \
                        "merge (u)<-[rUArcM:ARCHIVED_M]-(ArcM) \n" + \
                        "return p.packageId as packageId , p.label as slabel, p.status as status " 
    # filter (x in n.A where x<>"newValue")
    # "ArcM.words = ArcM.words + p.words \n" + \
    #print('archiving: ", neo4j_statement')
    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="archive package" + packagename,
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    res = {"message" : "ERROR - INVALID OPERATION", 
           "packageId": None, 
           "label":None, 
           "status":None
           }
    for node in nodes:
        #print(f"ciclo de nodes")
        sdict = dict(node)
        res = {'packageId': sdict["packageId"], "label":sdict["slabel"], "status":sdict["status"]}
        res["message"] = "-- SUCCESSFUL OPERATION --"
    return res


@router.post("/pst_/packagearchive/")
async def pst_packagearchive(package:str
                    , Authorization: Optional[str] = Header(None)):
    """
    Function change the package's label \n    
    
    {\n
        package:str=None
    }
    """
    global appNeo, session

    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    await awsleep(0)
    
    print("\n\n\n","="*30, "se ejecuta cierre de package")

    res = set_archived_package(package, userId)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return res

