from fastapi import APIRouter, Response
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs

router = APIRouter()

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