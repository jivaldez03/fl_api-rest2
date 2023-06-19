from fastapi import APIRouter
from . import dt_ui_oper_lv 
from __generalFunctions import _getenv_function

api_router = APIRouter()
#api_router.include_router(dt_ui_oper_lv.router,prefix="/dt/ui_oper_lv",tags=["dtui_oper_lv"])
api_router.include_router(dt_ui_oper_lv.router,prefix=_getenv_function("addressOperLv")
                          ,tags=[_getenv_function("laddressOperLv")])



