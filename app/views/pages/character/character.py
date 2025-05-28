from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.views.templates import templates
from app.views.templates.context import get_template_context


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
    # No additional data needed for character creation form initially
    return templates.TemplateResponse(
        request=request,
        name="character/character_create.html",
        context=context,
    )


@router.get("/character/{character_id}/view", response_class=HTMLResponse)
async def view_character_page(
    request: Request,
    character_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for viewing a specific Character."""
    character_obj = await crud.character.get(db=db, id=character_id)
    if not character_obj:
        raise HTTPException(status_code=404, detail="Character not found")

    context["character"] = character_obj
    return templates.TemplateResponse(
        request=request,
        name="character/character_view.html",
        context=context,
    )


@router.get("/character/{character_id}/edit", response_class=HTMLResponse)
async def edit_character_page(
    request: Request,
    character_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for editing a specific Character."""
    character_obj = await crud.character.get(db=db, id=character_id)
    if not character_obj:
        raise HTTPException(status_code=404, detail="Character not found")
    context["character"] = character_obj
    return templates.TemplateResponse(
        request=request,
        name="character/character_edit.html",
        context=context,
    )
