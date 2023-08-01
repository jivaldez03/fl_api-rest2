"""
https://www.youtube.com/watch?v=J0y2tjBz2Ao

python3 -m venv fastapi_env

pip install fastapi

pip install uvicorn

// crear programa con función
//activar uvicorn


en heroku esta como fl-api-rest

uvicorn main:app --reload --host 

cd Documents/proyectos/fl_api-rest2
source __flapiR2/bin/activate
uvicorn main_fapirest:app --reload --host localhost --port 3000 --timeout-keep-alive=20 --limit-concurrency=30
"""
#from fastapi import HTTPException #, FastAPI
from app import create_app 
#, app_fastapi as app
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

def include_router():
    global app
    app.include_router(dt_auth_router)
    app.include_router(dt_api_oper_gr_router)
    app.include_router(dt_api_oper_lv_router)
    return

	#app.include_router(api_router)   # login + auth
	#app.include_router(api_oper_gr_router)   # ui - operaciones generales        
	#app.include_router(api_oper_lv_router)   # ui - operaciones de registro de avance    
	#app.include_router(dt_auth_router)   # ui - testing
	#app.include_router(dt_api_oper_gr_router)   # ui - testing
	#app.include_router(dt_api_oper_lv_router)   # ui - testing

       
#appNeo, session, log = trx.connectNeo4j('admin', 'starting session')

app = create_app()
include_router()

def _gunic_create_app():
     global app
     app = create_app()
     include_router()
     return app

@app.get("/")
def index():
    return "Hello EVERYBODY ..... dELTA-pHASE is now working for you"

@app.get("/hello")
def helloworld():
    return {'message': "hello world"}


if __name__ == "__main__":
    #print('GETENV:', getenv("SEC_KEY")) 
    app.run(host='0.0.0.0', port=3000, debug=True)
