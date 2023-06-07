from fastapi import APIRouter
from . import dt_user_acc

api_router = APIRouter()
#api_router.include_router(route_general_pages.general_pages_router,prefix="",tags=["general_pages"])
api_router.include_router(dt_user_acc.router,prefix="/dt/auth",tags=["dtauth"])
