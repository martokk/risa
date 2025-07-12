from fastapi.templating import Jinja2Templates

from app import paths
from vcore.backend.templating.env import set_template_env


def get_templates() -> Jinja2Templates:
    """
    Create Jinja2Templates object and add global variables to templates.

    Returns:
        Jinja2Templates: Jinja2Templates object.
    """
    # Create Jinja2Templates object
    templates = Jinja2Templates(directory=paths.TEMPLATES_PATH)

    templates = set_template_env(templates)
    return templates


templates = get_templates()
