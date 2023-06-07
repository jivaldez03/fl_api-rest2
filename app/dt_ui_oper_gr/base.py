from fastapi import APIRouter
from . import dt_ui_oper_bs

api_router = APIRouter()
api_router.include_router(dt_ui_oper_bs.router,prefix="/dt/ui_oper_gr",tags=["dtui_oper_gr"])