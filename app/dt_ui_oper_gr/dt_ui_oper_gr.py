from fastapi import APIRouter, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log
import __generalFunctions as funcs
from __generalFunctions import myfunctionname \
                            ,_getdatime_T, _getdatetime, email_send \
                            , get_random_string

from asyncio import sleep as awsleep

#, get_list_elements #, myConjutationLink, get_list_element

from random import shuffle as shuffle

from app.model.md_params_oper import ForNamePackages, ForGames_KOW, \
                                    ForGames_puzzle, ForGames_archive, ForLevelEval, \
                                    ForAskSupport

import signal
signal.signal(signal.SIGWINCH, signal.SIG_IGN)

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
    """
    "PUT_TOGETHER_WORD"
    "PUZZLEWORDS"
    "G_UNKNOWN"
    "TRY_TW"
    "GUESS_TW"
    """

    statement = "with " + str(datas.adj) + " as adj, \n" + \
                            str(datas.verb) + " as verb, \n" + \
                            str(datas.pt_verb) + " as ptense, \n" + \
                            str(datas.noun) + " as noun, \n" + \
                            str(datas.adv) + " as adv, \n" + \
                            " True as prep, True as conj,  \n" + \
                            "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            "1 as idCat, 1 as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-\n" + \
                "[rc:SUBJECT]-(c:Category {idCat:idCat})-[rsc:CAT_SUBCAT]-(sc:SubCategory {idSCat:idSCat}) \n" + \
                "with u,o.lSource as Source, o.lTarget as Target, o, sc, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj \n" + \
                "// *** SE LOCALIZAN LAS PALABRAS QUE YA SE HAN EJERCITADO \n" + \
                "optional match (u)<-[r]-(gm:Game) \n" + \
                "where not type(r) in ['PUZZLEWORDS'] \n" + \
                "with u, Source, Target, o, sc, coalesce(gm.words,['']) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj \n" + \
                "unwind wordsgame as word \n" + \
                "with u, Source, Target, o, sc,  word, \n" + \
                    "adj, verb, noun, adv, prep, ptense, conj \n" + \
                "order by word \n" + \
                "with u, Source, Target, o, sc, collect(distinct word) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj \n" + \
                "with u, Source, Target, o, sc, wordsgame, apoc.coll.shuffle(wordsgame) as wordsgameSh, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj \n" + \
                "// SE LOCALIZAN LAS PALABRAS ARCHIVADAS \n" + \
                "match (u)<-[r:ARCHIVED_M]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                "where o.lSource in labels(rM) and o.lTarget in labels(rM) \n" + \
                "// Y SE ELIMINAN LAS QUE FUERON LLEVADAS A JUEGOS \n" + \
                "with u, o, apoc.coll.subtract(rM.words, wordsgame) as words, wordsgame, rM.words as rmwords, \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, wordsgameSh \n" + \
                "with u, o, (case when words = [] then rmwords else words end) as words, wordsgame,  \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, wordsgameSh \n" + \
                "unwind words as sword \n" + \
                "with u, o, collect(sword) as swords, adj, verb, noun, adv, prep, ptense, conj, wordsgameSh \n" + \
                "with u, o, swords + wordsgameSh[0.." + str(datas.limit * 2) + "] as swordsC, \n" + \
                    " adj, verb, noun, adv, prep, ptense, conj, swords \n" + \
                "unwind swordsC as sword \n" + \
                "with u, o, sword, adj, verb, noun, adv, prep, ptense, conj, swords \n" + \
                "match (we:Word {word:sword}) \n" + \
                "where o.lSource in labels(we) \n" + \
                "with distinct u, o, we, adj, verb, noun, adv, prep, ptense, conj, swords, \n" + \
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
                "        or conj and ckowlist contains 'conj' \n" + \
                "        or ckowlist contains 'modal' \n" + \
                "match (we)-[rt:TRANSLATOR]-(ws:Word)  \n" + \
                "where o.lTarget in labels(ws) \n" + \
                "with u, we.word as worde, we.ckowb_complete as ckow, ws.word as words  \n" + \
                "order by worde in swords desc, worde, rt.sorted \n" + \
                "with u, worde, ckow, collect(words) as words \n" + \
                " //limit "  + str(datas.limit) + \
                "\n" + \
                "return worde, words, ckow order by rand() limit "  + str(datas.limit) 
    #print(f"statement pronun: {statement}")

    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for games: ",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        en_let = list(elems["worde"])
        if len(en_let) < 3 :
            en_let.reverse()
        else:
            shuffle(en_let)
        elems["wordstouser"] = en_let
        #print("----------------------------> ", en_let, elems['worde'])
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

    dtimenow = _getdatetime()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = dtimenow.strftime("%W") # , status:'open'

    kogame = datas.kogame.upper()
    #if kogame in ["GUESS_TW", "TRY_TW","PUT_TOGETHER_WORD"] :kogame' = "PUT_TOGETHER_WORD"
    #    pass
    #else: 
    #    kogame = 'G_UNKNOWN'
    swords = str(datas.words)

    sswords = swords.replace("[",",").replace("]",",").replace("'","").replace('"',"").replace(", ",",")
    #print("\n\n ************************ ", datas.kogame, datas.words, swords, "\n\n")

    statement = "with " + "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            "'" + kogame + "' as kogame, \n" + \
                            str(yearr) + " as yearr, \n" + \
                            str(monthh) + " as monthh, \n" + \
                            str(weekk) + " as weekk, \n" + \
                            swords + 'as words, \n' + \
                            '"' + sswords + '" as swords, \n' + \
                            str(datas.average) + " as average, \n" + \
                            "1 as idCat, 1 as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})\n" + \
                "with u, kogame, userId, yearr, monthh, weekk, \n" + \
                    "o.lSource as Source, o.lTarget as Target, words, swords, average \n" + \
                "merge (u)<-[rg:" + kogame + "]-(gm:Game \n" + \
                    "{game:kogame, userId:userId, swords:swords, \n" + \
                        " year:yearr, month:monthh, week:weekk}) \n" + \
                "set gm.lSource = Source, gm.lTarget = Target, \n" + \
                    " gm.words = words, \n" + \
                    " gm.average = average, \n" + \
                    " gm.ctInsert = datetime() \n" + \
                "return u.userId as userId, size(gm.words) as qtywords "
    #print(f"statement pronun: {statement}")

    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="archiving words for games - " + kogame,
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle


@router.post("/gamesAA_puzzlewords/")
async def puzzlewords(#org:str, ulevel:str, kog: str, hms:int, avg:float, recs:int
                    datas:ForGames_puzzle
                    , Authorization: Optional[str] = Header(None)):
    """
    Function to create the word list for level 4 (lvl_40_01) \n    
    
    {\n
    {  
    params :  \n
        orgId: str:"DTL-01"
        ulevel:str      # A1,A2,B1,B2,C1,C2
        kog: str        # "puzzlewords"
        hms: int        # how many sentences
        words: str      # "['abc','cde','fgh']"
        avg: float      # avg result - post exercise
        setlevel: int       # save or not
    }
    """
    global appNeo, session
    
    token=funcs.validating_token(Authorization) 
    userId = token['userId']

    dtimenow = _getdatetime()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = dtimenow.strftime("%W") # , status:'open'

    kogame = datas.kog.upper()
    if kogame in ["PUZZLEWORDS"]:
        pass
    else: 
        kogame = 'G_UNKNOWN'

    if datas.ulevel == 'A1':
        llev = 2
        ulev = 5
    elif datas.ulevel == 'A2':
        llev = 2
        ulev = 6
    elif datas.ulevel == 'B1':
        llev = 4
        ulev = 7
    elif datas.ulevel == 'B2':
        llev = 4
        ulev = 9
    else: #if datas.ulevel == 'C1':
        llev = 7
        ulev = 99
        
    rlimit = str(datas.hms)

    if datas.org== 'DTL-01':
        source = 'English'
        target = 'Spanish'
        idCat = 1
        idSCat = 1
    elif datas.org == 'DTL-02':
        source = 'German'
        target = 'Spanish'
        idCat = 101
        idSCat = 1
    else:
        source = None
        target = None

    swords = str(datas.words)
    sswords = swords.replace("[",",").replace("]",",").replace("'","").replace('"',"").replace(", ",",")

    print('puzzle datas:', datas)

    if datas.setlevel == False: 
        neo4j_statement = "with '" + datas.org + "' as org \n" + \
                    "    , '" + userId + "' as userId \n" + \
                    "    , " +  str(llev) + " as llevel \n" + \
                    "    , " +  str(ulev) + " as ulevel \n" + \
                    "match (o:Organization {idOrg:org})<-[rou:RIGHTS_TO]-(u:User {userId:userId}) \n" + \
                    "-[r:ARCHIVED_M]-(arcM:Archived_M)-[rs:SUBCAT_ARCHIVED_M]->(sc:SubCategory) \n" + \
                    "with u.userId as userId, sc, arcM.words as words \n" + \
                        ", llevel, ulevel, o.lTarget as lTarget \n" + \
                    "unwind words as word \n" + \
                    "with userId, sc.idCat as idCat, sc.idSCat as idSCat, word \n" + \
                        ", llevel, ulevel, lTarget  \n" + \
                    "order by rand() \n" + \
                    "match (wss:WordSound {word:word, idCat:idCat, idSCat:idSCat}) \n" + \
                    "where not wss.example contains '–' // ['-', '*', '–','_'] \n" + \
                    "with wss.example as sentence, elementId(wss) as eletoshow \n" + \
                        "   , idCat * 1000000 + idSCat as idSCat \n" + \
                        "   , word, wss[lTarget] as exTarget \n" + \
                        ", replace( \n" + \
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
                        "        as sentence2 \n" + \
                        ", llevel, ulevel \n" + \
                    "with sentence, sentence2, split(sentence2, ' ') as wordstouser \n" + \
                            ", eletoshow, idSCat, word \n" + \
                        ", llevel, ulevel, exTarget \n" + \
                    "where llevel < size(wordstouser) < ulevel \n" + \
                    "return sentence2 as sentence, apoc.coll.shuffle(wordstouser) as wordstouser \n" + \
                    "       , eletoshow, idSCat, word, exTarget, sentence as original_sentence limit " + rlimit        
    else:        
        neo4j_statement = "with " + "'" + datas.org + "' as org, \n" + \
                                "'" + userId + "' as userId, \n" + \
                                "'" + kogame + "' as kogame, \n" + \
                                str(yearr) + " as yearr, \n" + \
                                str(monthh) + " as monthh, \n" + \
                                str(weekk) + " as weekk, \n" + \
                                swords + 'as words, \n' + \
                                '"' + sswords + '" as swords, \n' + \
                                str(datas.avg) + " as average, \n" + \
                                "1 as idCat, 1 as idSCat \n" + \
                    "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})\n" + \
                    "with u, kogame, userId, yearr, monthh, weekk, \n" + \
                        "o.lSource as Source, o.lTarget as Target, words, swords, average \n" + \
                    "merge (u)<-[rg:" + kogame + "]-(gm:Game \n" + \
                        "{game:kogame, userId:userId, swords:swords, \n" + \
                            " year:yearr, month:monthh, week:weekk}) \n" + \
                    "set gm.lSource = Source, gm.lTarget = Target, \n" + \
                        " gm.words = words, \n" + \
                        " gm.average = average, \n" + \
                        " gm.ctInsert = datetime() \n" + \
                    "return u.userId as userId, size(gm.words) as qtywords "
    #print("puzzle - neo4_statement:", neo4j_statement)
    await awsleep(0)
    
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="sentences for puzzlewords - setlevel = " + \
                                'True' if datas.setlevel else 'False',
                        statement=neo4j_statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return {'userId':userId, 'sentences': listEle}

            
@router.post("/leval/")
async def levaluation(datas:ForLevelEval, Authorization: Optional[str] = Header(None)):
    """
    orgId   : str  DTL-01 for English
    starton : int
    limit   : int
    word    : string
    setlevel: 
    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    if datas.orgId == 'DTL-01':
        source = 'English'
        target = 'Spanish'
        idCat = 1
        idSCat = 1
    elif datas.orgId == 'DTL-02':
        source = 'German'
        target = 'Spanish'
        idCat = 101
        idSCat = 1
    else:
        source = None
        target = None

    if datas.setlevel == False:
        statement = "with '" + datas.orgId + "' as org \n" + \
                    "match (og:Organization {idOrg:org}) \n" + \
                    "match (we:Word:" + source + ") \n" + \
                    "where exists {(we)-[r:TRANSLATOR]-(ws:Word:" + target + ")} \n" + \
                    "with we order by we.wordranking, we.word \n" + \
                    "skip "  + str(datas.starton) + " \n" + \
                    "limit " + str(datas.limit) + "\n" + \
                    "return we.word as word, we.wordranking as prevmax"        
    else:
        statement = "with '" + datas.orgId + "' as org, \n" + \
                    "'" + str(datas.word) + "' as word \n" + \
                    "match (u:User {userId:'" + userId + "'}) \n" + \
                    "-[ruo:RIGHTS_TO]-> \n" + \
                    "(og:Organization {idOrg:org}) \n" + \
                    "<-[rc:SUBJECT]-(c:Category {idCat:"+ str(idCat) + "}) \n" + \
                    "<-[rcs:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "}) \n" + \
                    "with og, c.idCat as idCat, sc, u \n" + \
                    "match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM2:Archived_M:" + source + ":" + target + ")-\n" + \
                        "[:ARCHIVED_M]->(u) \n" + \
                    "where arcM2.reference is null " + \
                    "with og, idCat, sc, u, arcM2.words as words \n" + \
                    "unwind words as word \n" + \
                    "with og, idCat, sc, u, collect(word) as wordsarcM \n" + \
                    "match (we:Word:" + source + ") \n" + \
                    "with og, idCat, sc, u, wordsarcM, we \n" + \
                    "order by we.wordranking, we.word \n" + \
                    " limit " + str(datas.starton) + " \n" + \
                    "with og, idCat, sc, u, wordsarcM, we \n" + \
                    "match (we) \n" + \
                    "where not we.word in wordsarcM \n" + \
                        " and exists {(we)-[r:TRANSLATOR]-(ws:Word:" + target + ")} \n" + \
                    "with og, idCat, sc, u, collect(we.word) as words \n"  + \
                    "merge (arcM:Archived_M:" + source + ":" + target + " {userId:'" + userId + "', \n" + \
                    "    source:og.lSource, target:og.lTarget, \n" + \
                    "    idCat:idCat, idSCat:sc.idSCat, reference:'Initial_Level'}) \n" + \
                    "on create set arcM.ctInsert = datetime() \n" + \
                    "on match set arcM.ctUpdate = datetime(),  \n" + \
                        "arcM.wordsBack=[toString(datetime())] + arcM.words \n" + \
                    "set arcM.words = words, arcM.month_qty = size(words) \n" + \
                    "merge (u)<-[rua:ARCHIVED_M]-(arcM)-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                    "return arcM.words, arcM.wordsBack  \n"
    
    await awsleep(0)
    
    #print(f"statement pronun: {statement}")

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting words for evaluation: ",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle


@router.get("/reclinks/")
async def recslinks(Authorization: Optional[str] = Header(None)):
    """    

    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    statement = "with " + "'" + userId + "' as userId \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]->(o:Organization) \n" + \
                    "<-[r:ORG_RECLINK]-(rl:RecLinks) \n" + \
                "return rl.image as logo,  rl.name as name, rl.link as link, \n" + \
                    "coalesce(rl[u.selected_lang],rl['Spanish']) as texttoshow, \n" + \
                    "rl.imagelink as imagelink \n" + \
                "order by rl.sorted"      
    #print(f"statement pronun: {statement}")

    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting recommended links",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle


@router.get("/reclinks/")
async def recslinks(Authorization: Optional[str] = Header(None)):
    """    

    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    statement = "with " + "'" + userId + "' as userId \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]->(o:Organization) \n" + \
                    "<-[r:ORG_RECLINK]-(rl:RecLinks) \n" + \
                "return rl.image as logo,  rl.name as name, rl.link as link, \n" + \
                    "coalesce(rl[u.selected_lang],rl['Spanish']) as texttoshow, \n" + \
                    "rl.imagelink as imagelink \n" + \
                "order by rl.sorted"      
    #print(f"statement pronun: {statement}")

    await awsleep(0)

    nodes, log = neo4j_exec(session, userId,
                        log_description="getting recommended links",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)
    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle


@router.post("/askforsupportoth/")
async def asksupport(datas:ForAskSupport, Authorization: Optional[str] = Header(None)):
    """
    classification: str
    subject : str
    longdescription : str    
    """
    global appNeo, session, log

    dtexec = _getdatime_T()

    token=funcs.validating_token(Authorization)
    userId = token['userId']
    useremail = token['useremail']
    useremail_alt = token['useremail_alt']
    if useremail_alt and useremail_alt.strip() == "":
        useremail_alt = None
    dtexec = _getdatime_T()
    subj = datas.subject.replace("'",'"')
    ldesc = datas.longdescription.replace("'",'"')

    suppId = get_random_string(10)

    statement = "with '" + userId + "' as userId, \n" + \
                    "'" + suppId + "' as supportId, \n" + \
                    "'" + datas.classification + "' as sclassification, \n" + \
                    "'" + subj + "' as ssubject, \n" + \
                    "'" + ldesc + "' as slongdescription \n" + \
                "match (u:User {userId:userId}) \n" + \
                "create (supp:Support {userId:userId, supportId:supportId, \n" + \
                        "subject:ssubject, classification:sclassification}) \n" + \
                " set supp.ctInsert = datetime(), supp.user_time = datetime('" + \
                            dtexec + "'), \n " + \
                "     supp.subject = ssubject, \n" + \
                "     supp.long_description = slongdescription, \n" + \
                "     supp.email = u.email, \n" + \
                "     supp.email_alt = u.email_alt \n" + \
                "merge (u)<-[r:USER_SUPPORT]-(supp) \n" + \
                " set r.ctInsert = datetime() \n" + \
                "return u.userId, u.email, u.email_alt limit 1"        
    
    #print("statement:\n",  statement)
    await awsleep(0)
    
    #print(f"statement pronun: {statement}")
    nodes, log = neo4j_exec(session, userId,
                        log_description="recording ask support",
                        statement=statement, 
                        filename=__name__, 
                        function_name=myfunctionname())
    listEle = []
    for ele in nodes:
        elems = dict(ele)
        listEle.append(elems)

    email_send(userId, useremail, # + ',' + useremail_alt, \
               "Code Id: " + dtexec.replace("-","").replace(":","") + "_" + \
                            suppId + "\n\n" + 
                datas.longdescription + "\n\n\nuserId: " + userId,  \
                'DTone - ' + datas.classification  + " (" + userId + "): " + datas.subject, \
                appNeo, useremail_alt)

    print("========== id: ", userId, " dt: ", _getdatime_T(), " -> ", myfunctionname(),"\n\n")
    return listEle

