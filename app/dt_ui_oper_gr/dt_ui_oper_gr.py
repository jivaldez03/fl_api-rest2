from fastapi import APIRouter, Response, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname \
                            ,_getdatime_T

#, get_list_elements #, myConjutationLink, get_list_element

from random import shuffle as shuffle

from app.model.md_params_oper import ForNamePackages, ForGames_KOW, ForGames_archive

router = APIRouter()

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
        #print(f" word: {word} - sdict {dict_pronunciation}")
    #print("id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname())
    return result


#@router.get("/get_/categories/")
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

@router.post("/pst_/packagename/")
async def pst_packagename(datas:ForNamePackages
                    , Authorization: Optional[str] = Header(None)):
    """
    Function change the package's label \n    
    
    {\n
        package:str=None,  
        label  :str=None
    }
    """
    global appNeo, session

    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    pkgname = datas.package
    newlabel = datas.label
    newlabel = newlabel.replace("'","").replace('"','')

    dtexec = funcs._getdatime_T()

    neo4j_statement = "with '" + pkgname + "' as pkgname, \n" + \
                    "'" + newlabel + "' as newname, \n" + \
                    "'" + userId + "' as userId  \n" + \
                    "match (p:Package {packageId:pkgname, userId:userId}) \n" + \
                    "set p.label = newname, p.cdUpdate = datetime() \n" + \
                    "return p.packageId as packageId , p.label as newlabel"
    
    nodes, log = neo4j_exec(session, userId,
                        log_description="rename package" + pkgname + ' as ' + newlabel,
                        statement=neo4j_statement, filename=__name__, function_name=myfunctionname())
    res = {}
    confirmlabel = ""
    for node in nodes:
        sdict = dict(node)
        confirmlabel = sdict["newlabel"]
        res = {'packageId' : sdict["packageId"], "newlabel": confirmlabel}

    if confirmlabel != newlabel:
        message = "ERROR - INVALID RENAME PACKAGE"
    else:
        message = "-- SUCCESSFUL OPERATION --"
    res["message"]=message

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return res


@router.post("/gamesAA/")
async def valuesforgames_AA(datas:ForGames_KOW, Authorization: Optional[str] = Header(None)):
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
    orgId: str
    limit: int
    subcat:int
    adj: bool
    verb: bool
    pt_verb: bool
    noun: bool
    adj : bool
    adv : bool
    prep : bool

    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    statement = "with " + str(datas.adj) + " as adj, \n" + \
                            str(datas.verb) + " as verb, \n" + \
                            str(datas.pt_verb) + " as ptense, \n" + \
                            str(datas.noun) + " as noun, \n" + \
                            str(datas.adv) + " as adv, \n" + \
                            str(datas.prep) + " as prep, \n" + \
                            "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            "1 as idCat, 1 as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-\n" + \
                "[rc:SUBJECT]-(c:Category {idCat:idCat})-[rsc:CAT_SUBCAT]-(sc:SubCategory {idSCat:idSCat}) \n" + \
                "with u,o.lSource as Source, o.lTarget as Target, o, sc \n" + \
                "    , adj, verb, noun, adv, prep, ptense \n" + \
                "match (u)-[r]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]-(sc) // :Source:Target) \n" + \
                "where o.lSource in labels(rM) and o.lTarget in labels(rM) \n" + \
                "with u, o, rM.words as words \n" + \
                "    , adj, verb, noun, adv, prep, ptense \n" + \
                "unwind words as sword \n" + \
                "with u, o, sword, adj, verb, noun, adv, prep, ptense \n" + \
                "match (we:Word {word:sword}) \n" + \
                "where o.lSource in labels(we) \n" + \
                "with u, o, we, adj, verb, noun, adv, prep, ptense, \n" + \
                        "REDUCE(mergedString = ',', \n" + \
                            "kow IN we.ckowb_complete | mergedString+kow +',') as ckowlist \n" + \
                "where  (ptense and ckowlist contains 'past – verb')  \n" + \
                "        or ((verb and ckowlist contains 'intrans verb' \n" + \
                "        or verb and ckowlist contains 'trans verb') \n" + \
                "        and not ckowlist contains 'past – verb') \n" + \
                "        or adj and ckowlist contains 'adj' \n" + \
                "        or adv and ckowlist contains 'adv' \n" + \
                "        or prep and ckowlist contains 'prep' \n" + \
                "        or noun and ckowlist contains 'noun' \n" + \
                "match (we)-[rt:TRANSLATOR]-(ws:Word)  \n" + \
                "where o.lTarget in labels(ws) \n" + \
                "with u, we.word as worde, we.ckowb_complete as ckow, ws.word as words  \n" + \
                "order by worde, rt.sorted \n" + \
                "with u, worde, ckow, collect(words) as words \n" + \
                "order by rand() \n" + \
                "return worde, words, ckow  limit "  + str(datas.limit) 
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for games: ",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle


@router.post("/gamesAA_archive/")
async def valuesforgames_AA_archive(datas:ForGames_archive, Authorization: Optional[str] = Header(None)):
    """
    Function to get the file .mp3 with the pronunciation example

    params :  \n
    orgId: str
    subcat:int
    words: str   # ['tree','car','table', 'apple']
    average: float
    kogame: str
    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    kogame = datas.kogame.upper()
    if kogame in ["GUESS_TW", "TRY_TW"]:
        pass
    else: 
        kogame = 'G_UNKNOWN'
    swords = str(datas.words)
    sswords = swords.replace("[",",").replace("]",",").replace("'","").replace('"',"").replace(", ",",")
    print("\n\n", datas, type(swords), type(datas.words), "\n\n")

    statement = "with " + "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            swords + 'as words, \n' + \
                            '"' + sswords + '" as swords, \n' + \
                            str(datas.average) + " as average, \n" + \
                            "1 as idCat, 1 as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})\n" + \
                "with u,o.lSource as Source, o.lTarget as Target, words, swords, average \n" + \
                "merge (u)<-[rg:" + kogame + "]-(gm:Game {swords:swords}) \n" + \
                "set gm.lSource = Source, gm.lTarget = Target, \n" + \
                    " gm.words = words, \n" + \
                    " gm.average = average, \n" + \
                    " gm.ctInsert = datetime() \n" + \
                "return u.userId as userId, size(gm.words) as qtywords "
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="archiving words for games",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle
