from fastapi import APIRouter, Response, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, myConjutationLink, get_list_element,_getdatime_T, get_list_elements

from random import shuffle as shuffle

from app.model.md_params_oper import ForPackages as ForNewPackage

router = APIRouter()

def get_w_SCat(userId, pkgname, idCat=None, idSCat=None):    
    if idCat == None:
        neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "'})\n" + \
                "-[:PACKAGED]->(u:User {userId:'" + userId + "'}) \n" + \
                "match (pkg)-[:PACK_SUBCAT]->(sc:SubCategory {idSCat:pkg.idSCat})-\n" + \
                "[:CAT_SUBCAT]->(c:Category)-[:SUBJECT]->(o:Organization)<-[:RIGHTS_TO]-(u) \n" + \
                "return pkg.source as pkgsource, sc.idSCat as idSCat, c.idCat as idCat"    

    else:
        neo4j_statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                "-[:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "match (pkg:Package {packageId:'" + pkgname + "'})\n" + \
                "-[:PACKAGED]->(u) \n" + \
                "return pkg.source as pkgsource"    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting new words (step 1) for new package",
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())

    pkgsource = ""
    for node in nodes:
        sdict = dict(node)
        pkgsource = sdict["pkgsource"]        

    if idCat == None:
        idCat = sdict["idCat"]
        idSCat = sdict["idSCat"]

    if idSCat == 1:
        wSCat = pkgsource
    else:
        wSCat = "w_SC_" + str(idCat * 1000000 + idSCat) # 'w_idSCat_' + str(idSCat)

    print("\n\n\n","="*50,"wsCat =", wSCat, idCat, idSCat)
    return wSCat

def get_pronunciationId(words, packagename, userId):
    """
    Function to identify and return the id() of pronunciation file
    into the WordSound collection
    """
    # getting the WordSound id for each word and example
    neo4j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                    "unwind wordlist as wordtext \n" + \
                    "match (pkg:Package {packageId:'" + packagename + "'})-\n" + \
                    "[:PACKAGED]-(u:User {userId: '"+ userId +"'}) \n" + \
                    "optional match(wp:WordSound {word:wordtext}) \n" + \
                    "where pkg.source in labels(wp) \n" + \
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

    return result


@router.get("/get_/categories/")
async def get_categories(Authorization: Optional[str] = Header(None)):
    """
    Function to get all categories and subcategories allowed for the user

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
    
    neo4j_statement = "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]-(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category)<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:1}) \n" + \
                        "with o, c, s.name as subcategory, c.idCat * 1000000 + s.idSCat as idCS \n" + \
                        "order by o.idOrg, c.name, subcategory \n" + \
                        "return o.name, c.name as category, c.idCat as idCat, \n" + \
                                "collect(subcategory) as subcategories, collect(idCS) as subid \n" + \
                        "union \n" + \
                        "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]-(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category)<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "where exists \n" + \
                        "   {match (s)<-[:SUBCAT]-(es:ElemSubCat) \n" + \
                        "   where o.lSource in labels(es)} \n" + \
                        "with o,c, s.name as subcategory, c.idCat * 1000000 + s.idSCat as idCS  \n" + \
                        "order by o.idOrg, c.name, subcategory \n" + \
                        "return o.name, c.name as category, c.idCat as idCat, \n" + \
                                "collect(subcategory) as subcategories, collect(idCS) as subid"
    
    #print('cats-subcats:', neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting categories for the user",
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
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
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return {'message': listcat}


@router.get("/get_/dashboard/")
async def get_dashboard_table(Authorization: Optional[str] = Header(None)):
    """
    Function to get how much has the user worked for each category

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    neo4j_statement =  "match (u:User {userId:'" + userId + "'})-[:RIGHTS_TO]->(o:Organization)<-\n" + \
        "[:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) \n" + \
        "match (es:Word) where o.lSource in labels(es) \n" + \
        "with u, c, sc, count(es) as wordsSC \n" + \
        "optional match (sc)<-[]-(pkg:Package {userId:'" + userId + "',status:'close',idSCat:sc.idSCat}) \n" + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) \n" + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, \n" + \
                "sum(size(pkg.words)) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS \n" + \
        "union \n" + \
        "match (pkg:Package {userId:'" + userId + "'}) \n" + \
        "with distinct pkg.idSCat as idSCats \n" + \
        "match (og:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + userId + "'}) \n" + \
        "match (og)<-[rsub:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-\n" + \
        "(sc:SubCategory {idSCat:idSCats})-[esr]-(es:ElemSubCat:English) " + \
        "-[tr]-(ws:ElemSubCat:Spanish) \n" + \
        "with c, sc, count(es.word) as wordsSC \n" + \
        "order by sc.idSCat, c.name, sc.name \n" + \
        "optional match (pkg:Package {userId:'" + userId + "',status:'close',idSCat:sc.idSCat}) \n" + \
        "return c.name as CatName, \n" + \
                "sc.name as SCatName, \n" + \
                "wordsSC as totalwords, \n" + \
                "sum(size(pkg.words)) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS"
    neo4j_statement =  "match (u:User {userId:'" + userId + "'})-[:RIGHTS_TO]->(o:Organization)<-\n" + \
        "[:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) \n" + \
        "match (es:Word) where o.lSource in labels(es) \n" + \
        "with u, o, c, sc, count(es) as wordsSC \n" + \
        "optional match (sc)<-[:PACK_SUBCAT]-" + \
            "(pkg:Package {userId:'" + userId + "',status:'closed',idSCat:sc.idSCat, source:o.lSource}) \n" + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) \n" + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, \n" + \
                "sum(size(pkg.words)) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS \n" + \
        "union \n" + \
        "match (pkg:Package {userId:'" + userId + "'}) \n" + \
        "with distinct pkg.idSCat as idSCats \n" + \
        "match (og:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + userId + "'}) \n" + \
        "match (og)<-[rsub:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-\n" + \
        "(sc:SubCategory {idSCat:idSCats})-[esr]-(es:ElemSubCat) " + \
        "-[tr]-(ws:ElemSubCat) \n" + \
        "where og.lSource in labels(es) and og.lTarget in labels(ws) \n" + \
        "with c, sc, count(es) as wordsSC \n" + \
        "order by sc.idSCat, c.name, sc.name \n" + \
        "optional match (sc)<-[:PACK_SUBCAT]-" + \
                "(pkg:Package {userId:'" + userId + "',status:'closed'}) \n" + \
        "return c.name as CatName, \n" + \
                "sc.name as SCatName, \n" + \
                "wordsSC as totalwords, \n" + \
                "sum(size(pkg.words)) as learned, \n" + \
                "c.idCat * 1000000 + sc.idSCat as idSCat, \n" + \
                "c.idCat as idCat, \n" + \
                "sc.idSCat as idCS"
    
    #print(f"neo4j_state: {neo4j_statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting data for dashboard table",
                        statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    listcat = []
    msg = ""
    try:
        for node in nodes:
            listcat.append(dict(node))
    except Exception as error:
        msg = "error on empty nodes - no iterable"

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), msg,"\n\n")
    return {'message': listcat}


@router.get("/get_/config_uid/")
async def get_config_uid(Authorization: Optional[str] = Header(None)):
    """
    Function to get some options or data of the user

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    neo4j_statement = "match (us:User {userId:'" + userId + "'})-[r]-(rep:FirstContact) \n" + \
                    "return us.userId as userId \n" + \
                        ", us.name as name \n" + \
                        ", us.birth_year as birth_year, us.month_year as month_year \n" + \
                        ", us.country_birth as country_birth, us.country_res as country_res \n" + \
                        ", us.nativeLang as native_lang \n" + \
                        ", toString(us.ctInsert) as us_ctInsert, us.email as usemail, us.defaultCap as capacity \n" + \
                        ", rep.contactId as contactId \n" + \
                        ", rep.name as contactName \n" + \
                        ", rep.phone as contactPhone \n" + \
                        ", rep.email as contactEmail \n" 
    
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
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(), msg,"\n\n")
    return sdict


@router.get("/get_/user_packagelist/{idSCat}")
async def get_user_packagelist(idSCat:int, Authorization: Optional[str] = Header(None)):
    """
    Function to get opened package list in a specific SubCategory \n

    """
    global appNeo, session, log 

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000

    #print('idcattt:', idCat, 'idSCat:', idSCat)
    token=funcs.validating_token(Authorization)
    userId = token['userId']    

    statement = "match (u:User {userId:'" + userId + "'})\n" + \
                "-[rt:RIGHTS_TO]-(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "-[:PACK_SUBCAT]-(pkg:Package {userId: u.userId, status:'open'}) \n" + \
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
                "toFloat(split(level,'-,-')[1]) as grade, levs, maxerrs, pkg.label as labelname"
    
    #"max(((pkgS.grade[0] / toFloat(pkgS.grade[1]) - 1 ) * 100)) as grade, \n" + \

    #print(statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
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
                , 'distinct_levs': sdict["levs"]
                , 'maxlevel': maxlevel # sdict["level"]
                , 'ptg_errors' : ptg_errors
                , 'maxptg_errs':sdict["maxerrs"]
                , 'label':sdict["labelname"]
        }
        
        listPack.append(ndic)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return {'message': listPack}


@router.get("/get_/user_package_st/{packageId}")
async def get_user_package_st(packageId:str, Authorization: Optional[str] = Header(None)):
    """
    Function to get package level \n

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
    
    statement = "match (u:User {userId:'" + userId + "'})-[]-\n" + \
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
    
    #print(statement)
    #"min(((pkgS.grade[0] / toFloat(pkgS.grade[1]) - 1 ) * 100)) as grade, \n" + \
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting opened packages list",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
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
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return {'message': listPack}

def get_words(userId, pkgname):
    global app, session, log

    #print('='*50," inicia get_userwords", _getdatime_T())

    npackage = []

    level = 'null'  # elementary level

    #print("\n\n\n*******************************\nuuuuserid:", userId, pkgname)    
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "'})" + \
                        "-[:PACKAGED]-(u:User {userId:'" + userId + "'})\n" + \
                        "-[rt:RIGHTS_TO]-(o:Organization)<-[:SUBJECT]\n" + \
                        "-(c:Category)<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:1})<-[:PACK_SUBCAT]-(pkg)\n" + \
                        "unwind pkg.words as pkgwords  \n" + \
                        "with pkg, pkg.packageId as pkgname, o.ptgmaxerrs as maxerrs, \n" + \
                            " pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, n, reverse(collect(s.word)) as swlist \n" + \
                        "with pkg, pkgname, pkglabel, maxerrs, \n" + \
                            "collect(COALESCE(n.ckow, [])) as kow, \n" + \
                            "collect(COALESCE(n.ckowb_complete, [])) as kowc, \n" + \
                            "collect(COALESCE(n.cword_ref, [])) as wordref, \n" + \
                            "collect(COALESCE(n.wrword_ref, '')) as wr_wordref, \n" + \
                            "collect(COALESCE(n.wr_kow, [])) as wr_kow, \n" + \
                            "collect(n.word) as ewlist, \n" + \
                            "collect(swlist) as swlist \n" + \
                        "optional match (pkgS:PackageStudy)-[]-(pkg) \n" + \
                            "where pkgS.ptgerror <= maxerrs \n" + \
                        "return 'words' as subCat, pkg.idSCat as idSCat, pkglabel as label, " + \
                            "COALESCE(max(pkgS.level), '" + level + "') as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, kow, kowc, wordref, swlist as slTarget, wr_wordref, wr_kow  \n" + \
                        "union \n" + \
                        "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "'})\n" + \
                        "-[:PACK_SUBCAT]->(s:SubCategory)-[:CAT_SUBCAT]->(cat:Category)\n" + \
                        "-[:SUBJECT]->(org:Organization) \n" + \
                        "unwind pkg.words as pkgwords  " + \
                        "match(s)-[rscat:SUBCAT]-(ew:ElemSubCat {word:pkgwords})\n" + \
                        "-[:TRANSLATOR]->(sw:ElemSubCat) \n" + \
                        "where pkg.source in labels(ew) and pkg.target in labels(sw) \n" + \
                        "with org, pkg, s, ew, collect(distinct sw.word) as sw, rscat \n" + \
                        "order by rscat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with org, pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(COALESCE(ew.ckow, [])) as kow, \n" + \
                            "collect(COALESCE(ew.ckowb_complete, [])) as kowc, \n" + \
                            "collect(COALESCE(ew.cword_ref, [])) as wordref, \n" + \
                            "collect(COALESCE(ew.wrword_ref, '')) as wr_wordref, \n" + \
                            "collect(COALESCE(ew.wr_kow, [])) as wr_kow, \n" + \
                            "collect(ew.word) as ewlist, collect(sw) as swlist \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) where pkgS.ptgerror <= org.ptgmaxerrs \n" + \
                        "with pkg, s, ewlist, swlist, kow, kowc, wordref, \n" + \
                        "COALESCE(max(pkgS.level), '" + level + "') as level, linktitles, links, wr_wordref, wr_kow \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, kow, kowc, wordref, swlist as slTarget, wr_wordref, wr_kow"
    
    #print("--neo4j_statement:", neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for user and pkgId="+pkgname,
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())  
    
    # creating the structure to return data   # ESTA SECCIÓN HASTA EL FINAL ES IGUAL GER_USER_WORDS4
    pkgdescriptor = {}
    words = []
    kow, kowc = [], []
    for node in nodes:
        sdict = dict(node)        
        npackage = []
        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":sdict["maxlevel"]
        }
        kow = sdict["kow"]
        kowc = sdict["kowc"]
        wrkowc = sdict["wr_kow"]
        wr_wordref = sdict["wr_wordref"]
        for gia, value in enumerate(sdict['slSource']):
            prnReference = funcs.get_list_element(sdict["linktitles"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            ltarget = funcs.get_list_element(sdict["slTarget"],gia)
            wordref = funcs.get_list_element(sdict["wordref"],gia)
            if type(ltarget) == type(list()):
                pass
            else:
                ltarget = [ltarget]
            npackage.append([value, ltarget, gia + 1, prnReference, prnLink, wordref])
            words.append(value) # (value, sdict['kow']))
            #print("----------------------------------------------wwword:", value)

    #print('gggget_pronunciationId(:', words, pkgname, userId)
          
    lpron = get_pronunciationId(words, pkgname, userId)

    #print(' lpront:', lpron)
          
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
        
        s_kow_verb = {'title': None}
        kowv, kowo = [], []
        if isitaverb[0] or 'v ' in str(wrkowc[gia]): # si es verbo
            if not isitaverb[0]:
                isitaverb[0] = 1
            #print("lene elemente:", len(element[5]), element[5])
            if wr_wordref[gia] != "":
                conjLink = myConjutationLink(wr_wordref[gia])   # wordref
            elif element[5] == [''] or len(element[5]) == 0:  ## es el infintivo del verbo o no hay referencia ligada
                conjLink = myConjutationLink(element[0])      # c' wordref 
            else:
                conjLink = myConjutationLink(element[5][0])   # c' wordref            
                
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
                    elif "v past" in str(wrkowc[gia]):
                        kowv.append('past - verb')
                    elif  "v past p" in str(wrkowc[gia]):
                        kowv.append('past part - verb')
                    else:
                        kowv.append('verb')
            s_kow_verb = {"type": "kow_verb"
                        , "position" : "source"
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
        s_object={"type": "location"
                        , "position" : "source" # source para tarjeta superio, 'target' para tarjeta inferior
                        , "apply_link": True if element[3] else False
                        , "link" : element[4]
                        , "title": element[3]
                        }
        ladds = []
        for ele in [s_kow_verb, s_kow, s_object]:
            if ele["title"] != None:
                ladds.append(ele)

        new_element = {'word': element[0]
                        , "tranlate": element[1]
                        , "position": element[2]
                        , "pronunciation": lpron[gia]
                        , "additional": ladds
                        }        

        element.append(lpron[gia])
        element.append([s_kow, s_object])
        result.append(element)
        result2.append(new_element)
    pkgdescriptor["message"] = result2

    #print('='*50," finaliza -get_words", _getdatime_T())

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return pkgdescriptor

@router.get("/get_/user_words/{pkgname}")
async def get_user_words(pkgname:str, Authorization: Optional[str] = Header(None)):
    """
    Function to get the words into a specific package \n

    {\n
    pkgname: str  (package Code) \n
    }

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    #print(f'input: {user_id} - {pkgname} for get_user_words')
    dtexec = funcs._getdatime_T()    
    if pkgname in ['', None]:        
        pkgname = dtexec 
    
    #pkgdescriptor["message"] = get_words(userId, pkgname, dtexec)
    pkgdescriptor = get_words(userId, pkgname)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return pkgdescriptor


@router.post("/pst_/user_words/")
def post_user_words(datas:ForNewPackage
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create new words package \n

    {\n
        idScat:int,  \n
        package:str=None, -> default = str(dt.now()),replace(' ', 'T')  = '2023-06-07T16:44:49.139573' \n
        capacity:int=8    \n
    }
    """
    global appNeo, session, log

    #print("\n\n\n",'='*50," inicia -pst_userwords", _getdatime_T())

    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    dtexec = funcs._getdatime_T()

    idCat = datas.idScat // 1000000
    idSCat = datas.idScat % 1000000
    pkgname = datas.package
    capacity = datas.capacity

    if not capacity or capacity < 8:
        capacity = 8

    if pkgname in ['', None]:        
        pkgname = dtexec 


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
        # we need to know which words are in open package to exclude of the new page  #w_idSCat
        neo4j_statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                    "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                    "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                    "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                "optional match (pkg:Package {status:'open', idSCat:" + str(idSCat) + "})\n" + \
                "-[:PACKAGED]->(u) \n" + \
                "unwind pkg.words as pkgwords \n" + \
                "with collect(pkgwords) as pkgwords \n" + \
                "return pkgwords "
        

        nodes, log = neo4j_exec(session, userId,
                            log_description="getting new words (step 1) for new package",
                            statement=neo4j_statement,
                            filename=__name__, 
                            function_name=myfunctionname())

        pkgwords = []
        for node in nodes:
            sdict = dict(node)
            pkgwords = sdict["pkgwords"]


    #print("\n\n\n",'='*50," termina -pst_userwords paso 2", _getdatime_T())
    
    if idSCat == 1:                              # words category is required        
        neo4j_statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                "set u." + lgSource + " = CASE WHEN u." + lgSource + " is null \n" + \
                    "THEN [] \n" + \
                    "ELSE u." + lgSource + " END \n" + \
                "with u \n" + \
                "match (u)-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT] \n" + \
                "-(c:Category {idCat:" + str(idCat) + "}) \n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat: 1}) \n" + \
                "optional match (u)<-[:PACKAGED]-(pkg:Package {status:'open'})-[:PACK_SUBCAT]->(sc) \n" + \
                "with u, pkg, coalesce(pkg.words,['.']) as pkgw \n" + \
                "unwind pkgw as pkgword \n" + \
                "with u, collect(pkgword) as pkgwords \n" + \
                "match (n:Word:" + lgSource + ") \n" + \
                "where not n.word in pkgwords  \n" + \
                "with u, n, n.word in u." + lgSource + " as alreadystored \n" + \
                "where alreadystored = False \n" + \
                "match (n)-[tes:TRANSLATOR]->(s:Word:Spanish) \n" + \
                "with u, n, s, tes \n" + \
                "order by n.wordranking, tes.sorted limit 100 \n" + \
                "with u, n, collect(distinct s.word) as swlist \n" + \
                "with u, collect(n.word) as ewlist, collect(swlist) as swlist \n" + \
                "return u.userId as idUser, 'words' as subCat, \n" + \
                "ewlist[0..8] as slSource, \n" + \
                "swlist[0..8] as slTarget "
        

    else: # if idSCat != 1:                                   # other one subcategory is required
        idSCatName = "w_SC_" + str(idCat * 1000000 + idSCat) 

        neo4j_statement = "with " + str(pkgwords) + " as pkgwords \n" + \
                "match (u:User {userId:'" + userId + "'}) \n" + \
                "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "})-\n" + \
                "[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                    "(sw:ElemSubCat:" + lgTarget + ") \n" + \
                "where  (not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL) \n" + \
                    "and not ew.word in pkgwords \n" + \
                "with s, u, ew, collect(distinct sw.word) as sw, scat \n" + \
                "order by scat.wordranking, ew.wordranking, ew.word \n" + \
                "with s, u, collect(distinct ew.word) as ewlist, collect(sw) as swlist \n" + \
                "return u.userId as idUser, s.name as subCat, \n" + \
                        "ewlist[0.." + str(capacity) + "] as slSource, \n" + \
                        "swlist[0.." + str(capacity) + "] as slTarget"
        
        neo4j_statement = "with " + str(pkgwords) + " as pkgwords \n" + \
                "match (u:User {userId:'" + userId + "'}) \n" + \
                "set u." + idSCatName + " = CASE WHEN u." + idSCatName + " is null \n" + \
                    "THEN [] \n" + \
                    "ELSE u." + idSCatName + " END \n" + \
                "with  u, pkgwords \n" + \
                "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "})-\n" + \
                "[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                    "(sw:ElemSubCat:" + lgTarget + ") \n" + \
                "where  (not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL) \n" + \
                    "and not ew.word in pkgwords \n" + \
                "with s, u, ew, collect(distinct sw.word) as sw, scat \n" + \
                "order by scat.wordranking, ew.wordranking, ew.word \n" + \
                "with s, u, collect(distinct ew.word) as ewlist, collect(sw) as swlist \n" + \
                "return u.userId as idUser, s.name as subCat, \n" + \
                        "ewlist[0.." + str(capacity) + "] as slSource, \n" + \
                        "swlist[0.." + str(capacity) + "] as slTarget"
        
                #+ \
                #"ewlist[0.." + str(capacity) + "] as slSource, " + \
                #"swlist[0.." + str(capacity) + "] as slTarget"
        #print(f"ne04j_state: {ne04j_statement}")
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

    #creating data structure  version del 20230703 tiene la versión de esta sección
    neo4j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                    "match (u:User {userId:'" + userId + "'}) \n" + \
                    "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                    "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                    "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
                    "merge (sc)<-[:PACK_SUBCAT]-\n" + \
                    "(pkg:Package {userId:'" + userId + "', packageId:'" + pkgname + "'})" + \
                    "-[pkgd:PACKAGED]->(u) \n" + \
                    "set pkg.words=wordlist, pkg.idSCat=" + str(idSCat) + ", \n" + \
                        "pkg.status='open', pkg.SubCat='" + idSCatName + "', \n" + \
                        "pkg.label  = pkg.packageId , \n" + \
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

    pkgdescriptor = get_words(userId, pkgname)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return pkgdescriptor #pkgname #pkgdescriptor


#@router.get("/get_/user_words4/{user_id} {pkgname}")
def get_user_words4(userId:str, pkgname:str, level:str):
    """
    internal function, it is not an endpoint
    """
    global appNeo, session, log

    npackage = []
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', idSCat:1}) \n" + \
                        "unwind pkg." + level + " as pkgwords  \n" + \
                        "with pkg, pkg.packageId as pkgname, pkgwords as pkgwords \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where pkg.source in labels(n) and pkg.target in labels(s) \n" + \
                        "with pkg, pkgname, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkg, pkgname, n, reverse(collect(distinct s.word)) as swlist  \n" + \
                        "with pkg, pkgname, \n" + \
                            "collect(COALESCE(n.ckow, [])) as kow, \n" + \
                            "collect(COALESCE(n.ckowb_complete, [])) as kowc, \n" + \
                            "collect(COALESCE(n.cword_ref, [])) as wordref, \n" + \
                            "collect(COALESCE(n.wrword_ref, '')) as wr_wordref, \n" + \
                            "collect(COALESCE(n.wr_kow, [])) as wr_kow, \n" + \
                            "collect(n.word) as ewlist, \n" + \
                            "collect(swlist) as swlist \n" + \
                        "optional match (pkg)<-[:STUDY]-(pkgS:PackageStudy) \n" + \
                        "return 'words' as subCat, 1 as idSCat, pkg.label as label, " + \
                            "max(pkgS.level) as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, kow, kowc, wordref, swlist as slTarget, wr_wordref, wr_kow \n" + \
                        "union " + \
                        "match (pkg:Package {packageId:'" + pkgname + "'}) \n" + \
                        "unwind pkg." + level + " as pkgwords  " + \
                        "match (pkg)-[:PACK_SUBCAT]->(s:SubCategory)<-[scat:SUBCAT]-" + \
                            "(ew:ElemSubCat {word:pkgwords})-[:TRANSLATOR]->(sw:ElemSubCat)  \n" + \
                        "where pkg.source in labels(ew) and pkg.target in labels(sw) \n" + \
                        "with pkg, s, ew, collect(distinct sw.word) as sw, scat \n" + \
                            "order by scat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(ew.word) as ewlist, collect(sw) as swlist  \n" + \
                        "optional match (pkg)<-[rps:STUDY]-(pkgS:PackageStudy) \n" + \
                        "with pkg, s, ewlist, swlist, max(pkgS.level) as level, linktitles, links order by rand() \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, [] as kow, [] as kowc, [] as wordref, \n" + \
                            "swlist as slTarget, [] as wr_wordref, [] as wr_kow \n"


    #print("--neo4j_statement:", neo4j_statement)
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for user and pkgId="+pkgname,
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())  
    
    # creating the structure to return data # ESTA SECCIÓN HASTA EL FINAL ES IGUAL A GET_WORDS

    pkgdescriptor = {}
    words = []
    kow, kowc = [], []
    for node in nodes:
        sdict = dict(node)        
        npackage = []
        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":sdict["maxlevel"]
        }
        kow = sdict["kow"]
        kowc = sdict["kowc"]
        wrkowc = sdict["wr_kow"]
        wr_wordref = sdict["wr_wordref"]
        for gia, value in enumerate(sdict['slSource']):
            prnReference = funcs.get_list_element(sdict["linktitles"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            ltarget = funcs.get_list_element(sdict["slTarget"],gia)
            wordref = funcs.get_list_element(sdict["wordref"],gia)
            if type(ltarget) == type(list()):
                pass
            else:
                ltarget = [ltarget]
            npackage.append([value, ltarget, gia + 1, prnReference, prnLink, wordref])
            words.append(value) # (value, sdict['kow']))
    lpron = get_pronunciationId(words, pkgname, userId)

    #print('***************************************\nlennnn lpron:', len(lpron), lpron)
    result = []
    result2 = []

    # we have a list with neo4 values, we need to add some elements like:
    # - pronunciation with sentence example (lpron)
    # - kind of word and link for conjungation verbs
    # - location or more information for countries, skeleton, etc 

    for gia, element in enumerate(npackage): # element Strcuture:[value, ltarget, gia + 1, prnReference, prnLink]
        # kow section
        if len(kow) == len(npackage):
            if len(kow[gia]) == 0:
                isitaverb = [False, []]
            else:
                verbis = str(kowc[gia]).lower().replace("adverb","xxxxx")
                isitaverb = [('verb' in verbis), kowc[gia]]
            
            s_kow_verb = {'title': None}
            kowv, kowo = [], []
            if isitaverb[0] or 'v ' in str(wrkowc[gia]): # si es verbo
                if not isitaverb[0]:
                    isitaverb[0] = 1
                #print("lene elemente:", len(element[5]), element[5])
                if wr_wordref[gia] != "":
                    conjLink = myConjutationLink(wr_wordref[gia])   # wordref
                elif element[5] == [''] or len(element[5]) == 0:  ## es el infintivo del verbo o no hay referencia ligada
                    conjLink = myConjutationLink(element[0])      # c' wordref 
                else:
                    conjLink = myConjutationLink(element[5][0])   # c' wordref            
                    
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
                        elif "v past" in str(wrkowc[gia]):
                            kowv.append('past - verb')
                        elif  "v past p" in str(wrkowc[gia]):
                            kowv.append('past part - verb')
                        else:
                            kowv.append('verb')
                s_kow_verb = {"type": "kow_verb"
                            , "position" : "source"
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
        else:
            s_kow_verb, s_kow= {'title': None}, {'title': None}
            
        s_object={"type": "location"
                        , "position" : "source" # source para tarjeta superio, 'target' para tarjeta inferior
                        , "apply_link": True if element[3] else False
                        , "link" : element[4]
                        , "title": element[3]
                        }
        ladds = []
        for ele in [s_kow_verb, s_kow, s_object]:
            if ele["title"] != None:
                ladds.append(ele)

        new_element = {'word': element[0]
                        , "tranlate": element[1]
                        , "position": element[2]
                        , "pronunciation": lpron[gia]
                        , "additional": ladds
                        }        

        element.append(lpron[gia])
        element.append([s_kow, s_object])
        result.append(element)
        result2.append(new_element)
    pkgdescriptor["message"] = result2
    print("========== id: GET_USER_WORDS4", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return pkgdescriptor


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
    
    idSCat = datas.idScat

    idCat = idSCat // 1000000
    idSCat = idSCat % 1000000
    pkgname = datas.package
    capacity = datas.capacity    
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    level = 'lvl_40_01'

    dtexec = funcs._getdatime_T()

    """
    # we need to know which words are in open package to exclude of the new page  #w_idSCat
    neo4j_statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                "-[rt:RIGHTS_TO]->(o:Organization)<-[:SUBJECT]\n" + \
                "-(c:Category {idCat:" + str(idCat) + "})\n" + \
                "<-[:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "})\n" + \
            "match (pkg:Package {packageId:'" + pkgname + "'})\n" + \
            "-[:PACKAGED]->(u) \n" + \
            "return pkg.source as pkgsource"    

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting new words (step 1) for new package",
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())

    pkgsource = ""
    for node in nodes:
        sdict = dict(node)
        pkgsource = sdict["pkgsource"]        

    if idSCat == 1:
        wSCat = pkgsource
    else:
        wSCat = "w_SC_" + str(idCat * 1000000 + idSCat) # 'w_idSCat_' + str(idSCat)
    """
    wSCat = get_w_SCat (userId, pkgname, idCat, idSCat)

    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + wSCat + "' as wSCat, \n" + \
            "'" + userId + "' as user_id, \n" + \
            str(capacity) + " as capacity \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "set u." + wSCat + "= CASE WHEN u." + wSCat + " = [] \n" + \
                "THEN null \n" + \
                "ELSE u." + wSCat + " END \n" + \
            "with u.userId as userId, COALESCE(u[wSCat],['.']) as uwords, packageId, wSCat, capacity \n" + \
            "unwind uwords as words \n" + \
            "with userId, words, packageId, wSCat, capacity order by rand() \n" + \
            "with userId, collect(words) as words, packageId, wSCat, capacity \n" + \
            "with userId, words[0..capacity] as lwords, packageId, wSCat, capacity \n" + \
            "match (u)-[rp:PACKAGED]-(pkg:Package {packageId:packageId}) \n" + \
            "set pkg.words40=(pkg.words + lwords)[0..capacity], \n" + \
                "pkg.status='open', \n" + \
                "pkg.ctUpdate = datetime('" + dtexec + "') \n" + \
            "create (pkgS:PackageStudy {level:'" + level + "'})-[rs:STUDY]->(pkg) \n" + \
            "set pkgS.studying_dt = datetime('" + dtexec + "'), \n" + \
                "pkgS.grade = [0,capacity] \n" + \
            "with userId, packageId, pkg, wSCat \n" + \
            "match (u2:User {userId:userId}) \n" + \
            "where u2." + wSCat + " is null \n" + \
            "match (pkg2:Package {packageId:packageId})-[]-(u2) \n" + \
            "set pkg2.words40 = pkg.words40[0..-1] \n" + \
            "return userId, packageId limit 1 "
    nodes, log = neo4j_exec(session, userId,
                    log_description="post_user_words4 -level_40_ \n packageId: " + pkgname,
                    statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    # now, getting the package using the same endpoint function to return words package
    result = get_user_words4(userId, pkgname, "words40")
    print("========== id: PST_USER_WORDS4", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return result


@router.post("/pst_/user_words5/")
async def post_user_words5(datas:ForNewPackage
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create the word list for level 5 (lvl_50_01) \n    
    
    {\n
        idScat:int,  \n
        package:str=None,  \n
        capacity:int=24    // 8, 16, 24, 32, 40 \n
    }
    """
    global appNeo, session, log
    
    idSCat = datas.idScat
    pkgname = datas.package
    capacity = datas.capacity    
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    level = 'lvl_50_01'

    dtexec = funcs._getdatime_T()
    if idSCat == 1:
        wSCat = 'words'
    else:
        wSCat = 'w_SC_' + str(idSCat)

    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + wSCat + "' as wSCat, \n" + \
            "'" + userId + "' as user_id, \n" + \
            str(capacity) + " as capacity \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "with u.userId as userId, COALESCE(u[wSCat],['.']) as uwords, packageId, wSCat, capacity \n" + \
            "unwind uwords as words \n" + \
            "with userId, words, packageId, wSCat, capacity order by rand() \n" + \
            "with userId, collect(words) as words, packageId, wSCat, capacity \n" + \
            "with userId, words[0..capacity] as lwords, packageId, wSCat, capacity \n" + \
            "match (u)-[rp:PACKAGED]-(pkg:Package {packageId:packageId}) \n" + \
            "set pkg.words50=(pkg.words + lwords)[0..capacity], \n" + \
                "pkg.status='open', \n" + \
                "pkg.ctUpdate = datetime('" + dtexec + "') \n" + \
            "create (pkgS:PackageStudy {level:'" + level + "'})-[rs:STUDY]->(pkg) \n" + \
            "set pkgS.studying_dt = datetime('" + dtexec + "'), \n" + \
                "pkgS.grade = [0,capacity] \n" + \
            "with userId, packageId, pkg \n" + \
            "match (u2:User {userId:userId}) \n" + \
            "where u2.words is null \n" + \
            "match (pkg2:Package {packageId:packageId})-[]-(u2) \n" + \
            "set pkg2.words50 = pkg.words50[0..-1] \n" + \
            "return userId, packageId limit 1 "
    
    nodes, log = neo4j_exec(session, userId,
                    log_description="post_user_words5 -level_50_ \n packageId: " + pkgname, 
                    statement=neo4j_statement, 
                    filename=__name__, 
                    function_name=myfunctionname())
    
    # now, getting the package using the same endpoint function to return words package
    result = get_user_words4(userId, pkgname, "words50")
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return result


@router.get("/get_/user_word_pronunciation/")
async def get_user_word_pronunciation(word:str, idWord:int):
    #                , Authorization: Optional[str] = Header(None)):    
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
        word:str, \n
        idNode: int
    """
    global appNeo, session, log

    #token=funcs.validating_token(Authorization) 
    userId = '__public__' #token['userId']

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
    for ele in nodes:
        elems = dict(ele)
        print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
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
    global appNeo, session, log

    token=funcs.validating_token(Authorization) 
    userId = token['userId']

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
        print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
        return Response(elems['ws.binfile'])

