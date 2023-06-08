from fastapi import APIRouter
from . import dt_ui_oper_lv 

api_router = APIRouter()
api_router.include_router(dt_ui_oper_lv.router,prefix="/dt/ui_oper_lv",tags=["dtui_oper_lv"])
#api_router.include_router(ui_oper_lv_p.router,prefix="/dt_ui_oper_lvp",tags=["ui_oper_lvp"])


