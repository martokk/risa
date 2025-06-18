from fastapi.templating import Jinja2Templates

from app.logic.state import get_network_state
from framework.core.db import get_db_context


def hook_get_templates(templates: Jinja2Templates) -> Jinja2Templates:
    with get_db_context() as db:
        network_state = get_network_state(db=db)

    templates.env.globals["RISA_HOST_ACCENT"] = network_state.host.accent
    templates.env.globals["RISA_HOST_BASE_DOMAIN"] = network_state.host.base_domain

    templates.env.globals["RISA_DEV_ACCENT"] = network_state.dev.accent
    templates.env.globals["RISA_DEV_BASE_DOMAIN"] = network_state.dev.base_domain

    templates.env.globals["RISA_LOCAL_ACCENT"] = network_state.local.accent
    templates.env.globals["RISA_LOCAL_BASE_DOMAIN"] = network_state.local.base_domain

    templates.env.globals["RISA_PLAYGROUND_ACCENT"] = network_state.playground.accent
    templates.env.globals["RISA_PLAYGROUND_BASE_DOMAIN"] = network_state.playground.base_domain

    return templates
