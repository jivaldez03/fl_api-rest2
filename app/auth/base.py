from fastapi import APIRouter

#from .user_acc import route_general_pages
#from .user_acc import route_users
from . import user_acc

api_router = APIRouter()
#api_router.include_router(route_general_pages.general_pages_router,prefix="",tags=["general_pages"])
api_router.include_router(user_acc.router,prefix="/auth",tags=["auth"])