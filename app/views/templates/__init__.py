from datetime import UTC, datetime

from fastapi.templating import Jinja2Templates

from app import paths, settings
from app.utils.datetime import format_datetime, utc_to_local
from app.views.templates.filters import (
    filter_humanize,
    filter_nl2br,
    format_date,
)


def get_templates() -> Jinja2Templates:
    """
    Create Jinja2Templates object and add global variables to templates.

    Returns:
        Jinja2Templates: Jinja2Templates object.
    """
    # Create Jinja2Templates object
    templates = Jinja2Templates(directory=paths.TEMPLATES_PATH)

    # Add custom filters to templates
    templates.env.filters["humanize"] = filter_humanize
    templates.env.filters["format_datetime"] = format_datetime
    templates.env.filters["utc_to_local"] = utc_to_local
    templates.env.filters["nl2br"] = filter_nl2br
    templates.env.filters["format_date"] = format_date

    # Add global variables to templates
    templates.env.globals["PROJECT_NAME"] = settings.PROJECT_NAME
    templates.env.globals["ENV_NAME"] = settings.ENV_NAME
    templates.env.globals["PACKAGE_NAME"] = settings.PACKAGE_NAME
    templates.env.globals["PROJECT_DESCRIPTION"] = settings.PROJECT_DESCRIPTION
    templates.env.globals["BASE_DOMAIN"] = settings.BASE_DOMAIN
    templates.env.globals["BASE_URL"] = settings.BASE_URL
    templates.env.globals["VERSION"] = settings.VERSION
    templates.env.globals["current_year"] = datetime.now(UTC).year

    return templates


templates = get_templates()
