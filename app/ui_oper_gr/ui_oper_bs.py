from fastapi import APIRouter, Response
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs

router = APIRouter()

def get_pronunciationId(words, npackage):
    # getting the WordSound id for each word and example
    ne04j_statement = "with " + str(list(words)) + " as wordlist " + \
                    "unwind wordlist as wordtext " + \
                    "match(wp:WordSound:English {word:wordtext}) " + \
                    "return wp.word, id(wp) as idNode, wp.actived, wp.example"  # wp.binfile,
    
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words pronunciation",
                        statement=ne04j_statement)
    result = []
    for gia, element in enumerate(npackage):
        #binfile = None
        idNode = None
        example = ''
        for node in nodes:
            sdict = dict(node)
            if element[0] == sdict['wp.word']:
                idNode = sdict["idNode"]
                example = sdict.get('wp.example', '')
                break
        dict_pronunciation = {'example': example,
                            'pronunciation': idNode } # binfile.decode("ISO-8859-1")} #utf-8")}
        element.append(dict_pronunciation)
        #element.insert(len(element)-1, dict_pronunciation)
        result.append(element)

        #    npackage.append((value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink))
        #    words.append(value)
    return result


@router.get("/get_/categories/{user_id}")
def get_categories(user_id):
    global appNeo, session, log, user
    """
    listcat = [{ 'category': 'Anathomy'
                        , 'idCat': 'cat.01.01'
                        , 'subcategories' : [
                            {'subcategory': 'human body' , 'idSCat': 'scat.01.01'}
                            , {'subcategory': 'human skeleton' , 'idSCat': 'scat.01.02'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.01.00'}
                        ]
                }
               ]
    """

    ne04j_statement = "match (o:Organization {idOrg:'DTL-01'})<-[]-(c:Category)<--(s:SubCategory) " + \
                        "with c, s.name as subcategory, s.idSCat as idSCat " + \
                        "order by c.name, subcategory " + \
                        "return c.name as category, c.idCat as idCat, " + \
                                "collect(subcategory) as subcategories, collect(idSCat) as subid" 
    
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement)
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


@router.get("/get_/dashboard/{user_id}")
def get_dashboard_table(user_id):
    global appNeo, session, log, user

    neo4j_statement = "match (es:Word:English) " + \
        "match (c:Category {idCat:1})<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "optional match (pkg:Package {userId:'" + user_id + "',status:'close',idSCat:sc.idSCat}) " + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) " + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned, " + \
                "c.idCat as idCat, " + \
                "sc.idSCat as idSCat " + \
        "union " + \
        "match (pkg:Package {userId:'" + user_id + "'}) " + \
        "with distinct pkg.idSCat as idSCats " + \
        "match (og:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + user_id + "'}) " + \
        "match (og)<-[rsub:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:idSCats})-[esr]-(es:ElemSubCat:English) " + \
        "-[tr]-(ws:ElemSubCat:Spanish) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "order by sc.idSCat, c.name, sc.name " + \
        "optional match (pkg:Package {userId:'" + user_id + "',status:'close',idSCat:sc.idSCat}) " + \
        "return c.name as CatName, " + \
                "sc.name as SCatName, " + \
                "wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned, " + \
                "c.idCat as idCat, " + \
                "sc.idSCat as idSCat"
    # "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) " + \
    #print(f"dashboard: {neo4j_statement}")
    nodes, log = neo4j_exec(session, user_id,
                 log_description="getting data for dashboard table",
                 statement=neo4j_statement)
    listcat = []
    for node in nodes:
        listcat.append(dict(node))
        #print(dict(node))
    return {'message': listcat}


@router.get("/get_/config_uid/{user_id}")
def get_config_uid(user_id):
    global appNeo, session, log, user

    neo4j_statement = "match (us:User {userId:'" + user_id + "'})-[r]-(rep:FirstContact) \n" + \
                    "return us.userId as userId\n" + \
                        ", us.name as name\n" + \
                        ", us.birth_year as birth_year, us.month_year as month_year\n" + \
                        ", us.country_birth as country_birth, us.country_res as country_res\n" + \
                        ", us.nativeLang as native_lang\n" + \
                        ", toString(us.ctInsert) as us_ctInsert, us.email as usemail, us.defaultCap as capacity\n" + \
                        ", rep.contactId as contactId\n" + \
                        ", rep.name as contactName\n" + \
                        ", rep.phone as contactPhone\n" + \
                        ", rep.email as contactEmail\n" 
                    #"return us {.*}, rep {.*}"
    
    nodes, log = neo4j_exec(session, user_id,
                 log_description="getting user data ",
                 statement=neo4j_statement)    
    
    for node in nodes:
        sdict = dict(node)
    return sdict


@router.get("/get_/user_words/{user_id} {pkgname}")
def get_user_words(user_id:str, pkgname:str):
    global appNeo, session, log, user

    #print(f'input: {user_id} - {pkgname} for get_user_words')
    dtexec = funcs._getdatime_T()    
    if pkgname in ['', None]:        
        pkgname = dtexec 

    npackage = []    
    ne04j_statement = "match (pkg:Package {packageId:'" + pkgname + "', idSCat:1}) " + \
                        "unwind pkg.words as pkgwords  \n" + \
                        "with pkg.packageId as pkgname, pkg.label as pkglabel, pkgwords as pkgwords, \n" + \
                            "pkg.source as source, pkg.target as target \n" + \
                        "match (n:Word {word:pkgwords})-[tes:TRANSLATOR]->(s:Word)  \n" + \
                        "where source in labels(n) and target in labels(s) \n" + \
                        "with pkgname, pkglabel, n, s, tes order by n.wordranking, tes.sorded \n" + \
                        "with pkgname, pkglabel, n, collect(distinct s.word) as swlist  \n" + \
                        "with pkgname, pkglabel, collect(n.word) as ewlist, collect(swlist) as swlist \n" + \
                        "optional match (pkgS:PackageStudy {packageId:pkgname}) \n" + \
                        "return 'words' as subCat, 1 as idSCat, pkglabel as label, " + \
                            "max(pkgS.level) as maxlevel, [] as linktitles, [] as links, \n" + \
                            "ewlist as slSource, swlist as slTarget  \n" + \
                        "union " + \
                        "match (pkg:Package {packageId:'" + pkgname + "'}) \n" + \
                        "unwind pkg.words as pkgwords  " + \
                        "match (s:SubCategory {idSCat:pkg.idSCat})-[scat:SUBCAT]-" + \
                            "(ew:ElemSubCat {word:pkgwords})-[:TRANSLATOR]->(sw:ElemSubCat)  \n" + \
                        "with pkg, s, ew, sw, scat order by scat.wordranking, ew.wordranking, ew.word  \n" + \
                        "with pkg, s, collect(ew.link_title) as linktitles, collect(ew.link) as links,  \n" + \
                            "collect(ew.word) as ewlist, collect(sw.word) as swlist  \n" + \
                        "optional match (pkg)-[rps:STUDY]-(pkgS:PackageStudy) \n" + \
                        "with pkg, s, ewlist, swlist, max(pkgS.level) as level, linktitles, links \n" + \
                        "return s.name as subCat, s.idSCat as idSCat, pkg.label as label, " + \
                            "pkg.level as maxlevel, linktitles, links, ewlist as slSource, swlist as slTarget"
                        

    #print(f"neo4j:state: {ne04j_statement}")
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement)
    
        
    # creating the structure to return data
    pkgdescriptor = {}
    words = []
    print(f"nodes type: {type(nodes)}")
    print(f"logs for nodes: {log}")
    for node in nodes:
        sdict = dict(node)        
        npackage = []
        pkgdescriptor = {"packageId": pkgname
                          , "label": sdict["label"]
                          , "maxlevel":sdict["maxlevel"]
        }
        for gia, value in enumerate(sdict['slSource']):
            prnFileName = funcs.get_list_element(sdict["links"], gia)
            prnLink     = funcs.get_list_element(sdict["links"], gia)
            npackage.append([value, funcs.get_list_element(sdict["slTarget"],gia), gia + 1, prnFileName, prnLink])
            words.append(value)

    result = get_pronunciationId(words, npackage)

    pkgdescriptor["message"] = result
    return pkgdescriptor


@router.post("/pst_/user_words/{user_id} {idSCat}")
def post_user_words(user_id:str, idSCat:int, pkgname:str=None, capacity:int=8):
    global appNeo, session, log, user

    dtexec = funcs._getdatime_T()
    if pkgname in ['', None]:        
        pkgname = dtexec 

    # getting SubCat, Category, and Organization values for Subcategory
    ne04j_statement_pre = "match (o:Organization)<-[]-(c:Category)" + \
                            "<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                            "return o.idOrg as idOrg, o.lSource as lSource, " + \
                                    "o.lTarget as lTarget, s.name as idSCatName limit 1" 
    
    nodes, log = neo4j_exec(session, user,
                        log_description="getting new words package for user",
                        statement=ne04j_statement_pre)
        
    #print(f"nodes : {sdict} , {len(sdict)}")
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
    ne04j_statement = "match (u:User {userId:'" + user_id + "'}) " + \
            "optional match (pkg:Package {status:'open', idSCat:" + str(idSCat) + "})-[:PACKAGED]->(u) " + \
            "unwind pkg.words as pkgwords " + \
            "with collect(pkgwords) as pkgwords " + \
            "return pkgwords "
    nodes, log = neo4j_exec(session, user,
                    log_description="getting words for user",
                    statement=ne04j_statement)
    pkgwords = []
    for node in nodes:
        sdict = dict(node)
        pkgwords = sdict["pkgwords"]

    print(f"sdict for neo: {pkgwords}")     
    if idSCat == 1:                                                     # words category is required
        ne04j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                "match (u:User {userId:'" + user_id + "'}) " + \
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
        ne04j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                "match (u:User {userId:'" + user_id + "'}) " + \
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
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement)    


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
    ne04j_statement = "with " + str(list(words)) + " as wordlist \n" + \
                    "match (u:User {userId:'" + user_id + "'}) \n" + \
                    "merge (pkg:Package {userId:'" + user_id + "', packageId:'" + pkgname + "'})" + \
                    "-[pkgd:PACKAGED]->(u) \n" + \
                    "set pkg.words=wordlist, pkg.idSCat=" + str(idSCat) + ", \n" + \
                        "pkg.status='open', pkg.SubCat='" + idSCatName + "', \n" + \
                        "pkg.source = '"+ lgSource + "', \n"  + \
                        "pkg.tarjet = '"+ lgTarget + "', \n"  + \
                        "pkg.ctInsert = datetime('"+ dtexec + "') "  + \
                    "return count(pkg) as pkg_qty"

    nodes, log = neo4j_exec(session, user,
                        log_description="getting words pronunciation",
                        statement=ne04j_statement)
    #                                                              end of create new data package

    # now, getting the package using the same endpoint function to return words package
    result = get_user_words(user_id, pkgname)
    return result #pkgdescriptor


@router.post("/pst_/user_words4/{user_id} {pkgname} {idSCat}")
def post_user_words4(user_id:str, pkgname:str, idSCat:int, capacity:int=24, level:str='lev04_01'):
    global appNeo, session, log, user

    print(f'input-4: {user_id} - {pkgname} for get_user_words4')
    dtexec = '05_' + funcs._getdatime_T()           # 'w_idSCat_1' as wSCat,  "1 as idSCat, \n" + \
    if idSCat == 1:
        wSCat = 'words'
    else:
        wSCat = 'w_idSCat_' + str(idSCat)

    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + wSCat + "' as wSCat, \n" + \
            "'" + user_id + "' as user_id, " + str(capacity) + " as capacity, \n" + \
            "'" + dtexec + "' as dtexec \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "with u.userId as userId, u[wSCat] as uwords, packageId, wSCat, capacity, dtexec \n" + \
            "unwind uwords as words \n" + \
            "with userId, words, packageId, dtexec, wSCat, capacity order by rand() \n" + \
            "with userId, collect(words) as words, packageId, wSCat, capacity, dtexec \n" + \
            "with userId, words[0..capacity] as lwords, packageId, wSCat, capacity, dtexec \n" + \
            "match (u)-[rp:PACKAGED]-(pkgSource:Package {packageId:packageId}) \n" + \
            "merge (pkg:Package {packageId: dtexec, userId: userId})-[pkgd:PACKAGED]->(u) \n" + \
            "set pkg.words=(pkgSource.words + lwords)[0..capacity], \n" + \
                "pkg.idSCat=pkgSource.idSCat, \n" + \
                "pkg.status='open', \n" + \
                "pkg.SubCat=pkgSource.SubCat, \n" + \
                "pkg.source = pkgSource.source, \n" + \
                "pkg.target = pkgSource.target, \n" + \
                "pkg.ctInsert = datetime() \n" + \
            "return userId, pkg.packageId as packageId limit 1" 
                # ", pkgSource.packageId, \n" +  \"
                # "pkg.words, lwords, pkgSource.words,  wSCat, capacity, dtexec"

    nodes, log = neo4j_exec(session, user,
                    log_description="getting words for user level 4",
                    statement=neo4j_statement)
    pkgwords = []
    for node in nodes:
        pkgwords = dict(node)
        # pkgwords = sdict["pkgwords"]
    
    # print(f'params for l45: {user_id} {pkgwords}')
    # now, getting the package using the same endpoint function to return words package
    result = get_user_words(user_id, pkgwords["packageId"])
    return result



@router.post("/pst_/user_words5/{user_id} {pkgname} {idSCat}")
def post_user_words5(user_id:str, pkgname:str, idSCat:int, capacity:int=24, level:str='lev05_01'):
    global appNeo, session, log, user

    print(f'input-5: {user_id} - {pkgname} for get_user_words5')
    dtexec = '05_' + funcs._getdatime_T()           # 'w_idSCat_1' as wSCat,  "1 as idSCat, \n" + \
    if idSCat == 1:
        wSCat = 'words'
    else:
        wSCat = 'w_idSCat_' + str(idSCat)

    neo4j_statement = "with '" + pkgname + "' as packageId, \n" + \
            "'" + wSCat + "' as wSCat, \n" + \
            "'" + user_id + "' as user_id, " + str(capacity) + " as capacity, \n" + \
            "'" + dtexec + "' as dtexec \n" + \
            "match (u:User {userId:user_id}) \n" + \
            "with u.userId as userId, u[wSCat] as uwords, packageId, wSCat, capacity, dtexec \n" + \
            "unwind uwords as words \n" + \
            "with userId, words, packageId, dtexec, wSCat, capacity order by rand() \n" + \
            "with userId, collect(words) as words, packageId, wSCat, capacity, dtexec \n" + \
            "with userId, words[0..capacity] as lwords, packageId, wSCat, capacity, dtexec \n" + \
            "match (u)-[rp:PACKAGED]-(pkgSource:Package {packageId:packageId}) \n" + \
            "merge (pkg:Package {packageId: dtexec, userId: userId})-[pkgd:PACKAGED]->(u) \n" + \
            "set pkg.words=(pkgSource.words + lwords)[0..capacity], \n" + \
                "pkg.idSCat=pkgSource.idSCat, \n" + \
                "pkg.status='open', \n" + \
                "pkg.SubCat=pkgSource.SubCat, \n" + \
                "pkg.source = pkgSource.source, \n" + \
                "pkg.target = pkgSource.target, \n" + \
                "pkg.ctInsert = datetime() \n" + \
            "return userId, pkg.packageId as packageId limit 1" 
                # ", pkgSource.packageId, \n" +  \"
                # "pkg.words, lwords, pkgSource.words,  wSCat, capacity, dtexec"

    nodes, log = neo4j_exec(session, user,
                    log_description="getting words for user level 5",
                    statement=neo4j_statement)
    pkgwords = []
    for node in nodes:
        pkgwords = dict(node)
        # pkgwords = sdict["pkgwords"]
    
    # print(f'params for l45: {user_id} {pkgwords}')
    # now, getting the package using the same endpoint function to return words package
    result = get_user_words(user_id, pkgwords["packageId"])
    return result

@router.get("/get_/user_words_vAnterior/{user_id} {idSCat}")
def get_user_words_va(user_id:str, idSCat:int, new_package:int=0, pkgname:str=None, capacity:int=8):
    global appNeo, session, log, user

    dtexec = funcs._getdatime_T()    
    if pkgname in ['', None]:        
        pkgname = dtexec 

    # getting SubCat, Category, and Organization values
    ne04j_statement_pre = "match (o:Organization)<-[]-(c:Category)" + \
                            "<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                            "return o.idOrg as idOrg, o.lSource as lSource, " + \
                                    "o.lTarget as lTarget, s.name as idSCatName limit 1" 
    
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement_pre)
        
    #print(f"nodes : {sdict} , {len(sdict)}")
    npackage = []
    continueflag = False
    for node in nodes:
        continueflag = True
        sdict = dict(node) 
        lgSource = sdict["lSource"]
        lgTarget = sdict["lTarget"]
        idOrg = sdict["idOrg"]
        idSCatName = sdict["idSCatName"]        
        idSCatName = idSCatName.replace("/","").replace(" ","")        

    if new_package == 0:                                                    # getting previous package
        if idSCat == 1:
            ne04j_statement = "match (pkg:Package {packageId:'" + pkgname + "', idSCat:1}) " + \
                        "match (u:User {userId:pkg.userId}) " + \
                        "match (n:Word:" + lgSource + ")-[tes:TRANSLATOR]->" + \
                        "(s:Word:" + lgTarget + ") " + \
                        "where  n.word in pkg.words " + \
                        "with u, n, s, tes " + \
                        "order by n.wordranking, tes.sorded " + \
                        "with u, n, collect(distinct s.word) as swlist " + \
                        "with u, collect(n.word) as ewlist, collect(swlist) as swlist " + \
                        "return u.alias as idUser, 'words' as subCat, " + \
                                "ewlist[0.." + str(capacity) + "] as slSource, " + \
                                "swlist[0.." + str(capacity) + "] as slTarget"
        else:
            ne04j_statement = "match (u:User {userId:'" + user_id + "'}) " + \
                    "match (pkg:Package {packageId:'" + pkgname + "', idSCat:" + str(idSCat) + "})-[:PACKAGED]->(u) " + \
                    "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                    "match (s)-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                        "(sw:ElemSubCat:" + lgTarget + ") " + \
                    "where  (not ew.word in pkg.words)" + \
                    "with s, u, ew, sw, scat " + \
                    "order by scat.wordranking " + \
                    "with s, u, collect(ew.word) as ewlist, collect(sw.word) as swlist " + \
                    "return u.userId as idUser, s.name as subCat, " + \
                            "ewlist[0.." + str(capacity) + "] as slSource, " + \
                            "swlist[0.." + str(capacity) + "] as slTarget"

        print(f"neo4j:state: {ne04j_statement}")
        nodes, log = neo4j_exec(session, user,
                            log_description="getting words for user",
                            statement=ne04j_statement)
    else:  # if new_package == 1                                                   # new words package is required

        ne04j_statement = "match (u:User {userId:'" + user_id + "'}) " + \
                "optional match (pkg:Package {status:'open', idSCat:" + str(idSCat) + "})-[:PACKAGED]->(u) " + \
                "unwind pkg.words as pkgwords " + \
                "with collect(pkgwords) as pkgwords " + \
                "return pkgwords "
        nodes, log = neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement)
        pkgwords = []
        for node in nodes:
            sdict = dict(node)
            pkgwords = sdict["pkgwords"]

        print(f"sdict for neo: {pkgwords}")     
        if idSCat == 1:
            ne04j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                    "match (u:User {userId:'" + user_id + "'}) " + \
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
        else: # if idSCat != 1:                                            # new subcategory package is required
               
            ne04j_statement = "with " + str(pkgwords) + " as pkgwords " + \
                    "match (u:User {userId:'" + user_id + "'}) " + \
                    "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                    "match (s)-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                        "(sw:ElemSubCat:" + lgTarget + ") " + \
                    "where  (not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL) and not ew.word in pkgwords " + \
                    "with s, u, ew, sw, scat " + \
                    "order by scat.wordranking " + \
                    "with s, u, collect(ew.word) as ewlist, collect(sw.word) as swlist " + \
                    "return u.userId as idUser, s.name as subCat, " + \
                            "ewlist[0.." + str(capacity) + "] as slSource, " + \
                            "swlist[0.." + str(capacity) + "] as slTarget"
                    #+ \
                    #"ewlist[0.." + str(capacity) + "] as slSource, " + \
                    #"swlist[0.." + str(capacity) + "] as slTarget"
            #print(f"ne04j_state: {ne04j_statement}")
        nodes, log = neo4j_exec(session, user,
                            log_description="getting words for user",
                            statement=ne04j_statement)
        
    # creating the structure to return data
    words = []
    for node in nodes:
        sdict = dict(node)        
        npackage = []
        prnFileName, prnLink = '', ''
        for gia, value in enumerate(sdict['slSource']):
            npackage.append([value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink])
            words.append(value)

    #                                                                               creating new data package 
    if new_package == 1:        
        ne04j_statement = "with " + str(list(words)) + " as wordlist " + \
                        "match (u:User {userId:'" + user_id + "'}) " + \
                        "merge (pkg:Package {userId:'" + user_id + "', packageId:'" + pkgname + "'})" + \
                        "-[pkgd:PACKAGED]->(u) " + \
                        "set pkg.words=wordlist, pkg.idSCat=" + str(idSCat) + "," + \
                            "pkg.status='open', pkg.SubCat='" + idSCatName + "', " + \
                            "pkg.ctInsert = datetime('"+ dtexec + "') "  + \
                        "return count(pkg) as pkg_qty"
    else:
        ne04j_statement = "with " + str(list(words)) + " as wordlist " + \
                        "match (u:User {userId:'" + user_id + "'}) " + \
                        "merge (pkg:Package {userId:'" + user_id + "', packageId:'" + pkgname + "'})" + \
                        "-[pkgd:PACKAGED]->(u) " + \
                        "set pkg.words=wordlist, pkg.idSCat=" + str(idSCat) + "," + \
                            "pkg.status='open', pkg.SubCat='" + idSCatName + "', " + \
                            "pkg.ctInsert = datetime('"+ dtexec + "') "  + \
                        "return count(pkg) as pkg_qty"

    nodes, log = neo4j_exec(session, user,
                        log_description="getting words pronunciation",
                        statement=ne04j_statement)        
    #                                                                              end of create new data package

    # getting the WordSound id for each word and example
    ne04j_statement = "with " + str(list(words)) + " as wordlist " + \
                    "unwind wordlist as wordtext " + \
                    "match(wp:WordSound:English {word:wordtext}) " + \
                    "return wp.word, id(wp) as idNode, wp.actived, wp.example"  # wp.binfile,
    
    nodes, log = neo4j_exec(session, user,
                        log_description="getting words pronunciation",
                        statement=ne04j_statement)
    result = []
    for gia, element in enumerate(npackage):
        binfile = None
        idNode = None
        example = ''
        for node in nodes:
            sdict = dict(node)
            if element[0] == sdict['wp.word']:
                #binfile = sdict['wp.binfile']
                idNode = sdict["idNode"]
                example = sdict.get('wp.example', '')
                break
        dict_pronunciation = {'example': example,
                            'pronunciation': idNode } # binfile.decode("ISO-8859-1")} #utf-8")}
        element.append(dict_pronunciation)
        result.append(element)

        #    npackage.append((value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink))
        #    words.append(value)

    return {"message": result}

@router.get("/get_/user_word_pron/{word} {idWord}")
def get_user_word_pron2(word, idWord):
    global appNeo, session, log, user

    statement = "match (ws:WordSound {word: '" +  word + "'}) " + \
                "where id(ws) = " + str(idWord) + " " + \
                "return ws.binfile limit 1"  # ws.word, ws.actived, 
    print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, user,
                        log_description="getting pronunciation word",
                        statement=statement)
    for ele in nodes:
        elems = dict(ele)
        #print(type(f), type(ele), ele, elems['ws.word'], elems['ws.actived'])
        #fw=open('savedfile4.mp3','wb')
        #fw.write(elems['ws.binfile'])
        #fw.close()
        return Response(elems['ws.binfile'])


@router.get("/get_/user_packagelist/{user_Id} {idSCat}")
def get_user_packagelist(user_id:str, idSCat:int):
    global appNeo, session, log, user
    #user_id = 'jivaldez03'    idSCat=12
    statement = "match (u:User {userId:'" + user_id + "'}) \n" + \
                "match (pkg:Package {userId: u.userId, status:'open', idSCat:" + str(idSCat) + "}) \n" + \
                "match (sc:SubCategory {idSCat:pkg.idSCat})-[]-(c:Category) \n"  + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) \n" + \
                "with u, pkg, c,  pkgS.level as level, min(pkgS.grade[0] / toFloat(pkgS.grade[1])) as grade \n" + \
                "with u, pkg, c,  max(level + '-,-' + toString(grade)) as level, count(DISTINCT level) as levs \n" + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName,  \n" + \
                        "pkg.SubCat as SCatName, \n" + \
                        "pkg.idSCat as idSCat, \n" + \
                        "split(level,'-,-')[0] as level, \n" + \
                        "toFloat(split(level,'-,-')[1]) as grade, \n" + \
                        "levs"
    nodes, log = neo4j_exec(session, user,
                        log_description="getting opened packages",
                        statement=statement)
    listPack = []
    for node in nodes:
        sdict = dict(node)                
        subcat_list = []
        if sdict["grade"] == None:
            ptg_errors = None
        else:
            ptg_errors = (sdict["grade"] - 1) * 100
        ndic = {'packageId': sdict["pkg.packageId"]
                , 'Category': sdict["CatName"], 'idCat' : sdict["idCat"]
                , 'SubCat': sdict["SCatName"], 'idSCat' : sdict["idSCat"]
                , 'distinct_levs': sdict["levs"]
                , 'maxlevel': sdict["level"]
                , 'ptg_errors' : ptg_errors
        }
        # ndic["ptg_errors"] -= 1
        listPack.append(ndic)
    return {'message': listPack}