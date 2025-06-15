from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from framework.core.db import get_db
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter(tags=["Characters"])


@router.get("/characters", response_class=HTMLResponse)
async def list_characters_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page listing all Characters."""
    characters = await crud.character.get_all(db=db)
    context["characters"] = characters
    return templates.TemplateResponse(
        request=request,
        name="character/character_list.html",
        context=context,
    )


@router.get("/character/create", response_class=HTMLResponse)
async def create_character_page(
    request: Request,
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for creating a new Character."""
    return templates.TemplateResponse(
        request=request,
        name="character/character.html",
        context=context,
    )


@router.get("/character/{character_id}", response_class=HTMLResponse)
async def character_page(
    request: Request,
    character_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for viewing and editing a specific Character."""
    character_obj = await crud.character.get(db=db, id=character_id)
    if not character_obj:
        raise HTTPException(status_code=404, detail="Character not found")

    context["character"] = character_obj
    return templates.TemplateResponse(
        request=request,
        name="character/character.html",
        context=context,
    )
