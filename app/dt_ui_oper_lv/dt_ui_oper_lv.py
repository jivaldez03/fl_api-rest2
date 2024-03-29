from fastapi import APIRouter, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs # import reg_exp as rexp #  as funcs^(lev([0-9][0-9])(_)([09][0-9]))$
from __generalFunctions import myfunctionname, _getdatime_T, _getdatetime

#from ..dt_ui_oper_gr.dt_ui_oper_bs import get_w_SCat

from app.model.md_params_oper import ForClosePackages

from asyncio import sleep as awsleep

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

router = APIRouter()


def get_w_SCat(userId, pkgname):
    #print("========== starting get_w_SCat id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    neo4j_statement = "match (pkg:Package {userId:'" + userId + "', packageId:'" + pkgname + "'})\n" + \
            "return pkg.source as pkgsource, pkg.target as pkgtarget, \n" + \
                "pkg.idSCat as idSCat, pkg.idCat as idCat"    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting new words (step 1) for new package",
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    pkgsource, pkgtarget, idCat, idSCat = "","","",""
    for node in nodes:
        print("leyendo nodes")
        sdict = dict(node)
        pkgsource = sdict["pkgsource"]
        pkgtarget = sdict["pkgtarget"]
        idCat = sdict["idCat"]
        idSCat = sdict["idSCat"]    
    #print("\n\n\n","="*50,"wsCat =", wSCat, idCat, idSCat)
    #print("        ->   ========== ending get_w_SCat id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())

    return [pkgsource, pkgtarget, idCat, idSCat]

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
                    "set pkg.ctUpdate = datetime(), \n" + \
                    " pkg.level = case when pkgS.level > coalesce(pkg.level,'lvl_00_00') and pkgS.ptgerror < 15.0 \n" + \
                                        "then pkgS.level else pkg.level end \n " + \
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


def set_archived_package(packagename, userId):
    # ESTA FUNCION NO PUEDE SER ASYNC 
    """
    Function to closed and add package words to the user's learned words
    """
    # getting the internal code for subcat 
    wSCat = get_w_SCat (userId, packagename)
    source, target = wSCat[0], wSCat[1]  # [source, target, idCat, idSCat] del paquete
    #source = wSCat[1]
    if wSCat[2] == 1 and wSCat[3] == 1:
        subcat = 'Word'
        relationship = "PRONUNCIATION"
    else:
        subcat = 'ElemSubCat'
        relationship = "PRONUNCIATION_PV"

    dtimenow = _getdatetime()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = int(dtimenow.strftime("%W")) # , status:'open'

    neo4j_statement = "with '" + packagename + "' as pkgname, \n" + \
                        "'" + userId + "' as userId, \n" + \
                        str(yearr) + " as yearr, \n" + \
                        str(monthh) + " as monthh, \n" + \
                        str(weekk) + " as weekk, \n" + \
                        "'" + source + "' as psource \n" + \
                        "match (sc:SubCategory)<-[:PACK_SUBCAT]-\n" + \
                        "(p:Package {packageId:pkgname, userId:userId, status:'open'}) \n" + \
                        "-[:PACKAGED]->(u:User {userId:userId}) \n" + \
                        "where p.level >= 'lvl_40_01' \n" + \
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
                        "on create set ArcM.month_qty = 0, ArcM.words=[], ArcM.sentences=[], ArcM.ctInsert = datetime() \n" + \
                        "on match set ArcM.ctUpdate = datetime() \n" + \
                        "set ArcM.words = ArcM.words + [ele in p.words where not ele in ArcM.words] \n" + \
                        "set ArcM.month_qty = size(ArcM.words) \n" + \
                        "merge (rofArc)-[rWM:WEEK_MONTH]->(ArcM) \n" + \
                        "merge (sc)<-[rSArcM:SUBCAT_ARCHIVED_M]-(ArcM) \n" + \
                        "merge (u)<-[rUArcM:ARCHIVED_M]-(ArcM) \n" + \
                        "// TO INCLUDE EXAMPLE SENTENCES \n" + \
                        "with p, ArcM, sc \n" + \
                        "unwind p.words as word \n" + \
                        "match (we:" + subcat + ":" + source + " {word:word})-[:" + relationship +"]->\n" + \
                        "(wss:WordSound:" + source + ") \n" + \
                        "where // exists {(wss)-[:SUBCAT]-(sc)} or \n" + \
                        " (wss.idCat = sc.idCat and wss.idSCat = sc.idSCat) \n" + \
                        "with p, ArcM, sc, wss.example as wssexample \n" + \
                        ", replace( \n" + \
                        "  replace( \n" + \
                        "    replace( \n" + \
                        "       replace( \n" + \
                        "              replace( \n" + \
                        "                    replace( \n" + \
                        "                            wss.example  \n" + \
                        "                            , '" + '"' + "' + word + " + "'" + '". ' + "' \n" + \
                        "                                , '' \n" + \
                        "                            )  \n" + \
                        "                    , '“' + word + '”' \n" + \
                        "                        , '' \n" + \
                        "                    ) \n" + \
                        '            , "' + "'" + '" + word + ' + '"' + "'. " + '" \n' + \
                        "            , '' \n" + \
                        "        )  \n" + \
                        "        , word + ' - ' \n" + \
                        "        , ''\n" + \
                        "    ) \n" + \
                        "    , apoc.text.capitalize(word) + '.' \n" + \
                        "    , ''\n" + \
                        "    ) \n" + \
                        "    , apoc.text.capitalizeAll(word) + '.' \n" + \
                        "    , ''\n" + \
                        ") \n" + \
                        "as sentence2 \n" + \
                        "with p, ArcM, sc, collect(wssexample) as wssexamples, collect(sentence2) as sentences2 " + \
                        "set ArcM.sentences = ArcM.sentences + [ele in sentences2 where not ele in ArcM.sentences] \n" + \
                        "return p.packageId as packageId , p.label as slabel, p.status as status " 
    # filter (x in n.A where x<>"newValue")
    # "ArcM.words = ArcM.words + p.words \n" + \
    #print('=============================\narchiving:', neo4j_statement)
    #await awsleep(0)
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
    
    #print("\n\n\n","="*30, "se ejecuta cierre de package")

    res = set_archived_package(package, userId)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return res

