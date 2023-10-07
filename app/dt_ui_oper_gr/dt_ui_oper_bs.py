from fastapi import APIRouter, Response, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log
import __generalFunctions as funcs
from datetime import datetime as dt
from asyncio import sleep as awsleep

# https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/11855
# dieron el tip de instalar pip install gradio_client==0.2.7
# para el error de Exception in ASGI application

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

from __generalFunctions import myfunctionname, myConjutationLink \
                    ,_getdatime_T \
                    , get_list_elements
                    #, get_list_element

from random import shuffle as shuffle

from app.model.md_params_oper import ForPackages as ForNewPackage

router = APIRouter()


def get_pronunciationId(words, packagename, userId):
    """
    Function to identify and return the id() of pronunciation file
    into the WordSound collection
    """
    #print("========== starting get_pronunciationId id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())

    # getting the WordSound id for each word and example
    neo4j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                    "unwind wordlist as wordtext \n" + \
                    "match (pkg:Package {packageId:'" + packagename + "'})-\n" + \
                    "[:PACKAGED]-(u:User {userId: '"+ userId +"'}) \n" + \
                    "optional match(wp:WordSound {word:wordtext}) \n" + \
                    "where pkg.source in labels(wp) \n" + \
                        " and pkg.idCat = wp.idCat \n" + \
                        " and pkg.idSCat = wp.idSCat \n" + \
                    "return wordtext, id(wp) as idNode, wp.actived, wp.example, wp.Spanish"

    #print('pronunciationId_neo4j_statement:', neo4j_statement)
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words pronunciation",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    result = []
    #print(f"ourssss words: {words}")
    for node in nodes:
        #print(f"ciclo de nodes")
        sdict = dict(node)
        idNode = None
        example = ''
        example_target = ''
        for word in words:            
            #print(f"paraaa word: -{word}- thenermos s_dictttt: -{sdict['wordtext']}-")
            if word == sdict['wordtext']:
                idNode = sdict["idNode"]
                example = sdict.get('wp.example', '')
                example_target = sdict.get('wp.Spanish', '')
                break
        dict_pronunciation = {'pronunciation': idNode,
                        'example': example,
                        'target':example_target} # binfile.decode("ISO-8859-1")} #utf-8")}
        result.append(dict_pronunciation)

    #print("        ->   ========== ending get_pronunciationId id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())    
    return result


@router.get("/get_/categories/")
async def get_categories(Authorization: Optional[str] = Header(None)):
    """
    Function to get all categories and subcategories allowed for the user

    """
    
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("========== starting get_categories id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    """
    neo4j_statement = "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]-(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category {idCat:1})<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "with o, c, s.name as subcategory, c.idCat * 1000000 + s.idSCat as idCS \n" + \
                        "order by o.idOrg, c.name, idCS, subcategory \n" + \
                        "return o.name, c.name as category, c.idCat as idCat, \n" + \
                                "collect(subcategory) as subcategories, collect(idCS) as subid \n" + \
                        "union \n" + \
                        "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]-(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category)<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "where c.idCat <> 1 and \n" + \
                             "exists {match (s)<-[:SUBCAT]-(es:ElemSubCat) \n" + \
                                    " where o.lSource in labels(es)} \n" + \
                        "with o,c, s.name as subcategory, c.idCat * 1000000 + s.idSCat as idCS  \n" + \
                        "order by o.idOrg, c.name, subcategory \n" + \
                        "return o.name, c.name as category, c.idCat as idCat, \n" + \
                                "collect(subcategory) as subcategories, collect(idCS) as subid"
    """
    neo4j_statement ="match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]->(o:Organization) \n" + \
                        "<-[:SUBJECT]-(c:Category {idCat:1})<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "with o.idOrg as idOrg, o.name as oname, \n" + \
                        "c.idCat as idCat, c.name as cname, s.name as subcategory, \n" + \
                        " c.idCat * 1000000 + s.idSCat as idCS \n" + \
                        "order by idOrg, cname, idCS, subcategory \n" + \
                        "return oname, cname as category, idCat, \n" + \
                        "collect(subcategory) as subcategories, collect(idCS) as subid \n" + \
                        "union \n" + \
                        "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]->(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category)<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "where c.idCat <> 1 and \n" + \
                        "exists {match (s)<-[:SUBCAT]-(es:ElemSubCat) \n" + \
                        "where o.lSource in labels(es)} \n" + \
                        "with o.idOrg as idOrg, o.name as oname, \n" + \
                        "c.idCat as idCat, c.name as cname, \n" + \
                        "s.name as subcategory, c.idCat * 1000000 + s.idSCat as idCS  \n" + \
                        "order by idOrg, cname, subcategory \n" + \
                        "return oname, cname as category, idCat as idCat, \n" + \
                        "collect(subcategory) as subcategories, collect(idCS) as subid "
    #print('cats-subcats:', neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting categories for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    await awsleep(0)
    
    listcat = []
    for node in nodes:
        sdict = dict(node)        
        #print(dict(node))
        subcat_list = []
        ndic = {'Category': sdict["category"], 'idCat' : sdict["idCat"]}
        for gia, value in enumerate(sdict['subcategories']):
            subs = {'subcategory': value , 'idSCat': sdict["subid"][gia]}
            subcat_list.append(subs)
        ndic["subcategories"] = subcat_list[:]
        listcat.append(ndic)
    print("        ->   ========== ending get_categories id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': listcat}


@router.get("/get_/dashboard/")
async def get_dashboard_table(Authorization: Optional[str] = Header(None)):
    """
    Function to get how many words has the user worked for each subcategory

    """
    
    global appNeo, session, log  # w_SC_10000053
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    startinat = _getdatime_T()
    tm1 = dt.now()
    #print("========== starting get_dashboard_table id: ", userId, " dt: ", startinat, " -> ", myfunctionname())

    dtimenow = dt.now()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = dtimenow.strftime("%W")     

    neo4j_statement =  "/* section to get words */ \n" + \
        "with " + str(yearr) + " as yearr, \n" + \
                        str(monthh) + " as monthh, \n" + \
                        str(weekk) + " as weekk \n" + \
        "match (u:User {userId:'" + userId + "'})-[:RIGHTS_TO]->(o:Organization)<-\n" + \
        "[:SUBJECT]-(c:Category {idCat:case when o.lSource = 'English' then 1 else 101 end})" + \
            "<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) \n" + \
        "optional match (u)<-[:ARCHIVED_W]-(rof:Archived_W " + \
            "{userId:u.userId, year:yearr, month:monthh, week:weekk, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_W]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, sum(rof.week_qty) as qtyweek \n" + \
        "optional match (u)<-[:ARCHIVED_M]-(rofM:Archived_M " + \
            "{userId:u.userId, year:yearr, month:monthh, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, sum(rofM.month_qty) as qtymonth \n" + \
        "// get all words learned \n"  + \
        "optional match (u)<-[:ARCHIVED_M]-(rofMt:Archived_M " + \
            "{userId:u.userId, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, qtymonth, sum(rofMt.month_qty) as qtytotal \n" + \
        "match (es:Word)-[:TRANSLATOR]->(ess:Word) \n" + \
        "where o.lSource in labels(es) and o.lTarget in labels(ess) \n" + \
        " and exists {(es)-[r:PRONUNCIATION]->(wss:WordSound) where o.lSource in labels(wss)} \n" + \
        "with u, o, c, sc, count(distinct es) as wordsSC, yearr, monthh, weekk, qtyweek, qtymonth,qtytotal \n" + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, \n" + \
                "sum(qtymonth) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS, \n" + \
                "qtyweek as qtyweek, qtymonth as qtymonth, qtytotal as qtytotal \n" + \
        "union \n" + \
        "/* SECTION TO GET cat = 1 and idSCat <> 1 */ \n" + \
        "with " + str(yearr) + " as yearr, \n" + \
                        str(monthh) + " as monthh, \n" + \
                        str(weekk) + " as weekk \n" + \
        "match (o:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + userId + "'}) \n" + \
        "match (o)<-[rsub:SUBJECT]-(c:Category {idCat:case when o.lSource = 'English' then 1 else 101 end}) \n" + \
        "match (c)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idCat:c.idCat}) \n" + \
        "where  sc.idSCat <> 1 \n" + \
        "optional match (u)<-[:ARCHIVED_W]-(rof:Archived_W " + \
            "{userId:u.userId, year:yearr, month:monthh, week:weekk, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_W]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, sum(rof.week_qty) as qtyweek \n" + \
        "optional match (u)<-[:ARCHIVED_M]-(rofM:Archived_M " + \
            "{userId:u.userId, year:yearr, month:monthh, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, sum(rofM.month_qty) as qtymonth \n" + \
        "// get all words learned \n"  + \
        "optional match (u)<-[:ARCHIVED_M]-(rofMt:Archived_M " + \
            "{userId:u.userId, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, qtymonth,  sum(rofMt.month_qty) as qtytotal \n" + \
        "match (sc)<-[esr:SUBCAT]-(es:ElemSubCat)-[tr:TRANSLATOR]->(ws:ElemSubCat) \n" + \
        "where o.lSource in labels(es) and o.lTarget in labels(ws) \n" + \
        "with o, c, sc, count(es) as wordsSC, yearr, monthh, weekk, qtyweek, qtymonth,qtytotal \n" + \
        "order by sc.idCat, sc.idSCat, c.name, sc.name \n" + \
        "return c.name as CatName, \n" + \
                "sc.name as SCatName, \n" + \
                "wordsSC as totalwords, \n" + \
                "sum(qtymonth) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS, \n" + \
                "qtyweek as qtyweek, qtymonth as qtymonth, qtytotal \n" + \
        "union \n" + \
        "/* SECTION TO GET CATEGORIIES DISTINCT TO 1 */ \n" + \
        "with " + str(yearr) + " as yearr, \n" + \
                        str(monthh) + " as monthh, \n" + \
                        str(weekk) + " as weekk \n" + \
        "match (o:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + userId + "'}) \n" + \
        "match (o)<-[rsub:SUBJECT]-(c:Category) \n" + \
        "where c.idCat <> 1  \n" + \
        "match (c)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idCat:c.idCat}) \n" + \
        "where exists {(sc)<-[:PACK_SUBCAT]-(:Package)-[:PACKAGED]->(u)} \n" + \
        "optional match (u)<-[:ARCHIVED_W]-(rof:Archived_W " + \
            "{userId:u.userId, year:yearr, month:monthh, week:weekk, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_W]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, sum(rof.week_qty) as qtyweek \n" + \
        "optional match (u)<-[:ARCHIVED_M]-(rofM:Archived_M " + \
            "{userId:u.userId, year:yearr, month:monthh, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, sum(rofM.month_qty) as qtymonth \n" + \
        "// get all words learned \n"  + \
        "optional match (u)<-[:ARCHIVED_M]-(rofMt:Archived_M " + \
            "{userId:u.userId, \n" + \
            "source:o.lSource, target:o.lTarget})-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
        "with u, o, c, sc, yearr, monthh, weekk, \n" + \
            "qtyweek, qtymonth, sum(rofMt.month_qty) as qtytotal \n" + \
        "match (sc)<-[esr]-(es:ElemSubCat)-[tr:TRANSLATOR]->(ws:ElemSubCat) \n" + \
        "where o.lSource in labels(es) and o.lTarget in labels(ws) \n" + \
        "with u, o, c, sc, count(es) as wordsSC, yearr, monthh, weekk, \n" + \
            " qtyweek, qtymonth,qtytotal \n" + \
        "order by sc.idCat, sc.idSCat, c.name, sc.name \n" + \
        "optional match (u)<-[:PACKAGED]-(pkg:Package {status:'closed'})-[:PACK_SUBCAT]->(sc) \n" + \
        "with o, c, sc, wordsSC, yearr, monthh, weekk, \n" + \
            " qtyweek, qtymonth,qtytotal, coalesce(count(distinct pkg),0) as clsdpkgs \n" + \
        "order by sc.idCat, sc.idSCat, c.name, sc.name \n" + \
        "return c.name as CatName, \n" + \
                "sc.name as SCatName, \n" + \
                "wordsSC as totalwords, \n" + \
                "clsdpkgs as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS, \n" + \
                "qtyweek as qtyweek, qtymonth as qtymonth, qtytotal as qtytotal "
    
    
    beforeNeo4 =  _getdatime_T()

    await awsleep(0)
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting data for dashboard table",
                        statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    afterNeo4 =  _getdatime_T()
    
    listcat,  listBasicK= [], []
    msg = ""
    try:
        for node in nodes:          
            sdict = dict(node)
            tw = ""
            qtymonth = str(sdict["qtymonth"]) if sdict["qtymonth"] else "0"
            qtyweek = str(sdict["qtyweek"]) if sdict["qtyweek"] else "0"
            twq = sdict["totalwords"] - sdict["learned"]
            if twq >= 120:
                #tw = "m: " + qtymonth + " / 120" + "  |  t: " + str(sdict["qtytotal"]) + " / " + str(sdict["totalwords"])
                tw = "m: " + qtymonth + "  |  t: " + str(sdict["qtytotal"]) + " / " + str(sdict["totalwords"])
            else:
                #tw = "m: " + qtymonth + " / " + str(twq) + " |  t: " + str(sdict["qtytotal"]) + " / " +  str(sdict["totalwords"])
                tw = "m: " + qtymonth + " |  t: " + str(sdict["qtytotal"]) + " / " +  str(sdict["totalwords"])
            if twq >= 40:
                #tw = "w: " + qtyweek + " / 40" + "  |  " + tw
                tw = "w: " + qtyweek + "  |  " + tw                
            else:
                #tw = "w: " + qtyweek + " / " + str(twq) + "  |  " + tw
                tw = "w: " + qtyweek + "  |  " + tw

            sdict["totalwords"] = tw
            if sdict['idCat'] == 52:
                listBasicK.append(sdict)
            else:
                listcat.append(sdict)
    except Exception as error:
        msg = "error on empty nodes - no iterable"
    diftime = str(dt.now() - tm1)
    #print("==> ",startinat, '\n antes de neo4j:', beforeNeo4, 'despues de neo4j:', afterNeo4, " termina a ", _getdatime_T(), " = ", diftime)
    print("        ->   ========== ending get_dashboard_table id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), msg)
    return {'message': listBasicK + listcat}


@router.get("/get_/config_uid/")
async def get_config_uid(Authorization: Optional[str] = Header(None)):
    """
    Function to get some options or data of the user

    """


    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("==========  starting get_config_uid id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log 

    neo4j_statement = "match (us:User {userId:'" + userId + "'}) \n" + \
                        "optional match (us)-[r:FIRSTCONTACT]->(rep:FirstContact) \n" + \
                    "return us.userId as userId \n" + \
                        ", us.name as name \n" + \
                        ", us.country_birth as country_birth, us.country_res as country_res \n" + \
                        ", us.native_lang as native_lang \n" + \
                        ", us.selected_lang as selected_lang \n" + \
                        ", toString(us.ctInsert) as us_ctInsert \n" + \
                        ", us.email as usemail, us.email_alt as usemail_alt \n" + \
                        ", us.kol as koflic \n" + \
                        ", us.defaultCap as capacity \n" + \
                        ", rep.contactId as contactId \n" + \
                        ", rep.name as contactName \n" + \
                        ", rep.phone as contactPhone \n" + \
                        ", rep.email as contactEmail \n" + \
                        "limit 1"
    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                 log_description="getting user local configuration data ",
                 statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    sdict={}
    msg = ""
    try:
        for node in nodes:
            sdict = dict(node)
    except Exception as error:
        msg = "error on empty nodes - no iterable"
    print("==========  ending get_config_uid id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), msg)
    return sdict


@router.get("/get_/cat_subc/{idSCat}")
async def get_user_packagelist(idSCat:int, Authorization: Optional[str] = Header(None)):
    """
    Function to get to get category name and subcategory name \n

    """
    
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("========== starting get_user_packagelist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log 

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000

    statement = "match (u:User {userId:'" + userId + "'})\n" + \
                "-[rt:RIGHTS_TO]-(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "return c.idCat as idCat, c.name as catname, sc.name as scname limit 1" 
    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    await awsleep(0)
    
    
    catscname = {}
    for node in nodes:
        sdict = dict(node)    
        catscname = {'idCat': sdict["idCat"]
                     , 'CatName': sdict["catname"]
                    , 'scatname': sdict["scname"]
        }
    print("        ->   ========== ending get_user_packagelist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return catscname


@router.get("/get_/user_packagelist/{idSCat}")
async def get_user_packagelist(idSCat:int, Authorization: Optional[str] = Header(None)):
    """
    Function to get opened package list in a specific SubCategory \n

    """
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("========== starting get_user_packagelist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log 

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000

    statement = "match (u:User {userId:'" + userId + "'})\n" + \
                "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "<-[:PACK_SUBCAT]-(pkg:Package {userId: u.userId, status:'open'}) \n" + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) \n" + \
                "with u, pkg, c,  pkgS.level as level, \n" + \
                "min(pkgS.ptgerror) as grade, \n" + \
                "coalesce(o.ptgmaxerrs,100.0-85.0) as maxerrs \n" + \
                "with u, pkg, c,  max(level + '-,-' + coalesce(toString(grade),'0')) as level, \n" + \
                "count(DISTINCT level) as levs, maxerrs \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName, \n" + \
                    "pkg.SubCat as SCatName, \n" + \
                    "c.idCat * 1000000 + pkg.idSCat as idSCat, \n" + \
                    "split(level,'-,-')[0] as level, \n" + \
                    "toFloat(split(level,'-,-')[1]) as grade, levs, maxerrs, pkg.label as labelname, \n" + \
                    "coalesce(pkg.ctUpdate, pkg.ctInsert) as updatedate \n" + \
                "order by updatedate desc, labelname"
    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    await awsleep(0)
        
    listPack = []
    for node in nodes:
        sdict = dict(node)    
        
        if sdict["grade"] == None:
            ptg_errors = 100
        else:
            ptg_errors = float(sdict["grade"]) #  - 1) * 100            
            if ptg_errors < 0:
                ptg_errors = 100
        #print(ptg_errors, 'maxerrs', sdict["maxerrs"])
        if sdict["maxerrs"] > (ptg_errors if ptg_errors>=0 else 100):
            maxlevel = sdict["level"]
        else:
            maxlevel = funcs.level_seq(sdict["level"], forward=False)
        ndic = {'packageId': sdict["pkg.packageId"]
                , 'Category': sdict["CatName"], 'idCat' : sdict["idCat"]
                , 'SubCat': sdict["SCatName"], 'idSCat' : sdict["idSCat"]
                , 'distinct_levs': sdict["levs"]
                , 'maxlevel': maxlevel # sdict["level"]
                , 'ptg_errors' : ptg_errors
                , 'maxptg_errs':sdict["maxerrs"]
                , 'label':sdict["labelname"]
        }
        
        listPack.append(ndic)
    print("        ->   ========== ending get_user_packagelist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': listPack}


@router.get("/get_/user_packagehistorylist/")
async def get_user_packagehistorylist(idSCat:int, ipage:int=1, ishow:int=10, ssearch:str=None, sword:str=None
                               ,Authorization: Optional[str] = Header(None)):
    """
    endpoint/subCategoryId?page=1&show=10&search='2023'
    --------------------------------
    {
        data: any[],
        pageLast: number,
    }

    Function to get opened package list in a specific SubCategory \n

    """
    
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("========== starting get_user_packagehistorylist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log 

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000

    if ssearch == None:
        ssearch = ''
    if sword == None:
        sword = ''
    ssearch = ssearch.strip().replace("'","").replace('"',"")
    sword = sword.strip().replace("'","").replace('"',"")

    statement = "with '" + ssearch + "' as slabel, '" + sword + "' as sword \n" + \
                "match (u:User {userId:'" + userId + "'})\n" + \
                "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "<-[:PACK_SUBCAT]-(pkg:Package {userId: u.userId, status:'closed'})-\n" + \
                    "[:PACKAGED]->(u) \n" + \
                "where (pkg.label contains slabel or slabel = '') \n" + \
                    "and (sword in pkg.words or sword = '') \n" + \
                "with u, o, c, collect(pkg) as pkgs, count(pkg) as qtypkg \n" + \
                "unwind pkgs as pkg\n" + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) \n" + \
                "with u, pkg, c, o, pkgS.level as level, \n" + \
                "min(pkgS.ptgerror) as grade, \n" + \
                "coalesce(o.ptgmaxerrs,100.0-85.0) as maxerrs, qtypkg \n" + \
                "with u, pkg, c,  max(level + '-,-' + coalesce(toString(grade),'0')) as level, \n" + \
                "count(DISTINCT level) as levs, maxerrs, qtypkg \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName, \n" + \
                    "pkg.SubCat as SCatName, \n" + \
                    "c.idCat * 1000000 + pkg.idSCat as idSCat, \n" + \
                    "split(level,'-,-')[0] as level, \n" + \
                    "toFloat(split(level,'-,-')[1]) as grade, levs, maxerrs, pkg.label as labelname, qtypkg \n" + \
                "order by coalesce(pkg.ctUpdate, pkg.ctInsert) desc \n" + \
                "skip " + str((ipage - 1) * ishow) + " \n" + \
                "limit " + str(ishow) 
    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    await awsleep(0)    
    
    listPack = []
    totrecs = 0
    for node in nodes:
        sdict = dict(node)    
        #subcat_list = []
        #print('sdict:', sdict)
        
        if sdict["grade"] == None:
            ptg_errors = 100
        else:
            ptg_errors = float(sdict["grade"]) #  - 1) * 100            
            if ptg_errors < 0:
                ptg_errors = 100
        #print(ptg_errors, 'maxerrs', sdict["maxerrs"])
        if sdict["maxerrs"] > (ptg_errors if ptg_errors>=0 else 100):
            maxlevel = sdict["level"]
        else:
            maxlevel = funcs.level_seq(sdict["level"], forward=False)
        ndic = {'packageId': sdict["pkg.packageId"]
                , 'Category': sdict["CatName"], 'idCat' : sdict["idCat"]
                , 'SubCat': sdict["SCatName"], 'idSCat' : sdict["idSCat"]
                , 'distinct_levs': sdict["levs"]
                , 'maxlevel': maxlevel # sdict["level"]
                , 'ptg_errors' : ptg_errors
                , 'maxptg_errs':sdict["maxerrs"]
                , 'label':sdict["labelname"]
        }
        totrecs = sdict["qtypkg"]        
        listPack.append(ndic)
    totalpages = totrecs // ishow 
    if totalpages * ishow != totrecs:
        totalpages += 1
    
    print("        ->   ========== ending get_user_packagehistorylist id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'page': ipage, 'show': ishow, 'totrecs': totrecs, 'lastpage':totalpages, 'data':listPack}


@router.get("/get_/user_package_st/{packageId}")
async def get_user_package_st(packageId:str, Authorization: Optional[str] = Header(None)):
    """
    Function to get package level \n

    """
    global appNeo, session, log
    
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    #print("========== starting get_user_package_st id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    
    statement = "match (u:User {userId:'" + userId + "'})<-[:PACKAGED]-\n" + \
                    "(pkg:Package {packageId: '" + packageId + "'}) \n" + \
                    "-[:PACK_SUBCAT]-(sc:SubCategory)\n" + \
                    "-[:CAT_SUBCAT]-(c:Category)-[:SUBJECT]->(o:Organization) \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName, \n" + \
                " sc.name as SCatName, \n" + \
                " c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                " pkg.level as level"
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    await awsleep(0)

    listPack = []
    for node in nodes:
        sdict = dict(node)
        ndic = {'packageId': sdict["pkg.packageId"]
                , 'Category': sdict["CatName"], 'idCat' : sdict["idCat"]
                , 'SubCat': sdict["SCatName"], 'idSCat' : sdict["idSCat"]
                , 'maxlevel': sdict["level"]
        }
        
        listPack.append(ndic)   

    """
    statement = "match (u:User {userId:'" + userId + "'})<-[:PACKAGED]-\n" + \
                "(pkg:Package {packageId: '" + packageId + "'}) \n" + \
                "-[:PACK_SUBCAT]-(sc:SubCategory)\n" + \
                "-[:CAT_SUBCAT]-(c:Category)-[:SUBJECT]->(o:Organization) \n" + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) \n" + \
                "with u, pkg, c, sc,  pkgS.level as level, \n" + \
                "min(pkgS.ptgerror) as grade, \n" + \
                "coalesce(o.ptgmaxerrs,100.0-85.0) as maxerrs \n" + \
                "with u, pkg, c, max(level + '-,-' + \n" + \
                "coalesce(toString(grade),'0')) as level, \n" + \
                "count(DISTINCT level) as levs, maxerrs, sc \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName, \n" + \
                "pkg.SubCat as SCatName, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "split(level,'-,-')[0] as level, \n" + \
                "toFloat(split(level,'-,-')[1]) as grade, levs, maxerrs"
    listPack = []
    for node in nodes:
        sdict = dict(node)    
        #subcat_list = []
        #print('sdict:', sdict)
        if sdict["grade"] == None:
            ptg_errors = 100
        else:
            ptg_errors = float(sdict["grade"]) #  - 1) * 100            
            if ptg_errors < 0:
                ptg_errors = 100
        #print(ptg_errors, 'maxerrs', sdict["maxerrs"])
        if sdict["maxerrs"] > (ptg_errors if ptg_errors>=0 else 100):
            maxlevel = sdict["level"]
        else:
            maxlevel = funcs.level_seq(sdict["level"], forward=False)
        ndic = {'packageId': sdict["pkg.packageId"]
                , 'Category': sdict["CatName"], 'idCat' : sdict["idCat"]
                , 'SubCat': sdict["SCatName"], 'idSCat' : sdict["idSCat"]
                #, 'distinct_levs': sdict["levs"]
                , 'maxlevel': maxlevel # sdict["level"]
                #, 'ptg_errors' : ptg_errors
                #, 'maxptg_errs':sdict["maxerrs"]
        }
        
        listPack.append(ndic)
    """
    print("        ->   ========== ending get_user_package_st id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return {'message': listPack}

def get_words(userId, pkgname, wordslevel='words'):
    global app, session, log

    #print("========== starting get words id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())    

    npackage = []

    level = 'null'  # elementary level        

    neo4j_statement = "/* EXTRACCIÓN PARA SUBCATEGORÍA WORDS  idSCat = 1*/ \n" + \
                        "match (pkg:Package {packageId:'" + pkgname + "', idSCat: 1})" + \
                        "-[:PACKAGED]-(u:User {userId:'" + userId + "'})\n" + \
                        "-[rt:RIGHTS_TO]-(o:Organization)<-[:SUBJECT]\n" + \
                        "-(c:Category {idCat:pkg.idCat})<-[:CAT_SUBCAT]-" + \
                            "(sc:SubCategory {idSCat:pkg.idSCat})<-[:PACK_SUBCAT]-(pkg)\n" + \
                        "where o.lSource = pkg.source and o.lTarget = pkg.target \n" + \
                        "unwind pkg. " + wordslevel + " as pkgwords \n" + \
                        "with pkg, pkg.packageId as pkgname, o.ptgmaxerrs as maxerrs, \n" + \
                            " pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, n, s, tes \n" + \
                        "order by n, tes.sorted \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, n, collect(s.word) as swlist \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, \n" + \
                            "COALESCE(n.ckow, []) as kow, \n" + \
                            "COALESCE(n.ckowb_complete, []) as kowc, \n" + \
                            "COALESCE(n.cword_ref, []) as wordref, \n" + \
                            "COALESCE(n.wrword_ref, '') as wr_wordref, \n" + \
                            "COALESCE(n.wr_kow, []) as wr_kow, \n" + \
                            "n.word as ewlist, \n" + \
                            "swlist as swlist \n" + \
                        "optional match (pkgS:PackageStudy)-[]-(pkg) \n" + \
                            "where pkgS.ptgerror <= maxerrs \n" + \
                        "return 'words' as subCat, pkg.idSCat as idSCat, pkg.idCat as idCat, pkglabel as label, " + \
                            "COALESCE(max(pkgS.level), '" + level + "') as maxlevel, '' as linktitles, '' as links, \n" + \
                            "ewlist as slSource, kow, kowc, wordref, swlist as slTarget, \n" + \
                            "wr_wordref, wr_kow, pkg.source as langsource, pkg.target as langtarget  \n" + \
                        "/* EXTRACCIÓN PARA OTRAS SUBCATEGORÍAS  */ \n" + \
                        "union \n" + \
                        "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "'})\n" + \
                        "-[:PACK_SUBCAT]->(s:SubCategory {idSCat:pkg.idSCat})-[:CAT_SUBCAT]\n" + \
                            "->(cat:Category {idCat:pkg.idCat})\n" + \
                        "-[:SUBJECT]->(org:Organization) \n" + \
                        "where org.lSource = pkg.source and org.lTarget = pkg.target \n" + \
                        "unwind pkg. " + wordslevel + " as pkgwords \n" + \
                        "match(s)<-[rscat:SUBCAT]-(ew:ElemSubCat {word:pkgwords})\n" + \
                        "-[:TRANSLATOR]->(sw:ElemSubCat)-[:SUBCAT]->(s) \n" + \
                        "where pkg.source in labels(ew) and pkg.target in labels(sw) \n" + \
                        "with org, pkg, s, ew, collect(distinct sw.word) as sw, rscat \n" + \
                        "order by rscat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with org, pkg, s, ew.link_title as linktitles, ew.link as links, \n" + \
                            "COALESCE(ew.ckow, []) as kow, \n" + \
                            "COALESCE(ew.ckowb_complete, []) as kowc, \n" + \
                            "COALESCE(ew.cword_ref, []) as wordref, \n" + \
                            "COALESCE(ew.wrword_ref, '') as wr_wordref, \n" + \
                            "COALESCE(ew.wr_kow, []) as wr_kow, \n" + \
                            "ew.word as ewlist, \n" + \
                            "sw as swlist \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) where pkgS.ptgerror <= org.ptgmaxerrs \n" + \
                        "with pkg, s, ewlist, swlist, kow, kowc, wordref, \n" + \
                        "COALESCE(max(pkgS.level), '" + level + "') as level, linktitles, links, wr_wordref, wr_kow \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, s.idCat as idCat, pkg.label as label, \n" + \
                            "level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, kow, kowc, wordref, swlist as slTarget, \n" + \
                            "wr_wordref, wr_kow, pkg.source as langsource, pkg.target as langtarget" 
    #print('statement 01:', neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for user and pkgId="+pkgname,
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())      
    #print("YA EJECUTÓ")
    pkgdescriptor = {}
    words = []
    npackage = []
    kow, kowc, wrkowc = [], [], [] 
    wr_wordref, langs, langt = [], [], []
    idCat= ""
    for gia, node in enumerate(nodes):
        sdict = dict(node)        
        idCat= sdict["idCat"]
        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":sdict["maxlevel"]
        }
        kow.append(sdict["kow"])
        kowc.append(sdict["kowc"])
        wrkowc.append(sdict["wr_kow"])
        wr_wordref.append(sdict["wr_wordref"])
        langs.append(sdict["langsource"])
        langt.append(sdict["langtarget"])

        #kow = sdict["kow"]
        #kowc = sdict["kowc"]
        #wrkowc = sdict["wr_kow"]
        #wr_wordref = sdict["wr_wordref"]
        #langs = sdict["langsource"]
        #langt = sdict["langtarget"]

        value = sdict["slSource"]               # element[0]
        prnReference = sdict["linktitles"]      # element[3]
        prnLink = sdict["links"]                # element[4]
        ltarget = sdict["slTarget"]             # element[1]
        wordref = sdict["wordref"]              # element[5]
        # position  # element[2]
        if type(ltarget) == type(list()):
            pass
        else:
            ltarget = [ltarget]
        npackage.append([value, ltarget, gia + 1, prnReference, prnLink, wordref])
        words.append(value) # (value, sdict['kow']))

        #for gia, value in enumerate(sdict['slSource']):
        #    prnReference = funcs.get_list_element(sdict["linktitles"], gia)
        #    prnLink     = funcs.get_list_element(sdict["links"], gia)
        #    ltarget = funcs.get_list_element(sdict["slTarget"],gia)
        #    wordref = funcs.get_list_element(sdict["wordref"],gia)
        #    if type(ltarget) == type(list()):
        #        pass
        #    else:
        #        ltarget = [ltarget]
        #    npackage.append([value, ltarget, gia + 1, prnReference, prnLink, wordref])
        #    words.append(value) # (value, sdict['kow']))
        #print("----------------------------------------------wwword:", value)

    lpron = get_pronunciationId(words, pkgname, userId)
         
    result = []
    result2 = []

    # we have a list with neo4 values, we need to add some elements like:
    # - pronunciation with sentence example (lpron)
    # - kind of word and link for conjungation verbs
    # - location or more information for countries, skeleton, etc 

    for gia, element in enumerate(npackage): # element Strcuture:[value, ltarget, gia + 1, prnReference, prnLink]
        # kow section
        if len(kow[gia]) == 0:
            isitaverb = [False, []]
        else:
            verbis = str(kowc[gia]).lower().replace("adverb","xxxxx")
            isitaverb = [('verb' in verbis), kowc[gia]]
        
        s_kow_verb, s_kow_past_verb = {'title': None}, {'title': None}
        kowv, kowo, past_verb = [], [], False
        if isitaverb[0] or 'v ' in str(wrkowc[gia]): # si es verbo
            if not isitaverb[0]:
                isitaverb[0] = 1
            #print("lene elemente:", len(element[5]), element[5])
            if wr_wordref[gia] != "":
                conjLink = myConjutationLink(wr_wordref[gia], langs[gia])   # wordref
            elif element[5] == [''] or len(element[5]) == 0:  ## es el infintivo del verbo o no hay referencia ligada
                conjLink = myConjutationLink(element[0], langs[gia])      
            else:
                conjLink = myConjutationLink(element[0][0], langs[gia])# c' wordref            
                
            for k in kowc[gia]:
                #print("valor de kkk:", k , 'verb' in k)
                if 'verb' in k:
                    kowv.append(k)
                else: 
                    kowo.append(k)
            if len(kowv) == 0:
                if 'v ' in str(wrkowc[gia]):
                    if "v past" in str(wrkowc[gia]) and "v past p" in str(wrkowc[gia]):
                        kowv.append('past - verb, past part - verb')
                        past_verb = True
                    elif "v past" in str(wrkowc[gia]):
                        kowv.append('past - verb')
                        past_verb = True
                    elif  "v past p" in str(wrkowc[gia]):
                        kowv.append('past part - verb')
                        past_verb = True
                    else:
                        kowv.append('verb')
            else:
                if "v past" in str(wrkowc[gia]) or "v past p" in str(wrkowc[gia]):
                    past_verb = True

            s_kow_verb = {"type": "kow_verb"
                        , "position" : "source"
                        , "apply_link": isitaverb[0] # is it a verb?
                        , "link" : conjLink
                        , "title": get_list_elements(kowv, 3) 
                        #(isitaverb[1],3) # kow[gia] # list of different kind of word for the same word
                        }
            if past_verb: 
                #if wr_wordref[gia] != "":
                #    conjLink = myConjutationLink(wr_wordref[gia], langt)   # wordref
                #elif element[5] == [''] or len(element[5]) == 0:  ## es el infintivo del verbo o no hay referencia ligada
                #    conjLink = myConjutationLink(element[0], langt[gia])      # c' wordref 
                #else:
                #    conjLink = myConjutationLink(element[0][0], langt[gia])   # c' wordref   
                conjLink = myConjutationLink(element[1][0], langt[gia])   # c' wordref   
                s_kow_past_verb = {"type": "kow_verb"
                            , "position" : "target"
                            , "apply_link": isitaverb[0] # is it a verb?
                            , "link" : conjLink
                            , "title": get_list_elements(kowv, 3) 
                            #(isitaverb[1],3) # kow[gia] # list of different kind of word for the same word
                            }
        else:
            kowo = kowc[gia]
            conjLink = ''
        if len(kowo) > 0:
            s_kow = {"type": "kow_diff_verb"
                            , "position" : "source"
                            , "apply_link": isitaverb[0] # is it a verb?
                            , "link" : ""
                            , "title": get_list_elements(kowo,3)
                            #(isitaverb[1],3) # kow[gia] # list of different kind of word for the same word
                            }
        else:
            s_kow = {'title': None}
        if element[3] not in [None, ""]:
            s_object={"type": "location"
                            , "position" : "source" # source para tarjeta superior, 'target' para tarjeta inferior
                            , "apply_link": True if element[3] else False
                            , "link" : element[4]
                            , "title": [element[3]]   # se añade en lista, para igual la salida con words
                            }
        else:
            s_object={"title":None }

        ladds = []
        for ele in [s_kow_verb, s_kow, s_object, s_kow_past_verb]:
            if ele["title"]:
                ladds.append(ele)

        new_element = {'word': element[0]
                        , "tranlate": element[1]
                        , "position": element[2]
                        , "pronunciation": lpron[gia]
                        , "additional": ladds
                        }        

        #element.append(lpron[gia])
        #element.append([s_kow, s_object])
        #result.append(element)
        result2.append(new_element)
    if idCat not in [52,102]:
        shuffle(result2)  # this shuffle is to execute an random sort with words
    pkgdescriptor["message"] = result2   

    print("        ->   ========== ending get words id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return pkgdescriptor

@router.get("/get_/user_words/{pkgname}")
async def get_user_words(pkgname:str, Authorization: Optional[str] = Header(None)):
    """
    Function to get the words into a specific package \n

    {\n
    pkgname: str  (package Code) \n
    }

    """    
    
    token=funcs.validating_token(Authorization)
    userId = token['userId']
    startinat = _getdatime_T()
    tm1 = dt.now()
    #print("========== starting get_user_words id: ", userId, " dt: ", startinat, " -> ", myfunctionname())
    global appNeo, session, log 

    #

    #print(f'input: {user_id} - {pkgname} for get_user_words')
    dtexec = funcs._getdatime_T()    
    if pkgname in ['', None]:        
        pkgname = dtexec 
    
    #pkgdescriptor["message"] = get_words(userId, pkgname, dtexec)
    #await awsleep(0)

    pkgdescriptor = get_words(userId, pkgname, 'words')

    diftime = str(dt.now() - tm1)
    print("==> ",startinat, ' - antes de neo4j:', '---', '- despues de neo4j:', '---', \
          " termina a ", _getdatime_T(), " tiempo exec: = ", diftime)
        
    #print("        ->   ========== ending get_user_words id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return pkgdescriptor


@router.post("/pst_/user_words/")
async def post_user_words(datas:ForNewPackage
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create new words package \n

    {\n
        idScat:int,  \n
        package:str=None, -> default = str(dt.now()),replace(' ', 'T')  = '2023-06-07T16:44:49.139573' \n
        capacity:int=8    \n
    }
    """
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']
    print("========== starting post_user_words id:  ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log

    #print("\n\n\n",'='*50," inicia -pst_userwords", _getdatime_T())

    #

    dtexec = funcs._getdatime_T()
    #print("datas:", datas)

    idCat = datas.idScat // 1000000
    idSCat = datas.idScat % 1000000
    pkgname = datas.package
    capacity = datas.capacity

    if not capacity or capacity < 8:
        capacity = 8

    if pkgname == None or pkgname.strip() in ['']:
        pkgname = dtexec 

    await awsleep(0)
    
    # getting SubCat, Category, and Organization values for Subcategory
    neo4j_statement_pre = "match (u:User {userId:'" + userId + "'})\n" + \
                            "-[rt:RIGHTS_TO]->(o:Organization)<-\n" + \
                            "[:SUBJECT]-(c:Category {idCat:" + str(idCat) + "})" + \
                            "<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) \n" + \
                            "return o.idOrg as idOrg, o.lSource as lSource, \n" + \
                                    "o.lTarget as lTarget, s.name as idSCatName limit 1" 
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting data previous to create new words package",
                        statement=neo4j_statement_pre,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    #print("\n\n\n",'='*50," termina -pst_userwords paso 1", _getdatime_T())    
    await awsleep(0)

    #npackage = []
    #continueflag = False
    for node in nodes:
        #continueflag = True
        sdict = dict(node) 
        lgSource = sdict["lSource"]
        lgTarget = sdict["lTarget"]
        idOrg = sdict["idOrg"]
        idSCatName = sdict["idSCatName"]        
        idSCatName = idSCatName.replace("/","").replace(" ","")    

    pkgwords = []
    if idSCat != 1:
        # new words package is required
        # we need to know which words are in open package to exclude of the new package  #w_idSCat
        pass
    neo4j_statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
            "optional match (sc)<-[:PACK_SUBCAT]-(pkg:Package {status:'open'})\n" + \
            "-[:PACKAGED]->(u) \n" + \
            "unwind pkg.words as pkgwords \n" + \
            "with collect(pkgwords) as pkgwords \n" + \
            "return pkgwords "

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting new words (step 1) for new package",
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())

    await awsleep(0)

    pkgwords = []
    for node in nodes:
        sdict = dict(node)
        pkgwords = sdict["pkgwords"]

    #print("\n\n\n",'='*50," termina -pst_userwords paso 2", _getdatime_T())
    
    if idSCat == 1:                              # words category is required

        neo4j_statement = "with " + str(pkgwords) + " as pkgwords \n" + \
                "match (u:User {userId:'" + userId + "'}) \n" + \
                "/* GETTING LEARNED WORDS */ \n" + \
                "match (c:Category {idCat:" + str(idCat) + "})-[:CAT_SUBCAT]\n" + \
                    "-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "optional match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM:Archived_M:\n" + \
                    lgSource + ":" + lgTarget +" {source:'" + lgSource + "', target:'" + lgTarget + "'})-\n" + \
                "[rUArcM:ARCHIVED_M]->(u) \n" + \
                "with u, pkgwords, c, sc, coalesce(arcM.words,['.']) as words \n" + \
                "unwind words as word \n" + \
                "with u, pkgwords, c, sc, collect(word) as words \n" + \
                "with u, c, sc, apoc.coll.union(pkgwords, words) as words" + \
                "/* GETTING NEW WORDS */ \n" + \
                "match (n:Word:" + lgSource + ") \n" + \
                "where not n.word in words \n" + \
                    " and exists {(n)-[tes:TRANSLATOR]->(s:Word:Spanish)}" + \
                "with u, n.word as word order by n.wordranking limit 20 \n" + \
                "with u, collect(word) as ewlist \n" + \
                "return u.userId as idUser, 'words' as subCat, \n" + \
                    "ewlist[0..8] as slSource "
        
                #"match (n)-[tes:TRANSLATOR]->(s:Word:Spanish) \n" + \
                #"with u, n, s, tes \n" + \
                #"order by n.wordranking, tes.sorted limit 100 \n" + \
                #"with u, n, collect(distinct s.word) as swlist \n" + \
                #"with u, collect(n.word) as ewlist, collect(swlist) as swlist \n" + \
                #"return u.userId as idUser, 'words' as subCat, \n" + \
                #    "ewlist[0..8] as slSource, \n" + \
                #    "swlist[0..8] as slTarget "

    else: # if idSCat != 1:                                   # other one subcategory is required
        #idSCatName = "w_SC_" + str(idCat * 1000000 + idSCat) 

        neo4j_statement = "with " + str(pkgwords) + " as pkgwords \n" + \
                "match (u:User {userId:'" + userId + "'}) \n" + \
                "/* getting learned words */ \n" + \
                "match (c:Category {idCat:" + str(idCat) + "})-[:CAT_SUBCAT]\n" + \
                    "-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "optional match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM:Archived_M)-\n" + \
                "[rUArcM:ARCHIVED_M]->(u) \n" + \
                "with u, pkgwords, c, sc, coalesce(arcM.words,['.']) as words \n" + \
                "unwind words as word \n" + \
                "with u, pkgwords, c, sc, collect(word) as words \n" + \
                "with u, c, sc, apoc.coll.union(pkgwords, words) as words" + \
                "/* getting new words */ \n" + \
                "match (sc)<-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ") \n" + \
                "where  not ew.word in words \n" + \
                    " and exists { (ew)-[:TRANSLATOR]->" + \
                            "(sw:ElemSubCat:" + lgTarget + ") } \n" + \
                "with sc, u, ew, scat \n" + \
                "order by scat.wordranking, ew.word  limit 20 \n" + \
                "with sc, u, collect(distinct ew.word) as ewlist \n" + \
                "return u.userId as idUser, sc.name as subCat, \n" + \
                        "ewlist[0.." + str(capacity) + "] as slSource \n" 
                # "swlist[0.." + str(capacity) + "] as slTarget"
                #+ \
                #"ewlist[0.." + str(capacity) + "] as slSource, " + \
                #"swlist[0.." + str(capacity) + "] as slTarget"
    #print(f"ne04j_state: {neo4j_statement}")
    await awsleep(0)
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting new words (step 2) for new package",
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())    


    #print("\n\n\n",'='*50," termina -pst_userwords paso 3", _getdatime_T())
    # creating the data structure to return it
    
    words = []
    for node in nodes:
        sdict = dict(node)        
        #npackage = []
        #prnFileName, prnLink = '', ''
        for gia, value in enumerate(sdict['slSource']):
            #npackage.append([value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink])
            words.append(value)

    print('\n\n\n',30*'=','lista de words pst_words:', words)
    #creating package data structure version del 20230703 tiene la versión anterior de esta sección
    if len(words) > 0:
        neo4j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                        "match (u:User {userId:'" + userId + "'}) \n" + \
                        "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                        "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                        "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                        "optional match (sc)<-[rpsubcat:PACK_SUBCAT]-(pkg:Package)-[:PACKAGED]->(u) \n" + \
                        "with u, sc, wordlist, toString(count(pkg) + 1) as foliopkg \n" + \
                        "merge (sc)<-[:PACK_SUBCAT]-\n" + \
                        "(pkg:Package {userId:'" + userId + "', packageId:'" + pkgname + "'})" + \
                        "-[pkgd:PACKAGED]->(u) \n" + \
                        "set pkg.words=wordlist, \n" + \
                            "pkg.idCat=" + str(idCat) + ", \n" + \
                            "pkg.idSCat=" + str(idSCat) + ", \n" + \
                            "pkg.status='open', pkg.SubCat='" + idSCatName + "', \n" + \
                            "pkg.label  = foliopkg, \n" + \
                            "pkg.source = '"+ lgSource + "', \n"  + \
                            "pkg.target = '"+ lgTarget + "', \n"  + \
                            "pkg.ctInsert = datetime() "  + \
                        "return count(pkg) as pkg_qty"

        nodes, log = neo4j_exec(session, userId,
                            log_description="creating new word package -> "+ pkgname,
                            statement=neo4j_statement, 
                            filename=__name__, 
                            function_name=myfunctionname())
        #                                                              end of create new data package

        # now, getting the package using the same endpoint function to return words package

        #print("\n\n\n",'='*50," finaliza -pst_userwords", _getdatime_T(), " y sigue get_words")
    await awsleep(0)
    
    pkgdescriptor = get_words(userId, pkgname)
    #else:
    #    pkgdescriptor = get_words(userId, pkgname)
    
    print("        ->   ========== ending post_user_words id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return pkgdescriptor #pkgname #pkgdescriptor



@router.post("/pst_/user_words4/")
async def post_user_words4(datas:ForNewPackage
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create the word list for level 4 (lvl_40_01) \n    
    
    {\n
        idScat:int,  \n
        package:str=None,  \n
        capacity:int=24    // 8, 16, 24, 32, 40 \n
    }
    """
    global appNeo, session
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']
    #print("========== starting post_user_words4 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    
    idSCat = datas.idScat

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000
    pkgname = datas.package
    capacity = datas.capacity    
    capacity = 12
    level = 'lvl_40_01'

    dtexec = funcs._getdatime_T()

    #wSCat = get_w_SCat (userId, pkgname, idCat, idSCat)
    #wSCat = wSCat[0]


    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + userId + "' as user_id, \n" + \
            str(capacity) + " as capacity \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "match (c:Category {idCat:" + str(idCat) + "})-[:CAT_SUBCAT]\n" + \
            "-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
            "optional match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM:Archived_M)-\n" + \
            "[rUArcM:ARCHIVED_M]->(u) \n" + \
            "with u.userId as userId, \n" + \
                "coalesce(arcM.words,['.']) as uwords, packageId, capacity, sc \n" + \
            "unwind uwords as words \n" + \
            "with sc, userId, collect(words) as words, packageId, capacity \n" + \
            "with sc, userId, words[0..capacity] as lwords, packageId, capacity \n" + \
            "match (u)-[rp:PACKAGED]-(pkg:Package {packageId:packageId})-[:PACK_SUBCAT]->(sc) \n" + \
            "set pkg.words40=case when pkg.status = 'open' \n" + \
                "then (pkg.words + lwords)[0..capacity] \n" + \
                "else lwords[0..capacity] end, \n" + \
                "pkg.ctUpdate = datetime('" + dtexec + "') \n" + \
            "set pkg.words40 = case when size(pkg.words40) = 9 \n" + \
                    "then pkg.words40[0..-1] \n" + \
                    "else pkg.words40 \n" + \
                "end \n" + \
            "return userId, packageId, pkg.words40 limit 1 "
    
            #"set pkg.words40 = apoc.coll.shuffle(pkg.words40) \n" + \
            #"with sc, userId, words, packageId, idCat, idSCat, capacity order by rand() \n" + \
            #"match (u2:User {userId:userId}) \n" + \
            #"match (sc)<-[PACK_SUBCAT]-(pkg2:Package {packageId:packageId})-[:PACKAGED]->(u2) \n" + \
            #"set pkg2.words40 = CASE WHEN not exists \n" + \
            #            "{(sc)<-[:SUBCAT_ARCHIVED_M]-(arcM:Archived_M)-[rUArcM:ARCHIVED_M]->(u2)} \n" + \
            #            "THEN pkg2.words40[0..-1] ELSE pkg2.words40 END \n" + \
            #"return userId, packageId, pkg2.words40 limit 1 "
    await awsleep(0)
    print("neo4j_statement:", neo4j_statement)
    
    nodes, log = neo4j_exec(session, userId,
                    log_description="post_user_words4 -level_40_ \n packageId: " + pkgname,
                    statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    # now, getting the package using the same endpoint function to return words package
    await awsleep(0)
    
    #result = get_user_words4(userId, pkgname, "words40")
    result = get_words(userId, pkgname, 'words40')

    print("        ->   ========== ending post_user_words4 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


@router.get("/get_/user_word_pronunciation/")
async def get_user_word_pronunciation(word:str, idWord:int):
    #                , Authorization: Optional[str] = Header(None)):    
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
        word:str, \n
        idWord: int
    """
    userId = '__publicPron__' #token['userId']
    #print("========== starting get_user_word_pronunciation id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log

    #token=funcs.validating_token(Authorization) 
    #

    #word = datas.word
    #idWord = datas.idNode

    statement = 'match (ws:WordSound {word: "' +  word + '"}) ' + \
                "where id(ws) = " + str(idWord) + " " + \
                "return ws.binfile limit 1"  # ws.word, ws.actived, 
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting pronunciation word: " + word,
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    await awsleep(0)
    
    for ele in nodes:
        elems = dict(ele)
    print("        ->   ========== ending get_user_word_pronunciation id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return Response(elems['ws.binfile'])


@router.get("/get_/word_sound_element/")
async def get_word_sound_element(word:str, idWord:str
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
        word:str, \n
        idWord: int
    """
    userId = '__publicPron__' #token['userId']
    #print("========== starting get_user_word_pronunciation id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log

    #token=funcs.validating_token(Authorization) 
    #

    #word = datas.word
    #idWord = datas.idNode

    statement = 'match (ws:WordSound {word: "' +  word + '"}) ' + \
                "where elementId(ws) = '" + idWord + "' \n" + \
                "return ws.binfile limit 1"  # ws.word, ws.actived, 
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting sound element - word: " + word,
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    await awsleep(0)
    
    for ele in nodes:
        elems = dict(ele)
    print("        ->   ========== ending get_word_sound_element: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return Response(elems['ws.binfile'])


@router.get("/get_/user_word_pron/{word} {idWord}")
def get_user_word_pron2(word:str, idWord:int
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
        word:str, \n
        idWord: int
    """

    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']
    #print("========== starting  get_user_word_pron2 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    global appNeo, session, log

    #

    statement = 'match (ws:WordSound {word: "' +  word + '"}) ' + \
                "where id(ws) = " + str(idWord) + " " + \
                "return ws.binfile limit 1"  # ws.word, ws.actived, 
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting pronunciation word: " + word,
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    for ele in nodes:
        elems = dict(ele)
    print("        ->   ========== ending get_user_word_pron2 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return Response(elems['ws.binfile'])


@router.get("/get_/user_words4_borrar/")
async def get_user_words4_borrar(idScat:int, package:str, capacity:int
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create the word list for level 4 (lvl_40_01) \n    
    
    {\n
    {  
        idScat:int,  \n
        package:str=None,  \n
        capacity:int=16    // 8, 16, 24, 32, 40 \n
    }
    """
    global appNeo, session
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']
    #print("========== starting post_user_words4 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    
    idSCat = idScat

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000
    pkgname = package
    capacity = capacity    

    level = 'lvl_40_01'

    dtexec = funcs._getdatime_T()

    #wSCat = get_w_SCat (userId, pkgname, idCat, idSCat)
    #wSCat = wSCat[0]

    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + userId + "' as user_id, \n" + \
            str(capacity) + " as capacity \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "match (c:Category {idCat:" + str(idCat) + "})-[:CAT_SUBCAT]\n" + \
            "-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
            "optional match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM:Archived_M)-\n" + \
            "[rUArcM:ARCHIVED_M]->(u) \n" + \
            "with u.userId as userId, \n" + \
                "coalesce(arcM.words,['.']) as uwords, packageId, capacity, sc \n" + \
            "unwind uwords as words \n" + \
            "with sc, userId, collect(words) as words, packageId, capacity \n" + \
            "with sc, userId, words[0..capacity] as lwords, packageId, capacity \n" + \
            "match (u)-[rp:PACKAGED]-(pkg:Package {packageId:packageId})-[:PACK_SUBCAT]->(sc) \n" + \
            "set pkg.words40=case when pkg.status = 'open' \n" + \
                "then (pkg.words + lwords)[0..capacity] \n" + \
                "else lwords[0..capacity] end, \n" + \
                "pkg.ctUpdate = datetime('" + dtexec + "') \n" + \
            "set pkg.words40 = case when size(pkg.words40) = 9 \n" + \
                    "then pkg.words40[0..-1] \n" + \
                    "else pkg.words40 \n" + \
                "end \n" + \
            "return userId, packageId, pkg.words40 limit 1 "
    await awsleep(0)
    #print("neo4j_statement:", neo4j_statement)
    
    nodes, log = neo4j_exec(session, userId,
                    log_description="post_user_words4 -level_40_ \n packageId: " + pkgname,
                    statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    # now, getting the package using the same endpoint function to return words package
    await awsleep(0)
    
    #result = get_user_words4(userId, pkgname, "words40")
    result = get_words(userId, pkgname, 'words40')

    print("        ->   ========== ending post_user_words4 id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


