from fastapi import APIRouter
from . import ui_oper_bs

api_router = APIRouter()
api_router.include_router(ui_oper_bs.router,prefix="/ui_oper_gr",tags=["ui_oper_gr"])
