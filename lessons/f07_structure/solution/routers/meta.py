from typing import Annotated

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings

router = APIRouter(tags=["meta"])


@router.get("/info")
def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {"app_name": settings.app_name, "debug": settings.debug}
