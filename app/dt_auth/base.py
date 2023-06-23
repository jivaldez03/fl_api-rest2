from fastapi import APIRouter
from . import dt_user_acc, dt_user_rec
from __generalFunctions import _getenv_function 

api_router = APIRouter()
#api_router.include_router(route_general_pages.general_pages_router,prefix="",tags=["general_pages"])
#api_router.include_router(dt_user_acc.router,prefix="/dt/auth",tags=["dtauth"])
api_router.include_router(dt_user_acc.router,prefix=_getenv_function("addressAuth"),tags=[_getenv_function("laddressAuth")])
api_router.include_router(dt_user_rec.router,prefix=_getenv_function("addressAuth"),tags=[_getenv_function("laddressAuth")])

