from typing import Any

from fastapi import Depends, Request
from sqlmodel import Session

from vcore.backend import models
from vcore.backend.core.db import get_db
from vcore.backend.templating.deps import get_current_active_user, get_tokens_from_cookie


async def get_template_context(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    tokens: models.Tokens = Depends(get_tokens_from_cookie),
) -> dict[str, Any]:
    """
    Get template context.
    """
    tokens = tokens if tokens else models.Tokens(access_token="", refresh_token="")
    return {
        "request": request,
        "current_user": current_user,
        "tokens": tokens,
    }
