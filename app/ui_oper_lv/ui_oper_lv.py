from fastapi import APIRouter
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs

router = APIRouter()


@router.get("/get_/level/{user_id}")
def get_level(user_id):
    global appNeo, session, log, user

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


@router.get("/get_/level_user_words/{user_id} {idSCat}")
def get_user_words(user_id:str, idSCat:int, capacity:int=8):
    global appNeo, session, log, user

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
        #print("---------------en ciclo nodes")
        continueflag = True
        sdict = dict(node) 
        lgSource = sdict["lSource"]
        lgTarget = sdict["lTarget"]
        idOrg = sdict["idOrg"]
        idSCatName = sdict["idSCatName"]
        #print(f"results for idSCat : ", lgSource, lgTarget, idOrg, idSCatName)
        idSCatName = idSCatName.replace("/","").replace(" ","")
        #print(f"results for idSCat : ", lgSource, lgTarget, idOrg, idSCatName)
    if continueflag:
        if idSCat == 1:
            ne04j_statement = "match (u:User {alias:'" + user_id + "'}) " + \
                    "match (n:Word:" + lgSource + ")-[tes:TRANSLATOR]->" + \
                    "(s:Word:" + lgTarget + ") " + \
                    "where  not n.word in u.words or u.words is NULL " + \
                    "with u, n, s, tes " + \
                    "order by n.wordranking, tes.sorded " + \
                    "with u, n, collect(s.word) as swlist " + \
                    "with u, collect(n.word) as ewlist, collect(swlist) as swlist " + \
                    "return u.alias as idUser, 'words' as subCat, " + \
                    "ewlist[0.." + str(capacity) + "] as slSource, " + \
                    "swlist[0.." + str(capacity) + "] as slTarget"
            """            
                    "optional match (wp:WordSound:" + lgSource + ")<-[pron:PRONUNCIATION]-(n)" + \
                    "with u, collect(n.word) as ewlist, collect(wp) as wplist, collect(swlist) as swlist " + \                    
                    "wplist[0..10] as wpSource, " + \
            """
        else: # if idSCat != 1:
            ne04j_statement = "match (u:User {alias:'" + user_id + "'}) " + \
                        "match (c:Category)-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                        "match (s)-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                            "(sw:ElemSubCat:" + lgTarget + ") " + \
                        "where  not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL " + \
                        "with s, u, ew, sw, scat " + \
                        "order by scat.wordranking " + \
                        "with s, u, collect(ew.word) as ewlist, collect(sw.word) as swlist " + \
                        "return u.alias as idUser, s.name as subCat, " + \
                                "ewlist[0.." + str(capacity) + "] as slSource, " + \
                                "swlist[0.." + str(capacity) + "] as slTarget"
                
        nodes, log = neo4j_exec(session, user,
                            log_description="getting words for user",
                            statement=ne04j_statement)
        
        words = []
        for node in nodes:
            sdict = dict(node)        
            npackage = []
            prnFileName, prnLink = '', ''
            for gia, value in enumerate(sdict['slSource']):
                npackage.append([value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink])
                words.append(value)

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

