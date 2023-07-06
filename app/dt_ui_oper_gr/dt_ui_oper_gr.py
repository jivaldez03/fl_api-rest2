from fastapi import APIRouter, Response, Header
from typing import Optional
from _neo4j.neo4j_operations import neo4j_exec
from _neo4j import appNeo, session, log, user
import __generalFunctions as funcs
from __generalFunctions import myfunctionname, myConjutationLink, get_list_element,_getdatime_T, get_list_elements

from random import shuffle as shuffle

from app.model.md_params_oper import ForNamePackages

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
