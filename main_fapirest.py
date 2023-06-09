"""
https://www.youtube.com/watch?v=J0y2tjBz2Ao

python3 -m venv fastapi_env

pip install fastapi

pip install uvicorn

// crear programa con función
//activar uvicorn

uvicorn main:app --reload --host 

cd Documents/proyectos/fl_api-rest2
source __flapiR2/bin/activate
uvicorn main_fapirest:app --reload --host localhost --port 3000 --timeout-keep-alive=20 --limit-concurrency=30
"""
#from fastapi import HTTPException #, FastAPI
from app import create_app, app_fastapi as app
from fastapi import Response #, Header
#from typing import Optional

#import __generalFunctions as funcs
from __generalFunctions import myfunctionname

#from app.model.md_books import Book
#from uuid import  uuid4 as uuid
from random import randint 
from _neo4j import neo4j_operations as trx 
from _neo4j import appNeo, session, log

#from app.auth.base import api_router
#from app.ui_oper_gr.base import api_router as api_oper_gr_router
#from app.ui_oper_lv.base import api_router as api_oper_lv_router

from app.dt_auth.base import api_router as dt_auth_router
from app.dt_ui_oper_gr.base import api_router as dt_api_oper_gr_router
from app.dt_ui_oper_lv.base import api_router as dt_api_oper_lv_router

def include_router(app):
	#app.include_router(api_router)   # login + auth
	#app.include_router(api_oper_gr_router)   # ui - operaciones generales        
	#app.include_router(api_oper_lv_router)   # ui - operaciones de registro de avance    
	app.include_router(dt_auth_router)   # ui - testing
	app.include_router(dt_api_oper_gr_router)   # ui - testing
	app.include_router(dt_api_oper_lv_router)   # ui - testing

#app = create_app()
include_router(app)

        
#appNeo, session, log = trx.connectNeo4j('admin', 'starting session')

"""
import requests
url = 'https://fl-api-rest.herokuapp.com/get_/categories/jcdelangel'
data = requests.get(url)
if data.status_code == 200: # ok
	datas = data.json()
	for data in datas:
		print(data)
          
class Book(BaseModel):
    title: str
    author: str
    pages: int
    editorial: Optional[str]
"""

@app.get("/")
def index():
    return "Hello EVERYBODY ..... dELTA-pHASE is now working for you"

#@app.get("/hello")
def helloworld():
    return {'message': "hello world"}

#@app.get("/get_/categories/{user_id}")
def get_categories_subc(user_id):
    listcat = [{ 'category': 'Anathomy'
                        , 'idCat': 'cat.01.01'
                        , 'subcategories' : [
                            {'subcategory': 'human body' , 'idSCat': 'scat.01.01'}
                            , {'subcategory': 'human skeleton' , 'idSCat': 'scat.01.02'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.01.00'}
                        ]
                }
                , {'category': 'Animals'
                        , 'idCat': 'cat.01.02'
                        , 'subcategories' : [
                            {'subcategory': 'aquatics' , 'idSCat': 'scat.03.01'}
                            , {'subcategory': 'amphibians' , 'idSCat': 'scat.03.02'}
                            , {'subcategory': 'mamals' , 'idSCat': 'scat.03.03'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.03.00'}
                        ]        
                }, {'category': 'Music'
                        , 'idCat': 'cat.01.04'
                        , 'subcategories' : [
                            {'subcategory': 'Instruments' , 'idSCat': 'scat.04.01'}
                            , {'subcategory': 'Famous Classical Compositors' , 'idSCat': 'scat.04.02'}
                            , {'subcategory': 'Famous Jazz Musician' , 'idSCat': 'scat.04.03'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.04.00'}
                        ]        
                }, {'category': 'Geography'
                        , 'idCat': 'cat.01.05'
                        , 'subcategories' : [
                            {'subcategory': 'Mountains' , 'idSCat': 'scat.05.01'}
                            , {'subcategory': 'Rivers' , 'idSCat': 'scat.05.02'}
                            , {'subcategory': 'Continents/Oceans/Gulfs' , 'idSCat': 'scat.05.03'}
                            , {'subcategory': 'Countries/Capitals' , 'idSCat': 'scat.05.03'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.05.00'}
                        ]        
                }
               ]
    return {'message': listcat}


#@app.get("/get_/categories2/{user_id}")
def get_categories2(user_id):
    global appNeo, session, log
    listcat = [{ 'category': 'Anathomy'
                        , 'idCat': 'cat.01.01'
                        , 'subcategories' : [
                            {'subcategory': 'human body' , 'idSCat': 'scat.01.01'}
                            , {'subcategory': 'human skeleton' , 'idSCat': 'scat.01.02'}
                            , {'subcategory': '_alls' , 'idSCat': 'scat.01.00'}
                        ]
                }
               ]
    user = 'admin'
    #app = None
    #session = None
    if session == None:
        appNeo, session, log = trx.connectNeo4j(user, 'cat&subcat updating')

    ne04j_statement = "match (o:Organization {idOrg:'DTL-01'})<-[]-(c:Category)<--(s:SubCategory) " + \
                        "with c, s.name as subcategory, s.idSCat as idSCat " + \
                        "order by c.name, subcategory " + \
                        "return c.name as category, c.idCat as idCat, " + \
                                "collect(subcategory) as subcategories, collect(idSCat) as subid" 
    
    nodes, log = trx.neo4j_exec(session, user,
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
            #npackage.append((value, sdict["slTarget"][gia], gia + 1 ))        
        ndic["subcategories"] = subcat_list[:]
        listcat.append(ndic)

    return {'message': listcat}

"""
@app.get("/get_/user_words/{user_id} {idSCatName}")
def get_user_words(user_id, idSCatName):
    if randint(1,10) < 5:
        sdict = {'idUser': 'jivaldez03', 'subCat': 'kitchen', 
                'slSource': ['kettle', 'toaster', 'microwave oven', 
                            'refrigerator (“fridge”)', 'dishwasher', 
                            'breadbox', 'pitcher (or jug)', 'blender'], 
                'slTarget': ['tetera', 'tostador', 'microondas', 
                            'refrigerador', 'lavavajillas', 
                            'panera', 'jarra', 'batidora']}
    else:
        sdict = {'idUser': 'jivaldez03', 'subCat': 'Sentences', 
                'slSource': ['good morning', 'good afternoon', 'good evening', 
                             'good night', 'goodbye', 'my name is ~ laura ~', 
                             'see you soon', 'see you later'], 
                'slTarget': ['buenos días', 'buenas tardes', 
                             'buenas noches (al llegar)', 'buenas noches', 
                             'adiós', 'mi nombre es laura', 
                             'te veo pronto', 'te veo mas tarde']}
    npackage = []
    prnFileName, prnLink = '', ''
    for gia, value in enumerate(sdict['slSource']):
        npackage.append((value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink))
    return npackage


@app.get("/get_/get_testing_Heroku")
def get_testing_Heroku(user_id, idSCatName):
    s_url = 'https://fl-api-rest.herokuapp.com/get_/user_words2/ijcesar%2012'
    rHeroku = geturl(s_url)
    print(f"geturlStatus: {rHeroku.status_code} on url = {s_url}")
    print(f"get: {rHeroku.text}")
    return rHeroku.text
"""

"""
@app.get("/books/author/{id_book} {id_sin}")
def book_author(id_book:int, id_sin):
    if id_sin == None:
        id_sin = 'n/a'
    elif id_sin != '....':
        pass
    else:
        raise HTTPException(status_code=404, detail="record not found")

    return {'id': id_book
            ,'author': 'Jorge Iduvas'
            , 'sin_code': id_sin
            }

@app.post("/books/new_book/")
def new_book(book: Book):
    return {'message': f"{book.title} insertado"
            }
"""
#resp = make_response(redirect('http://127.0.0.1:8000/hello'))
#print(resp)

"""
@app.get("/get_/user_words_neo/{user_id} {idSCatName}")
def get_user_words_neo(user_id, idSCatName):  
    user = 'admin'
    app = None
    session = None
    if session == None:
        app, session, log = trx.connectNeo4j(user, 'cat&subcat updating')

    idUser = 'jivaldez03'
    idCatName = 'Sentences' #'Home'
    idSCatName = 'Sentences' #'kitchen'
    lgSource = 'English'
    lgTarget = 'Spanish'

    ne04j_statement = "match (u:User {alias:'" + idUser + "'}) " + \
                "match (c:Category {name:'" + idCatName + "'})-[:CAT_SUBCAT]-" +\
                    "(s:SubCategory {name:'" + idSCatName + "'}) " + \
                "match (s)-[scat:SUBCAT]-(ew:ElemSubCat:" + lgSource + ")-[:TRANSLATOR]-" + \
                    "(sw:ElemSubCat:" + lgTarget + ") " + \
                "where  not ew.word in u." + idSCatName + " or u." + idSCatName + " is NULL " + \
                "with s, u, ew, sw, scat " + \
                "order by scat.wordranking " + \
                "with s, u, collect(ew.word) as ewlist, collect(sw.word) as swlist " + \
                "return u.alias as idUser, s.name as subCat, " + \
                        "ewlist[0..8] as slSource, swlist[0..8] as slTarget"

    if session == None:
        app, session, log = trx.connectNeo4j(user, 'cat&subcat updating')

    #print(app, session)
    nodes, log = trx.neo4j_exec(session, user,
                        log_description="getting words for user",
                        statement=ne04j_statement)
    #print(type(nodes))
    for node in nodes:
        sdict = dict(node)        
        #print(dict(node))
        npackage = []
        prnFileName, prnLink = '', ''
        for gia, value in enumerate(sdict['slSource']):
            npackage.append((value, sdict["slTarget"][gia], gia + 1, prnFileName, prnLink))
    return npackage
"""

#@app.get("/get_/user_words2/{user_id} {idSCat}")
def get_user_words2(user_id:str, idSCat:int):
    global appNeo, session, log
    user = 'admin'
    #appNeo = None
    #session = None
    if session == None:
        appNeo, session, log = trx.connectNeo4j(user, 'cat&subcat updating')

    ne04j_statement_pre = "match (o:Organization)<-[]-(c:Category)" + \
                            "<-[:CAT_SUBCAT]-(s:SubCategory {idSCat:" + str(idSCat) + "}) " + \
                            "return o.idOrg as idOrg, o.lSource as lSource, " + \
                                    "o.lTarget as lTarget, s.name as idSCatName limit 1" 
    
    nodes, log = trx.neo4j_exec(session, user,
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
                    "ewlist[0..8] as slSource, " + \
                    "swlist[0..8] as slTarget"
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
                                "ewlist[0..8] as slSource, swlist[0..8] as slTarget"
                
        nodes, log = trx.neo4j_exec(session, user,
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
        nodes, log = trx.neo4j_exec(session, user,
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


@app.get("/get_/user_word_pron2/{word} {idWord}")
def get_user_word_pron2(word, idWord):
    global appNeo, session, log
    user = 'admin'
    #appNeo = None
    #session = None
    if session == None:
        appNeo, session, log = trx.connectNeo4j(user, 'cat&subcat updating')

    statement = 'match (ws:WordSound {word: "' +  word + '"}) ' + \
                "where id(ws) = " + str(idWord) + " " + \
                "return ws.binfile limit 1"  # ws.word, ws.actived, 
    print(f"statement pronun: {statement}")
    nodes, log = trx.neo4j_exec(session, user,
                        log_description="getting pronunciation word",
                        statement=statement,
                        filename=__name__, 
                        function_name=myfunctionname())
    
    for ele in nodes:
        elems = dict(ele)
        #print(type(f), type(ele), ele, elems['ws.word'], elems['ws.actived'])
        #fw=open('savedfile4.mp3','wb')
        #fw.write(elems['ws.binfile'])
        #fw.close() 
        return Response(elems['ws.binfile'])

if __name__ == "__main__":
    #print('GETENV:', getenv("SEC_KEY")) 
    app.run(host='0.0.0.0', port=3000, debug=True)
