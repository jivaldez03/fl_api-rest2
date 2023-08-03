from fastapi import APIRouter
from . import root

api_router = APIRouter()

api_router.include_router(root.router,prefix="",tags=[""])