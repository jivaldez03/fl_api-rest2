from fastapi import APIRouter, Response, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, myConjutationLink, get_list_element

from random import shuffle as shuffle

from app.model.md_params_oper import ForPackages as ForNewPackage

router = APIRouter()

def get_pronunciationId(words, packagename, userId):
    """
    Function to identify and return the id() of pronunciation file
    into the WordSound collection
    """
    # getting the WordSound id for each word and example
    neo4j_statement = "with " + str(list(words)) + " as wordlist " + \
                    "unwind wordlist as wordtext " + \
                    "match (pkg:Package {packageId:'" + packagename + "'})-\n" + \
                    "[:PACKAGED]-(u:User {userId: '"+ userId +"'}) \n" + \
                    "match(wp:WordSound {word:wordtext}) " + \
                    "where pkg.source in labels(wp) \n" + \
                    "return wp.word, id(wp) as idNode, wp.actived, wp.example, wp.Spanish"

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words pronunciation",
                        statement=neo4j_statement,
                        filename=__name__,
                        function_name=myfunctionname())
    result = []    
    for word in words:
        idNode = None
        example = ''
        example_target = ''
        for node in nodes:
            sdict = dict(node)
            if word == sdict['wp.word']:
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
def get_categories(Authorization: Optional[str] = Header(None)):
    """
    Function to get all categories and subcategories allowed for the user

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']
    
    neo4j_statement = "match (u:User {userId:'" + userId + "'})-[rt:RIGHTS_TO]-(o:Organization)\n" + \
                        "<-[:SUBJECT]-(c:Category)<-[:CAT_SUBCAT]-(s:SubCategory) \n" + \
                        "where exists \n" + \
                        "   {match (s)<-[:SUBCAT]-(es:ElemSubCat) \n" + \
                        "   where o.lSource in labels(es)} \n" + \
                        "with o,c, s.name as subcategory, s.idSCat as idSCat \n" + \
                        "order by o.idOrg, c.name, subcategory \n" + \
                        "return o.name, c.name as category, c.idCat as idCat, \n" + \
                                "collect(subcategory) as subcategories, collect(idSCat) as subid"     
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
    return {'message': listcat}


@router.get("/get_/dashboard/")
def get_dashboard_table(Authorization: Optional[str] = Header(None)):
    """
    Function to get how much has the user worked for each category

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    neo4j_statement = "match (es:Word:English) " + \
        "match (c:Category {idCat:1})<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "optional match (pkg:Package {userId:'" + userId + "',status:'close',idSCat:sc.idSCat}) " + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) " + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned, " + \
                "c.idCat as idCat, " + \
                "sc.idSCat as idSCat " + \
        "union " + \
        "match (pkg:Package {userId:'" + userId + "'}) " + \
        "with distinct pkg.idSCat as idSCats " + \
        "match (og:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + userId + "'}) " + \
        "match (og)<-[rsub:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:idSCats})-[esr]-(es:ElemSubCat:English) " + \
        "-[tr]-(ws:ElemSubCat:Spanish) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "order by sc.idSCat, c.name, sc.name " + \
        "optional match (pkg:Package {userId:'" + userId + "',status:'close',idSCat:sc.idSCat}) " + \
        "return c.name as CatName, " + \
                "sc.name as SCatName, " + \
                "wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned, " + \
                "c.idCat as idCat, " + \
                "sc.idSCat as idSCat"
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting data for dashboard table",
                        statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    
    listcat = []
    for node in nodes:
        listcat.append(dict(node))
        #print(dict(node))
    return {'message': listcat}


@router.get("/get_/config_uid/")
def get_config_uid(Authorization: Optional[str] = Header(None)):
    """"
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
    
    for node in nodes:
        sdict = dict(node)
    return sdict


@router.get("/get_/user_packagelist/{idSCat}")
def get_user_packagelist(idSCat:int, Authorization: Optional[str] = Header(None)):
    """
    Function to get opened package list in a specific SubCategory \n

    """
    global appNeo, session, log 

    token=funcs.validating_token(Authorization)
    userId = token['userId']


    statement = "match (u:User {userId:'" + userId + "'}) \n" + \
                "match (pkg:Package {userId: u.userId, status:'open', idSCat:" + str(idSCat) + "}) \n" + \
                "match (sc:SubCategory {idSCat:pkg.idSCat})-[]-(c:Category)-[:SUBJECT]->(o:Organization) \n" + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) \n" + \
                "with u, pkg, c,  pkgS.level as level, \n" + \
                "max(((pkgS.grade[0] / toFloat(pkgS.grade[1]) - 1 ) * 100)) as grade, \n" + \
                "coalesce(o.ptgmaxerrs,100.0-85.0) as maxerrs \n" + \
                "with u, pkg, c,  max(level + '-,-' + coalesce(toString(grade),'0')) as level, \n" + \
                "count(DISTINCT level) as levs, maxerrs \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName, \n" + \
                "pkg.SubCat as SCatName, \n" + \
                "pkg.idSCat as idSCat, \n" + \
                "split(level,'-,-')[0] as level, \n" + \
                "toFloat(split(level,'-,-')[1]) as grade, levs, maxerrs"
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
        }
        
        listPack.append(ndic)
    return {'message': listPack}


def get_words(userId, pkgname):
    global app, session, log

    npackage = []

    level = 'lvl_10_01'  # elementary level
    
    neo4j_statement = "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "', idSCat:1}) " + \
                        "unwind pkg.words as pkgwords  \n" + \
                        "with pkg.packageId as pkgname, pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkgname, pkglabel, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkgname, pkglabel, n, collect(distinct s.word) as swlist  \n" + \
                        "with pkgname, pkglabel, \n" + \
                            "collect(COALESCE(n.kowcomplete, [])) as kow, \n" + \
                            "collect(COALESCE(n.kowc, [])) as kowc, \n" + \
                            "collect(n.word) as ewlist, \n" + \
                            "collect(swlist) as swlist \n" + \
                        "optional match (pkgS:PackageStudy {packageId:pkgname}) \n" + \
                        "return 'words' as subCat, 1 as idSCat, pkglabel as label, " + \
                            "COALESCE(max(pkgS.level), '" + level + "') as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, kow, kowc, swlist as slTarget  \n" + \
                        "union " + \
                        "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "'}) \n" + \
                        "unwind pkg.words as pkgwords  " + \
                        "match (s:SubCategory {idSCat:pkg.idSCat})-[scat:SUBCAT]-" + \
                            "(ew:ElemSubCat {word:pkgwords})-[:TRANSLATOR]->(sw:ElemSubCat)  \n" + \
                        "with pkg, s, ew, sw, scat order by scat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(ew.word) as ewlist, collect(sw.word) as swlist  \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) \n" + \
                        "with pkg, s, ewlist, swlist, COALESCE(max(pkgS.level), '" + level + "') as level, linktitles, links \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "pkg.level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, [] as kow, [] as kowc, swlist as slTarget"

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for user and pkgId="+pkgname,
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())  
    
    # creating the structure to return data
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
        for gia, value in enumerate(sdict['slSource']):
            prnReference = funcs.get_list_element(sdict["linktitles"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            ltarget = funcs.get_list_element(sdict["slTarget"],gia)
            if type(ltarget) == type(list()):
                pass
            else:
                ltarget = [ltarget]
            npackage.append([value, ltarget, gia + 1, prnReference, prnLink])
            words.append(value) # (value, sdict['kow']))
    lpron = get_pronunciationId(words, pkgname, userId)
    result = []
    result2 = []

    # we have a list with neo4 values, we need to add some elements like:
    # - pronunciation with sentence example (lpron)
    # - kind of word and link for conjungation verbs
    # - location or more information for countries, skeleton, etc 

    for gia, element in enumerate(npackage): # element Strcuture:[value, ltarget, gia + 1, prnReference, prnLink]
        # kow section
        if len(kow) == 0:
            isitaverb = (False, [])
        else:
            isitaverb = (('vb' in str(kowc[gia]).lower()), kow[gia])
        if isitaverb[0]:
            conjLink = myConjutationLink(element[0])
        else:
            conjLink = ''
        s_kow = {"type": "kow"
                        , "position" : "source"
                        , "apply_link": isitaverb[0] # is it a verb?
                        , "link" : conjLink
                        , "title": get_list_element(isitaverb[1],0) # kow[gia] # list of different kind of word for the same word
                        }
        s_object={"type": "location"
                        , "position" : "source"
                        , "apply_link": True if element[3] else False
                        , "link" : element[4]
                        , "title": element[3]
                        }
        ladds = []
        for ele in [s_kow, s_object]:
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

    return pkgdescriptor

@router.get("/get_/user_words/{pkgname}")
def get_user_words(pkgname:str, Authorization: Optional[str] = Header(None)):
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
    """
    npackage = []    

    #"n.kowcomplete as kow, \n" + \
    neo4j_statement = "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "', idSCat:1}) " + \
                        "unwind pkg.words as pkgwords  \n" + \
                        "with pkg.packageId as pkgname, pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkgname, pkglabel, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkgname, pkglabel, n, collect(distinct s.word) as swlist  \n" + \
                        "with pkgname, pkglabel, \n" + \
                            "collect(COALESCE(n.kowcomplete, [])) as kow, \n" + \
                            "collect(COALESCE(n.kowc, [])) as kowc, \n" + \
                            "collect(n.word) as ewlist, \n" + \
                            "collect(swlist) as swlist \n" + \
                        "optional match (pkgS:PackageStudy {packageId:pkgname}) \n" + \
                        "return 'words' as subCat, 1 as idSCat, pkglabel as label, " + \
                            "COALESCE(max(pkgS.level), 'lvl_01_01') as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, kow, kowc, swlist as slTarget  \n" + \
                        "union " + \
                        "match (u:User {userId:'" + userId + "'})-[:PACKAGED]-\n" + \
                        "(pkg:Package {packageId:'" + pkgname + "'}) \n" + \
                        "unwind pkg.words as pkgwords  " + \
                        "match (s:SubCategory {idSCat:pkg.idSCat})-[scat:SUBCAT]-" + \
                            "(ew:ElemSubCat {word:pkgwords})-[:TRANSLATOR]->(sw:ElemSubCat)  \n" + \
                        "with pkg, s, ew, sw, scat order by scat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(ew.word) as ewlist, collect(sw.word) as swlist  \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) \n" + \
                        "with pkg, s, ewlist, swlist, COALESCE(max(pkgS.level), 'lvl_01_01') as level, linktitles, links \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "pkg.level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, [] as kow, [] as kowc, swlist as slTarget"

    print(f"neo4j:state: {neo4j_statement}")
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=neo4j_statement)    

    # creating the structure to return data
    pkgdescriptor = {}
    words = []
    kow, kowc = [], []
    print(f"nodes type: {type(nodes)}")
    print(f"logs for nodes: {log}")
    for node in nodes:
        sdict = dict(node)        
        npackage = []
        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":sdict["maxlevel"]
        }
        kow = sdict["kow"]
        kowc = sdict["kowc"]
        for gia, value in enumerate(sdict['slSource']):
            prnReference = funcs.get_list_element(sdict["linktitles"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            ltarget = funcs.get_list_element(sdict["slTarget"],gia)
            if type(ltarget) == type(list()):
                pass
            else:
                ltarget = [ltarget]
            npackage.append([value, ltarget, gia + 1, prnReference, prnLink])
            words.append(value) # (value, sdict['kow']))
    lpron = get_pronunciationId(words, npackage)
    result = []      
    for gia, element in enumerate(npackage):        
        element.append(lpron[gia])
        if len(kow) == 0:
            isitaverb = (False, [])
        else:
            isitaverb = (('vb' in str(kowc[gia]).lower()), kow[gia])
        section_extra = {"kow": isitaverb[1] # kow[gia] # list of different kind of word for the same word
                        , "verb": isitaverb[0] # is it a verb?
                        }

        element.append(section_extra)
        result.append(element)
    """
    #pkgdescriptor["message"] = get_words(userId, pkgname, dtexec)
    pkgdescriptor = get_words(userId, pkgname)

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

    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    dtexec = funcs._getdatime_T()

    idSCat = datas.idScat
    pkgname = datas.package
    capacity = datas.capacity

    if not capacity or capacity < 8:
        capacity = 8

    if pkgname in ['', None]:        
        pkgname = dtexec 

    # getting SubCat, Category, and Organization values for Subcategory
    neo4j_statement_pre = "match (o:Organization)<-[]-(c:Category)" + \
                            "<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                            "return o.idOrg as idOrg, o.lSource as lSource, " + \
                                    "o.lTarget as lTarget, s.name as idSCatName limit 1" 
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting data previous to create new words package",
                        statement=neo4j_statement_pre,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    npackage = []
    #continueflag = False
    for node in nodes:
        #continueflag = True
        sdict = dict(node) 
        lgSource = sdict["lSource"]
        lgTarget = sdict["lTarget"]
        idOrg = sdict["idOrg"]
        idSCatName = sdict["idSCatName"]        
        idSCatName = idSCatName.replace("/","").replace(" ","")        

    # new words package is required
    # we need to know which words are in open package to exclude of the new page
    neo4j_statement = "match (u:User {userId:'" + userId + "'}) " + \
            "optional match (pkg:Package {status:'open', idSCat:" + str(idSCat) + "})-[:PACKAGED]->(u) " + \
            "unwind pkg.words as pkgwords " + \
            "with collect(pkgwords) as pkgwords " + \
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
        
    if idSCat == 1:                                                     # words category is required
        neo4j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                "match (u:User {userId:'" + userId + "'}) " + \
                "match (n:Word:" + lgSource + ")-[tes:TRANSLATOR]->" + \
                "(s:Word:" + lgTarget + ") " + \
                "where  (not n.word in u.words or u.words is NULL) and not n.word in pkgwords " + \
                "with u, n, s, tes " + \
                "order by n.wordranking, tes.sorded " + \
                "with u, n, collect(distinct s.word) as swlist " + \
                "with u, collect(n.word) as ewlist, collect(swlist) as swlist " + \
                "return u.alias as idUser, 'words' as subCat, " + \
                        "ewlist[0.." + str(capacity) + "] as slSource, " + \
                        "swlist[0.." + str(capacity) + "] as slTarget"
    else: # if idSCat != 1:                                            # other one subcategory is required            
        neo4j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                "match (u:User {userId:'" + userId + "'}) " + \
                "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                "match (s)-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                    "(sw:ElemSubCat:" + lgTarget + ") " + \
                "where  (not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL) and not ew.word in pkgwords " + \
                "with s, u, ew, sw, scat " + \
                "order by scat.wordranking, ew.wordranking, ew.word " + \
                "with s, u, collect(ew.word) as ewlist, collect(sw.word) as swlist " + \
                "return u.userId as idUser, s.name as subCat, " + \
                        "ewlist[0.." + str(capacity) + "] as slSource, " + \
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


    # creating the data structure to return it
    words = []
    for node in nodes:
        sdict = dict(node)        
        #npackage = []
        #prnFileName, prnLink = '', ''
        for gia, value in enumerate(sdict['slSource']):
            #npackage.append([value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink])
            words.append(value)

    #creating data structure
    neo4j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                    "match (u:User {userId:'" + userId + "'}) \n" + \
                    "merge (pkg:Package {userId:'" + userId + "', packageId:'" + pkgname + "'})" + \
                    "-[pkgd:PACKAGED]->(u) \n" + \
                    "set pkg.words=wordlist, pkg.idSCat=" + str(idSCat) + ", \n" + \
                        "pkg.status='open', pkg.SubCat='" + idSCatName + "', \n" + \
                        "pkg.label=' ', \n" + \
                        "pkg.source = '"+ lgSource + "', \n"  + \
                        "pkg.target = '"+ lgTarget + "', \n"  + \
                        "pkg.ctInsert = datetime('"+ dtexec + "') "  + \
                    "return count(pkg) as pkg_qty"

    nodes, log = neo4j_exec(session, userId,
                        log_description="creating new word package -> "+ pkgname,
                        statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    #                                                              end of create new data package

    # now, getting the package using the same endpoint function to return words package
    pkgdescriptor = get_words(userId, pkgname)
    return pkgdescriptor #pkgname #pkgdescriptor


#@router.get("/get_/user_words4/{user_id} {pkgname}")
def get_user_words4(userId:str, pkgname:str, level:str):
    """"
    internal function, it is not an endpoint
    """
    global appNeo, session, log

    npackage = []
    
    neo4j_statement = "match (pkg:Package {packageId:'" + pkgname + "', idSCat:1}) \n" + \
                        "unwind pkg." + level + " as pkgwords  \n" + \
                        "with pkg.packageId as pkgname, pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkgname, pkglabel, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkgname, pkglabel, n, collect(distinct s.word) as swlist  \n" + \
                        "with pkgname, pkglabel, \n" + \
                            "collect(COALESCE(n.kowcomplete, [])) as kow, \n" + \
                            "collect(COALESCE(n.kowc, [])) as kowc, \n" + \
                            "collect(n.word) as ewlist, \n" + \
                            "collect(swlist) as swlist \n" + \
                        "optional match (pkgS:PackageStudy {packageId:pkgname}) \n" + \
                        "return 'words' as subCat, 1 as idSCat, pkglabel as label, " + \
                            "max(pkgS.level) as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, kow, kowc, swlist as slTarget  \n" + \
                        "union " + \
                        "match (pkg:Package {packageId:'" + pkgname + "'}) \n" + \
                        "unwind pkg." + level + " as pkgwords  " + \
                        "match (s:SubCategory {idSCat:pkg.idSCat})-[scat:SUBCAT]-" + \
                            "(ew:ElemSubCat {word:pkgwords})-[:TRANSLATOR]->(sw:ElemSubCat)  \n" + \
                        "with pkg, s, ew, sw, scat order by scat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(ew.word) as ewlist, collect(sw.word) as swlist  \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) \n" + \
                        "with pkg, s, ewlist, swlist, max(pkgS.level) as level, linktitles, links order by rand() \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "pkg.level as maxlevel, linktitles, links, \n" + \
                            "ewlist as slSource, [] as kow, [] as kowc, swlist as slTarget \n"
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="get_user_words4 for level: " + level + \
                                        "\n getting words package: " + pkgname,
                        statement=neo4j_statement,
                        filename=__name__, 
                        function_name=myfunctionname())
        
    # creating the structure to return data
    pkgdescriptor = {}
    words = []
    kow, kowc = [], []

    for node in nodes:
        sdict = dict(node)        
        npackage = []

        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":('lvl_50_01' if level == 'words50' else 'lvl_40_01') # sdict["maxlevel"]
        }
        kow = sdict["kow"]
        kowc = sdict["kowc"]
        for gia, value in enumerate(sdict['slSource']):
            prnReference = funcs.get_list_element(sdict["linktitles"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            ltarget = funcs.get_list_element(sdict["slTarget"],gia)
            if type(ltarget) == type(list()):
                pass
            else:
                ltarget = [ltarget]
            npackage.append([value, ltarget, gia + 1, prnReference, prnLink])
            words.append(value) # (value, sdict['kow']))
    lpron = get_pronunciationId(words, pkgname, userId)
    result = []      
    for gia, element in enumerate(npackage):        
        element.append(lpron[gia])
        if len(kow) == 0:
            isitaverb = (False, [])
        else:
            isitaverb = (('vb' in str(kowc[gia]).lower()), kow[gia])
        section_extra = {"kow": isitaverb[1] # kow[gia] # list of different kind of word for the same word
                        , "verb": isitaverb[0] # is it a verb?
                        }
        element.append(section_extra)
        result.append(element)        

    #print('before shuffle')
    shuffle(result)
    #print('after shuffle')
    pkgdescriptor["message"] = result
    return pkgdescriptor


@router.post("/pst_/user_words4/")
def post_user_words4(datas:ForNewPackage
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
    pkgname = datas.package
    capacity = datas.capacity    
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    level = 'lvl_40_01'

    dtexec = funcs._getdatime_T()

    if idSCat == 1:
        wSCat = 'words'
    else:
        wSCat = 'w_idSCat_' + str(idSCat)

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
            "set pkg.words40=(pkg.words + lwords)[0..capacity], \n" + \
                "pkg.status='open', \n" + \
                "pkg.ctUpdate = datetime('" + dtexec + "') \n" + \
            "create (pkgS:PackageStudy {level:'" + level + "'})-[rs:STUDY]->(pkg) \n" + \
            "set pkgS.studying_dt = datetime('" + dtexec + "'), \n" + \
                "pkgS.grade = [0,capacity] \n" + \
            "with userId, packageId, pkg \n" + \
            "match (u2:User {userId:userId}) \n" + \
            "where u2.words is null \n" + \
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
    return result


@router.post("/pst_/user_words5/")
def post_user_words5(datas:ForNewPackage
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
        wSCat = 'w_idSCat_' + str(idSCat)

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
    return result


@router.get("/get_/user_word_pron/{word} {idWord}")
def get_user_word_pron2(word, idWord
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

    statement = "match (ws:WordSound {word: '" +  word + "'}) " + \
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
        return Response(elems['ws.binfile'])

