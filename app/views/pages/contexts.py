from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.views.templates import templates
from app.views.templates.context import get_template_context


router = APIRouter()


@router.get("/contexts", response_class=HTMLResponse)
async def contexts_list_page(
    request: Request,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Render the list page for all context templates."""

    # All Contexts
    contexts_list = await crud.context.get_all(db)
    context["contexts"] = contexts_list

    # All Context Templates
    context_tempaltes = await crud.context_template.get_all(db)
    context["context_templates"] = context_tempaltes

    return templates.TemplateResponse("contexts/list.html", context)


@router.get("/contexts/{context_id}", response_class=HTMLResponse)
async def context_detail_page(
    request: Request,
    context_id: int,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Render the detail page for a single context."""

    # Single Context
    context_obj = await crud.context.get(db, id=context_id)
    context["context"] = context_obj

    # All Context Templates
    context_tempaltes = await crud.context_template.get_all(db)
    context["context_templates"] = context_tempaltes

    return templates.TemplateResponse("contexts/detail.html", context)
