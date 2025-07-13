from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import settings
from vcore.backend import crud, models
from vcore.backend.core.db import get_db
from vcore.backend.templating import templates
from vcore.backend.templating.context import get_template_context


router = APIRouter()


@router.get("/job-schedulers", response_class=HTMLResponse)
@router.get("/job-schedulers/{env_name}", response_class=HTMLResponse)
async def job_schedulers_page(
    request: Request,
    env_name: str | None = None,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    env_name = env_name or settings.ENV_NAME
    if env_name == "all":
        schedulers = await crud.job_scheduler.get_all(db=db)
    else:
        schedulers = await crud.job_scheduler.get_multi(db=db, env_name=env_name)
    on_start_schedulers = [
        s for s in schedulers if s.trigger_type == models.JobSchedulerTriggerType.on_start
    ]
    repeat_schedulers = [
        s for s in schedulers if s.trigger_type == models.JobSchedulerTriggerType.repeat
    ]
    context["env_name"] = env_name
    context["on_start_schedulers"] = on_start_schedulers
    context["repeat_schedulers"] = repeat_schedulers
    return templates.TemplateResponse("jobs/job_scheduler.html", context)
