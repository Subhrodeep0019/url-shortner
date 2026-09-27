from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import HttpUrl
from src.config import settings

from src.link.schemas import LinkCreateModel, LinkResponseModel
from src.link.service import get_link_service, LinkService

from src.db.models import Link


link_router = APIRouter()

@link_router.post(
    "/shorten_url/",
    response_model=LinkResponseModel,
    status_code=status.HTTP_201_CREATED
)
async def shorten_url(
        link_payload: LinkCreateModel,
        link_service: LinkService = Depends(get_link_service)
):
    link: Link = await link_service.create_link(link_payload)
    short_ = f"{settings.BASE_URL}/r/{link.short_code}/"

    return LinkResponseModel(
        uid=link.uid,
        short_url=short_,
        long_url=HttpUrl(link.long_url),
        created_at=link.created_at,
        expires_at=link.expires_at,
    )

@link_router.get(
    "/r/{short_code}",
)
async def redirect_url(
        short_code: str,
        link_service: LinkService = Depends(get_link_service),
):
    long_url = await link_service.get_long_url(short_code)
    if long_url is None:
        # raise custom error later
        raise HTTPException(
            detail="no link found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return RedirectResponse(
        url=long_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )

@link_router.delete(
    "/{short_code}"
)
async def delete_url(
        short_code: str,
        link_service: LinkService = Depends(get_link_service),
):
    if await link_service.soft_delete(short_code):
        return JSONResponse(
            content="Successfully deleted",
            status_code=status.HTTP_200_OK
        )
    else:
        raise HTTPException(
            detail="no link found",
            status_code=status.HTTP_404_NOT_FOUND
        )