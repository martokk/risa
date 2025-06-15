from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.logic import state
from framework.core.db import get_db
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter(tags=["State"])


@router.get("/state/instance", response_class=HTMLResponse)
async def instance_state_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the instance state page."""

    instance_state = await state.get_instance_state()
    context["instance_state"] = instance_state

    return templates.TemplateResponse(
        request=request,
        name="state/instance.html",
        context=context,
    )


@router.get("/state/network", response_class=HTMLResponse)
async def network_state_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the network state page."""

    network_state = await state.get_network_state_from_host()
    context["network_state"] = network_state

    return templates.TemplateResponse(
        request=request,
        name="state/network.html",
        context=context,
    )
