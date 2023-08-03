from fastapi import APIRouter 
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
async def get_root():
    """
    Function to redirect a /docs

    """
    return RedirectResponse('/docs')