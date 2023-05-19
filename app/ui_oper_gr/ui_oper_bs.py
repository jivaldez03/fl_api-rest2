from fastapi import APIRouter, Response
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs

router = APIRouter()


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
def get_dashboad_table(user_id):
    global appNeo, session, log, user

    neo4j_statement = "match (es:Word:English) " + \
        "match (c:Category {idCat:1})<-[sr:CAT_SUBCAT]-(sc:SubCategory {idSCat:1}) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "optional match (pkg:Package {userId:'" + user_id + "',status:'close',idSCat:sc.idSCat}) " + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) " + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned " + \
        "union " + \
        "match (og:Organization)<-[rr:RIGHTS_TO]-(u:User {userId:'" + user_id + "'}) " + \
        "match (og)<-[rsub:SUBJECT]-(c:Category)<-[sr:CAT_SUBCAT]-(sc:SubCategory )-[esr]-(es:ElemSubCat:English) " + \
        "-[tr]-(ws:ElemSubCat:Spanish) " + \
        "with c, sc, count(es.word) as wordsSC " + \
        "order by sc.idSCat, c.name, sc.name " + \
        "optional match (pkg:Package {userId:'" + user_id + "',status:'close',idSCat:sc.idSCat}) " + \
        "optional match (pkg)<-[rst:STUDY]-(pkgS:PackageStudy) " + \
        "return c.name as CatName, sc.name as SCatName, wordsSC as totalwords, " + \
                "sum(size(pkg.words)) as learned"
    
    nodes, log = neo4j_exec(session, user_id,
                 log_description="getting data for dashboard table",
                 statement=neo4j_statement)
    listcat = []
    for node in nodes:
        listcat.append(dict(node))
        #print(dict(node))
    return {'message': listcat}

@router.get("/get_/user_words/{user_id} {idSCat}")
def get_user_words(user_id:str, idSCat:int, new_package:int=0, pkgname:str=None, capacity:int=8):
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
        else:                                                                   # new words package is required
            if idSCat == 1:
                ne04j_statement = "match (u:User {userId:'" + user_id + "'}) " + \
                        "optional match (pkg:Package {status:'open', idSCat:1})-[:PACKAGED]->(u) " + \
                        "unwind pkg.words as pkgwords " + \
                        "with u, collect(pkgwords) as pkgwords " + \
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
                """            
                        "optional match (wp:WordSound:" + lgSource + ")<-[pron:PRONUNCIATION]-(n)" + \
                        "with u, collect(n.word) as ewlist, collect(wp) as wplist, collect(swlist) as swlist " + \                    
                        "wplist[0..10] as wpSource, " + \
                """
            else: # if idSCat != 1:                                            # new subcategory package is required
                ne04j_statement = "match (u:User {userId:'" + user_id + "'}) " + \
                        "optional match (pkg:Package {status:'open', idSCat:" + str(idSCat) + "})-[:PACKAGED]->(u) " + \
                        "unwind pkg.words as pkgwords " + \
                        "with u, collect(pkgwords) as pkgwords " + \
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


@router.get("/get_/user_packagelist/{user_Id}")
def get_user_packagelist(user_id:str):
    global appNeo, session, log, user
    
    statement = "match (u:User {userId:'" + user_id + "'}) " + \
                "match (pkg:Package {userId: u.userId, status:'open'}) " + \
                "match (sc:SubCategory {idSCat:pkg.idSCat})-[]-(c:Category) "  + \
                "optional match (pkgS:PackageStudy)-[rs:STUDY]->(pkg) " + \
                "with u, pkg, c,  pkgS.level as level, min(pkgS.grade[0] / toFloat(pkgS.grade[1])) as grade " + \
                "with u, pkg, c,  max(level + '-,-' + toString(grade)) as level, count(DISTINCT level) as levs " + \
                "return pkg.packageId, c.idCat as idCat, c.name as CatName,  " + \
                        "pkg.SubCat as SCatName, " + \
                        "pkg.idSCat as idSCat, " + \
                        "split(level,'-,-')[0] as level, " + \
                        "toFloat(split(level,'-,-')[1]) as grade, " + \
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