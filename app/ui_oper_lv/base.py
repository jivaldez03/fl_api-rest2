from fastapi import APIRouter
from . import ui_oper_lv


api_router = APIRouter()
api_router.include_router(ui_oper_lv.router,prefix="/ui_oper_lv",tags=["ui_oper_lv"])

