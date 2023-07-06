from fastapi import APIRouter
from . import dt_ui_oper_bs
from . import dt_ui_oper_gr
from __generalFunctions import _getenv_function

api_router = APIRouter()
#api_router.include_router(dt_ui_oper_bs.router,prefix="/dt/ui_oper_gr",tags=["dtui_oper_gr"])
api_router.include_router(dt_ui_oper_bs.router,prefix=_getenv_function("addressOperGr")
                          ,tags=[_getenv_function("laddressOperGr")])
api_router.include_router(dt_ui_oper_gr.router,prefix=_getenv_function("addressOperGr")
                          ,tags=[_getenv_function("laddressOperGr")])
