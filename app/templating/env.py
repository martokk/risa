from fastapi.templating import Jinja2Templates

from app.frontend.templates.filters import (
    filter_humanize_network,
    filter_humanize_network_text_color,
)
from app.logic.state import get_network_state
from vcore.backend.core.db import get_db_context


def hook_inject_app_templating_env(templates: Jinja2Templates) -> Jinja2Templates:
    with get_db_context() as db:
        network_state = get_network_state(db=db)

    # Add custom filters to templates
    templates.env.filters["humanize_network"] = filter_humanize_network
    templates.env.filters["humanize_network_text_color"] = filter_humanize_network_text_color

    # Add global variables to templates
    templates.env.globals["ENV_NAMES"] = ["dev", "local", "playground", "host"]

    templates.env.globals["RISA_HOST_ACCENT"] = network_state.host.accent
    templates.env.globals["RISA_HOST_BASE_URL"] = network_state.host.base_url

    templates.env.globals["RISA_DEV_ACCENT"] = network_state.dev.accent
    templates.env.globals["RISA_DEV_BASE_URL"] = network_state.dev.base_url

    templates.env.globals["RISA_LOCAL_ACCENT"] = network_state.local.accent
    templates.env.globals["RISA_LOCAL_BASE_URL"] = network_state.local.base_url

    templates.env.globals["RISA_PLAYGROUND_ACCENT"] = network_state.playground.accent
    templates.env.globals["RISA_PLAYGROUND_BASE_URL"] = network_state.playground.base_url
    templates.env.globals["RISA_PLAYGROUND_RUNPOD_POD_ID"] = (
        f"https://{network_state.playground.runpod_pod_id}"
    )

    return templates
