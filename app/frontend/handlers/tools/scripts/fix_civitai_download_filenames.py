from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.models import settings
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter()


@router.get("/tools/fix-civitai-download-filenames", response_class=HTMLResponse)
async def fix_civitai_download_filenames_page(
    request: Request,
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Page for the Fix Civitai Download Filenames tool.

    Args:
        request: FastAPI request object
        context: Template context dictionary

    Returns:
        HTML response with rendered template
    """
    context["hub_path"] = settings.HUB_PATH
    return templates.TemplateResponse(
        "tools/fix_civitai_download_filenames.html",
        context,
    )
