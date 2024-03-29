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
    await awsleep(0)
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
    await awsleep(0)
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
    kogame: str
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
    

    if datas.kogame: 
        kogame = ":" + datas.kogame.upper()
    else:
        kogame = ""
    print("\nkog:", kogame)
    """
    "PUT_TOGETHER_WORD"
    "PUZZLEWORDS"
    "G_UNKNOWN"
    "TRY_TW"
    "GUESS_TW"
    """

    if userId == 'jagr':
        datas.orgId = 'DTL-02'
        
    """
    # se comenta para que tambien opere con las palabras de las subcategorias
    statement = "with " + str(datas.adj) + " as adj, \n" + \
                            str(datas.verb) + " as verb, \n" + \
                            str(datas.pt_verb) + " as ptense, \n" + \
                            str(datas.noun) + " as noun, \n" + \
                            str(datas.adv) + " as adv, \n" + \
                            " True as prep, True as conj, True as pron, \n" + \
                            "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            idCat + " as idCat, " + idSCat + " as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-\n" + \
                "[rc:SUBJECT]-(c:Category {idCat:idCat})-[rsc:CAT_SUBCAT]-(sc:SubCategory {idSCat:idSCat}) \n" + \
                "with u,o.lSource as Source, o.lTarget as Target, o, sc, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "// *** SE LOCALIZAN LAS PALABRAS QUE YA SE HAN EJERCITADO \n" + \
                "optional match (u)<-[r" + kogame + "]-(gm:Game) \n" + \
                "where not type(r) in ['PUZZLEWORDS'] \n" + \
                "with u, Source, Target, o, sc, coalesce(gm.words,['']) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "unwind wordsgame as word \n" + \
                "with u, Source, Target, o, sc,  word, \n" + \
                    "adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "order by word \n" + \
                "with u, Source, Target, o, sc, collect(distinct word) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "with u, Source, Target, o, sc, wordsgame, apoc.coll.shuffle(wordsgame) as wordsgameSh, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "// SE LOCALIZAN LAS PALABRAS ARCHIVADAS \n" + \
                "match (u)<-[r:ARCHIVED_M]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                "where o.lSource in labels(rM) and o.lTarget in labels(rM) \n" + \
                "// Y SE ELIMINAN LAS QUE FUERON LLEVADAS A JUEGOS \n" + \
                "with u, o, apoc.coll.subtract(rM.words, wordsgame) as words, wordsgame, rM.words as rmwords, \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "with u, o, (case when words = [] then rmwords else words end) as words, wordsgame,  \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "unwind words as sword \n" + \
                "with u, o, collect(sword) as swords, adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "with u, o, swords + wordsgameSh[0.." + str(datas.limit * 2) + "] as swordsC, \n" + \
                    " adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "unwind swordsC as sword \n" + \
                "with u, o, sword, adj, verb, noun, adv, prep, ptense, conj, pron, \n" + \
                " case when sword in wordsgameSh then 1 else 0 end as prioridad \n" + \
                "match (we:Word {word:sword}) \n" + \
                "where o.lSource in labels(we) and not we.word contains ' ' \n" + \
                "with distinct u, o, we, adj, verb, noun, adv, prep, ptense, conj, pron, prioridad \n" + \
                "/*, REDUCE(mergedString = ',', \n" + \
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
                "        or pron and ckowlist contains 'pron' \n" + \
                "        or ckowlist contains 'modal' */ \n" + \
                "match (wss:WordSound)<-[:PRONUNCIATION]-(we)-[rt:TRANSLATOR]-(ws:Word)  \n" + \
                "where o.lTarget in labels(ws) \n" + \
                "with u, elementId(wss) as soundId, we.word as worde, \n" + \
                " we.ckowb_complete as ckow, ws.word as words, prioridad  \n" + \
                "order by prioridad, // worde in swords desc, \n" + \
                    " worde, rt.sorted \n" + \
                "with u, soundId, prioridad, worde, ckow, collect(words) as words \n" + \
                "order by u, prioridad, rand() \n" + \
                "limit "  + str(datas.limit) + " \n" + \
                "return worde, words, ckow, soundId " #// order by rand() // limit "  + str(datas.limit) 
    """

    statement = "with " + str(datas.adj) + " as adj, \n" + \
                            str(datas.verb) + " as verb, \n" + \
                            str(datas.pt_verb) + " as ptense, \n" + \
                            str(datas.noun) + " as noun, \n" + \
                            str(datas.adv) + " as adv, \n" + \
                            " True as prep, True as conj, True as pron, \n" + \
                            "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-\n" + \
                "[rc:SUBJECT]-(c:Category)-[rsc:CAT_SUBCAT]-(sc:SubCategory) \n" + \
                "with u,o.lSource as Source, o.lTarget as Target, o, sc, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "// *** SE LOCALIZAN LAS PALABRAS QUE YA SE HAN EJERCITADO \n" + \
                "optional match (u)<-[r" + kogame + "]-(gm:Game) \n" + \
                "where not type(r) in ['PUZZLEWORDS'] \n" + \
                "with u, Source, Target, o, sc, coalesce(gm.words,['']) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "unwind wordsgame as word \n" + \
                "with u, Source, Target, o, sc,  word, \n" + \
                    "adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "order by word \n" + \
                "with u, Source, Target, o, sc, collect(distinct word) as wordsgame, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "with u, Source, Target, o, sc, wordsgame, apoc.coll.shuffle(wordsgame) as wordsgameSh, \n" + \
                "    adj, verb, noun, adv, prep, ptense, conj, pron \n" + \
                "// SE LOCALIZAN LAS PALABRAS ARCHIVADAS \n" + \
                "match (u)<-[r:ARCHIVED_M]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                "where o.lSource in labels(rM) and o.lTarget in labels(rM) \n" + \
                "// Y SE ELIMINAN LAS QUE FUERON LLEVADAS A JUEGOS \n" + \
                "with u, o, sc, apoc.coll.subtract(rM.words, wordsgame) as words, wordsgame, rM.words as rmwords, \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "with u, o, sc, (case when words = [] then rmwords else words end) as words, wordsgame,  \n" + \
                "  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "unwind words as sword \n" + \
                "with u, o, sc, collect(sword) as swords, adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "with u, o, sc, swords + wordsgameSh[0.." + str(datas.limit * 2) + "] as swordsC, \n" + \
                    " adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh \n" + \
                "unwind swordsC as sword \n" + \
                "with u, o, sword, adj, verb, noun, adv, prep, ptense, conj, pron, \n" + \
                "   sc.idCat as idCat, sc.idSCat as idSCat, \n" + \
                "   case when sword in wordsgameSh then 1 else 0 end as prioridad \n" + \
                "// SE OBTIENE LA PRONUNCIACION \n" + \
                "match (we:WordSound {word:sword}) \n" + \
                "where o.lSource in labels(we) and not we.word contains ' ' \n" + \
                "   and we.idCat = idCat and we.idSCat = idSCat \n" + \
                "with distinct u, o, we, adj, verb, noun, adv, prep, ptense, conj, pron, prioridad, \n" + \
                "     we.word as worde \n" + \
                "order by prioridad, worde // worde in swords desc, \n" + \
                "with we, u, o, prioridad, worde \n" + \
                "order by u, o, prioridad, rand() \n" + \
                "limit "  + str(datas.limit) + " \n" + \
                "// FUNCIONES PARA OBTENER LA TRADUCCIÓN DE LA PALABRA o SUBCATEGORIA \n" + \
                    "CALL { \n" + \
                        "with we, o \n" + \
                        "match (we)<-[rp:PRONUNCIATION]-(w:Word)-[rt:TRANSLATOR]->(ws:Word) \n" + \
                        "where o.lSource in labels(w) and o.lTarget in labels(ws) and we.idSCat = 1 \n" + \
                        "with ws.word as sword \n" + \
                        "order by rt.sorted \n" + \
                        "return collect(sword) as swordcollect \n" + \
                    "} \n" + \
                    "CALL { \n" + \
                        "with we, o \n" + \
                        "match (we)<-[rp:PRONUNCIATION_PV]-(w:ElemSubCat)-[rt:TRANSLATOR]->(ws:ElemSubCat) \n" + \
                        "where o.lSource in labels(w) and o.lTarget in labels(ws) and we.idSCat <> 1 \n" + \
                        "with ws.word as sword     \n" + \
                        "return collect(sword) as swordcollectES \n" + \
                    "} \n" + \
                "with worde, elementId(we) as soundId, \n" + \
                     " case when we.idSCat = 1 then swordcollect else swordcollectES end as swords \n" + \
                "//with worde, words, soundId, \n" + \
                "//  case when swordcollect = [] then swordcollectES else swordcollect end as swords \n" + \
                "return worde, swords as words, ' ' as ckow, soundId " 
                # "return worde, words, ' ' as ckow, soundId " #// order by rand() // limit "  + str(datas.limit) 
    
    print(f"statement AAAgames: {statement}")

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
    words: list   # ['tree','car','table', 'apple']
    grades: list # [90,100,80,60]
    average: float
    kogame: str
    """
    global appNeo, session, log

    token=funcs.validating_token(Authorization)
    userId = token['userId']

    #print("game archive - datas:", datas)

    if userId == 'jagr':
        datas.orgId = 'DTL-02'

    dtimenow = _getdatetime()
    yearr = dtimenow.year
    monthh = dtimenow.month
    weekk = int(dtimenow.strftime("%W")) # , status:'open'

    kogame = datas.kogame.upper()
    #if kogame in ["GUESS_TW", "TRY_TW","PUT_TOGETHER_WORD"] :kogame' = "PUT_TOGETHER_WORD"
    
    swords_complete = str(datas.words)
    swords_ap = datas.words

    swords = []
    for gia, ele in enumerate(datas.grades):
        if ele >= 80:
            swords.append(swords_ap[gia])

    swords = str(swords)
    sswords = swords.replace("[",",").replace("]",",").replace("'","").replace('"',"").replace(", ",",")    

    statement = "with " + "'" + datas.orgId + "' as org, \n" + \
                            "'" + userId + "' as userId, \n" + \
                            "'" + kogame + "' as kogame, \n" + \
                            str(yearr) + " as yearr, \n" + \
                            str(monthh) + " as monthh, \n" + \
                            str(weekk) + " as weekk, \n" + \
                            swords + ' as words, \n' + \
                            '"' + sswords + '" as swords, \n' + \
                            swords_complete + " as swords_complete, \n" + \
                            str(datas.grades) + " as swords_grades, \n" + \
                            str(datas.average) + " as average, \n" + \
                            "1 as idCat, 1 as idSCat \n" + \
                "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})\n" + \
                "// where 1 = 2 \n" + \
                "with u, kogame, userId, yearr, monthh, weekk, \n" + \
                    "o.lSource as Source, o.lTarget as Target, words, swords, average, \n" + \
                    "swords_complete, swords_grades\n" + \
                "merge (u)<-[rg:" + kogame + " {ctInsert:datetime()}]-(gm:Game \n" + \
                    "{game:kogame, userId:userId, swords:swords, \n" + \
                        " year:yearr, month:monthh, week:weekk}) \n" + \
                "set gm.lSource = Source, gm.lTarget = Target, \n" + \
                    " gm.words = words, \n" + \
                    " gm.words_complete = swords_complete, \n" + \
                    " gm.grades = swords_grades, \n" + \
                    " gm.average = average, \n" + \
                    " gm.ctInsert = datetime() \n" + \
                "return u.userId as userId, size(gm.words) as qtywords "
    
    print(f"statement game archive: {statement}")

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

    #print(f"result game archive: {listEle}")

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
        words: list      # "['abc','cde','fgh','ijk','lmn']"
        grades: list      # "[100, 80, 90, 70, 60]"
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
    weekk = int(dtimenow.strftime("%W")) # , status:'open'

    print("datas PUZZLEWORD:", datas)
    kogame = datas.kog.upper()
    if kogame in ["PUZZLEWORDS"]:
        pass
    else: 
        kogame = 'G_UNKNOWN'

    #no aplica, siempre se recibe A1
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
    
    llev = 3
    ulev = 20

    rlimit = str(datas.hms)
    
    org = datas.org

    if userId == 'jagr':   # usuario de jiduma para probar aleman
        org = 'DTL-02'        

    if org == 'DTL-01':
        source = 'English'
        target = 'Spanish'
        idCat = 1
        idSCat = 1
    elif org == 'DTL-02':
        source = 'German'
        target = 'Spanish'
        idCat = 101
        idSCat = 1
    else:
        source = None
        target = None

    
    swords_complete = str(datas.words)
    swords_ap = datas.words

    swords = []
    for gia, ele in enumerate(datas.grades):
        if ele >= 80:
            swords.append(swords_ap[gia])

    swords = str(swords)
    sswords = swords.replace("[",",").replace("]",",").replace("'","").replace('"',"").replace(", ",",")        

    #print('puzzle datas:', datas)
    if datas.setlevel == False: 
        """ extracción que no verificaba si era con las palabras aprendidas
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
        """

        neo4j_statement = "with '" + org + "' as org \n" + \
                    " , '" + userId + "' as userId \n" + \
                    "//, 1 as idCat, 1 as idSCat \n" + \
                    "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-\n" + \
                    "[rc:SUBJECT]-(c:Category)-[rsc:CAT_SUBCAT]-(sc:SubCategory) \n" + \
                    "with u,o.lSource as Source, o.lTarget as Target, o, sc \n" + \
                    "// *** SE LOCALIZAN LAS SENTENCIAS QUE YA SE HAN EJERCITADO \n" + \
                    "optional match (u)<-[r:PUZZLEWORDS]-(gm:Game)  \n" + \
                    "with u, Source, Target, o, sc, coalesce(gm.words,['']) as wordsgame \n" + \
                    "unwind wordsgame as word  \n" + \
                    "with u, Source, Target, o, sc,  word \n" + \
                    "order by word  \n" + \
                    "with u, Source, Target, o, sc, collect(distinct word) as wordsgame \n" + \
                    "with u, Source, Target, o, sc, wordsgame, apoc.coll.shuffle(wordsgame) as wordsgameSh \n" + \
                    "// SE LOCALIZAN LAS PALABRAS ARCHIVADAS  \n" + \
                    "match (u)<-[r:ARCHIVED_M]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]->(sc)  \n" + \
                    "where o.lSource in labels(rM) and o.lTarget in labels(rM)  \n" + \
                    "// Y SE ELIMINAN LAS QUE FUERON LLEVADAS A JUEGOS  \n" + \
                    "with u, o, apoc.coll.subtract(rM.sentences, wordsgame) as words, wordsgame, \n" + \
                    " rM.sentences as rmwords, wordsgameSh  \n" + \
                    "with u, o, (case when words = [] then rmwords else words end) as words, \n" + \
                    " wordsgame, wordsgameSh  \n" + \
                    "unwind words as sword  \n" + \
                    "with u, o, collect(sword) as swords, wordsgameSh  \n" + \
                    "with u, o, swords + wordsgameSh[0..10] as swordsC, wordsgameSh  \n" + \
                    "unwind swordsC as sword  \n" + \
                    "with u, o, sword, \n" + \
                    "case when sword in wordsgameSh then 1 else 0 end as prioridad  \n" + \
                    "with distinct u, o, sword as we, prioridad  \n" + \
                    "order by u, prioridad, rand()  \n" + \
                    "limit " + rlimit + " \n" + \
                    "return we as sentence, apoc.coll.shuffle(split(we, ' ')) as wordstouser \n" + \
                    " , 'elementIdtoSound' as eletoshow, 0 as idSCat, ' ' as word, ' ' as exTarget \n" + \
                    " , we as original_sentence"
                    #"return we" Cat {idCat:idCat}  {idSCat:idSCat}

    else:        
        neo4j_statement = "with " + "'" + org + "' as org, \n" + \
                                "'" + userId + "' as userId, \n" + \
                                "'" + kogame + "' as kogame, \n" + \
                                str(yearr) + " as yearr, \n" + \
                                str(monthh) + " as monthh, \n" + \
                                str(weekk) + " as weekk, \n" + \
                                swords + ' as words, \n' + \
                                '"' + sswords + '" as swords, \n' + \
                                swords_complete + " as swords_complete, \n" + \
                                str(datas.grades) + " as swords_grades, \n" + \
                                str(datas.avg) + " as average, \n" + \
                                "1 as idCat, 1 as idSCat \n" + \
                    "match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})\n" + \
                    "with u, kogame, userId, yearr, monthh, weekk, \n" + \
                        "o.lSource as Source, o.lTarget as Target, words, swords, average, \n" + \
                        "swords_complete, swords_grades \n" + \
                    "merge (u)<-[rg:" + kogame + "]-(gm:Game \n" + \
                        "{game:kogame, userId:userId, swords:swords, \n" + \
                            " year:yearr, month:monthh, week:weekk}) \n" + \
                    "set gm.lSource = Source, gm.lTarget = Target, \n" + \
                        " gm.words = words, \n" + \
                    " gm.words_complete = swords_complete, \n" + \
                    " gm.grades = swords_grades, \n" + \
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
    # datas.org
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

    orgId = datas.orgId

    if userId == 'jagr':   # usuario de jiduma para probar aleman
        orgId = 'DTL-02'        
    
    if orgId == 'DTL-01':
        source = 'English'
        target = 'Spanish'
        idCat = 1
        idSCat = 1
    elif orgId == 'DTL-02':
        source = 'German'
        target = 'Spanish'
        idCat = 101
        idSCat = 1
    else:
        source = None
        target = None

    if datas.setlevel == False:
        statement = "with '" + orgId + "' as org \n" + \
                    "match (og:Organization {idOrg:org}) \n" + \
                    "match (we:Word:" + source + ") \n" + \
                    "where exists {(we)-[r:TRANSLATOR]->(ws:Word:" + target + ")} \n" + \
                    " and exists {(we)-[r:PRONUNCIATION]->(wss:WordSound:" + source + ")} \n" + \
                    "with we order by we.wordranking, we.word \n" + \
                    "skip "  + str(datas.starton) + " \n" + \
                    "limit " + str(datas.limit) + "\n" + \
                    "return we.word as word, we.wordranking as prevmax"        
    else:
        if datas.starton <= 10: 
            statement = "with '" + orgId + "' as org \n" + \
                        "match (u:User {userId:'" + userId + "'}) \n" + \
                        "-[ruo:RIGHTS_TO]-> \n" + \
                        "(og:Organization {idOrg:org}) \n" + \
                        "<-[rc:SUBJECT]-(c:Category {idCat:"+ str(idCat) + "}) \n" + \
                        "<-[rcs:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "}) \n" + \
                        "with og, c.idCat as idCat, sc, u \n" + \
                        "merge (arcM:Archived_M:" + source + ":" + target + " {userId:'" + userId + "', \n" + \
                        "    source:og.lSource, target:og.lTarget, \n" + \
                        "    idCat:idCat, idSCat:sc.idSCat, reference:'Initial_Level'}) \n" + \
                        "on create set arcM.ctInsert = datetime() \n" + \
                        "on match set arcM.ctUpdate = datetime(),  \n" + \
                            "arcM.wordsBack=[toString(datetime())] + arcM.words \n" + \
                        "set arcM.words = [], arcM.month_qty = 0, arcM.sentences=[] \n" + \
                        "merge (u)<-[rua:ARCHIVED_M]-(arcM)-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                        "return arcM.words[1..10], arcM.wordsBack[1..10] \n"
        else:
            statement = "with '" + orgId + "' as org, \n" + \
                        "'" + str(datas.word) + "' as word \n" + \
                        "match (u:User {userId:'" + userId + "'}) \n" + \
                        "-[ruo:RIGHTS_TO]-> \n" + \
                        "(og:Organization {idOrg:org}) \n" + \
                        "<-[rc:SUBJECT]-(c:Category {idCat:"+ str(idCat) + "}) \n" + \
                        "<-[rcs:CAT_SUBCAT]-(sc:SubCategory {idSCat:" + str(idSCat) + "}) \n" + \
                        "with og, c.idCat as idCat, sc, u \n" + \
                        "optional match (sc)<-[:SUBCAT_ARCHIVED_M]-(arcM2:Archived_M:" + source + ":" + target + ")-\n" + \
                            "[:ARCHIVED_M]->(u) \n" + \
                        "where arcM2.reference is null " + \
                        "with og, idCat, sc, u, coalesce(arcM2.words,['.']) as words \n" + \
                        "unwind words as word \n" + \
                        "with og, idCat, sc, u, collect(word) as wordsarcM \n" + \
                        "match (we:Word:" + source + ") \n" + \
                        "with og, idCat, sc, u, wordsarcM, we \n" + \
                        "//order by we.wordranking, we.word \n" + \
                        "// limit " + str(datas.starton) + " \n" + \
                        "//with og, idCat, sc, u, wordsarcM, we \n" + \
                        "match (we) \n" + \
                        "where not we.word in wordsarcM \n" + \
                        " and exists {(we)-[r:TRANSLATOR]->(ws:Word:" + target + ")} \n" + \
                        " and exists {(we)-[r:PRONUNCIATION]->(wss:WordSound:" + source + ")} \n" + \
                        "with og, idCat, sc, u, wordsarcM, we \n" + \
                        "order by we.wordranking, we.word \n" + \
                        "limit " + str(datas.starton) + " \n" + \
                        "with og, idCat, sc, u, collect(we.word) as words \n"  + \
                        "merge (arcM:Archived_M:" + source + ":" + target + " {userId:'" + userId + "', \n" + \
                        "    source:og.lSource, target:og.lTarget, \n" + \
                        "    idCat:idCat, idSCat:sc.idSCat, reference:'Initial_Level'}) \n" + \
                        "on create set arcM.ctInsert = datetime() \n" + \
                        "on match set arcM.ctUpdate = datetime(),  \n" + \
                            "arcM.wordsBack=[toString(datetime())] + arcM.words \n" + \
                        "set arcM.words = words, arcM.month_qty = size(words), arcM.sentences=[] \n" + \
                        "merge (u)<-[rua:ARCHIVED_M]-(arcM)-[:SUBCAT_ARCHIVED_M]->(sc) \n" + \
                        "//return arcM.words, arcM.wordsBack  \n" + \
                        "// TO INCLUDE EXAMPLE SENTENCES \n" + \
                        "with words as pwords, arcM, sc \n" + \
                        "unwind pwords as word \n" + \
                        "match (we:Word:" + source + " {word:word})-[:PRONUNCIATION]->\n" + \
                        "(wss:WordSound:" + source + ") \n" + \
                        "where exists {(wss)-[:SUBCAT]-(sc)} or \n" + \
                        " (wss.idCat = sc.idCat and wss.idSCat = sc.idSCat) \n" + \
                        "with arcM, sc, wss.example as wssexample \n" + \
                        ",replace( \n" + \
                        "  replace( \n" + \
                        "   replace( \n" + \
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
                        "     ) \n" + \
                        "    , word + ' - ' \n" + \
                        ", ''\n" + \
                        "    ) \n" + \
                        "    , apoc.text.capitalize(word) + '.' \n" + \
                        "    , ''\n" + \
                        "    ) \n" + \
                        "    , apoc.text.capitalizeAll(word) + '.' \n" + \
                        "    , ''\n" + \
                        ") \n" + \
                        "as sentence2 \n" + \
                        "with arcM, sc, collect(wssexample) as wssexamples, collect(sentence2) as sentences2 " + \
                        "set arcM.sentences = arcM.sentences + [ele in sentences2 where not ele in arcM.sentences] \n" + \
                        "return arcM.words[1..10], arcM.wordsBack[1..10] \n"
    
    await awsleep(0)
    #print("\n\nstatement leval:\n", statement)
    print("====================================================================\n") #{statement}")
    print("datas: ", datas, "\n", _getdatime_T(),"\n") 
    print("====================================================================\n") #{statement}")

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

"""

with True as adj, 
True as verb, 
False as ptense, 
True as noun, 
True as adv, 
 True as prep, True as conj, True as pron, 
'DTL-01' as org, 
'jaiv' as userId 
match (u:User {userId:userId})-[ro:RIGHTS_TO]-(o:Organization {idOrg:org})-
[rc:SUBJECT]-(c:Category)-[rsc:CAT_SUBCAT]-(sc:SubCategory) 
with u,o.lSource as Source, o.lTarget as Target, o, sc, 
    adj, verb, noun, adv, prep, ptense, conj, pron 
// *** SE LOCALIZAN LAS PALABRAS QUE YA SE HAN EJERCITADO 
optional match (u)<-[r:TRY_TW]-(gm:Game) 
where not type(r) in ['PUZZLEWORDS'] 
with u, Source, Target, o, sc, coalesce(gm.words,['']) as wordsgame, 
    adj, verb, noun, adv, prep, ptense, conj, pron 
unwind wordsgame as word 
with u, Source, Target, o, sc,  word, 
adj, verb, noun, adv, prep, ptense, conj, pron 
order by word 
with u, Source, Target, o, sc, collect(distinct word) as wordsgame, 
    adj, verb, noun, adv, prep, ptense, conj, pron 
with u, Source, Target, o, sc, wordsgame, apoc.coll.shuffle(wordsgame) as wordsgameSh, 
    adj, verb, noun, adv, prep, ptense, conj, pron 
// SE LOCALIZAN LAS PALABRAS ARCHIVADAS 
match (u)<-[r:ARCHIVED_M]-(rM:Archived_M)-[rsm:SUBCAT_ARCHIVED_M]->(sc) 
where o.lSource in labels(rM) and o.lTarget in labels(rM) 
// Y SE ELIMINAN LAS QUE FUERON LLEVADAS A JUEGOS 
with u, o, sc, apoc.coll.subtract(rM.words, wordsgame) as words, wordsgame, rM.words as rmwords, 
  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh 
with u, o, sc, (case when words = [] then rmwords else words end) as words, wordsgame,  
  adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh 
unwind words as sword 
with u, o, sc, collect(sword) as swords, adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh 
with u, o, sc, swords + wordsgameSh[0..6] as swordsC, 
 adj, verb, noun, adv, prep, ptense, conj, pron, wordsgameSh 
unwind swordsC as sword 
with u, o, sword, adj, verb, noun, adv, prep, ptense, conj, pron, 
   sc.idCat as idCat, sc.idSCat as idSCat, 
   case when sword in wordsgameSh then 1 else 0 end as prioridad 
// SE OBTIENE LA PRONUNCIACION 
match (we:WordSound {word:sword}) 
where o.lSource in labels(we) and not we.word contains ' ' 
   and we.idCat = idCat and we.idSCat = idSCat 
with distinct u, o, we, adj, verb, noun, adv, prep, ptense, conj, pron, prioridad, 
     elementId(we) as soundId, we.word as worde, 
     ' ' as ckow, we.word as words 
order by prioridad, // worde in swords desc, 
 worde 
with u, soundId, prioridad, worde, ckow, collect(words) as words 
order by u, prioridad, rand() 
limit 3 
return worde, words, ckow, soundId 
"""