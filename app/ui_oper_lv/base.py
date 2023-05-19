from fastapi import APIRouter
from . import ui_oper_lv, ui_oper_lv_p

api_router = APIRouter()
api_router.include_router(ui_oper_lv.router,prefix="/ui_oper_lv",tags=["ui_oper_lv"])
api_router.include_router(ui_oper_lv_p.router,prefix="/ui_oper_lvp",tags=["ui_oper_lvp"])

