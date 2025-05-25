from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.views.templates import templates
from app.views.templates.context import get_template_context


router = APIRouter()


@router.get("/context-templates", response_class=HTMLResponse)
async def context_templates_list_page(
    request: Request,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Render the list page for all context templates."""
    templates_list = await crud.context_template.get_all(db)
    context["templates"] = templates_list
    return templates.TemplateResponse("context_templates/list.html", context)


@router.get("/context-templates/{template_id}", response_class=HTMLResponse)
async def context_template_detail_page(
    request: Request,
    template_id: int,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Render the detail page for a single context template."""
    template = await crud.context_template.get(db, id=template_id)
    context["template"] = template
    return templates.TemplateResponse("context_templates/detail.html", context)
