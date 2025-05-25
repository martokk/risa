from typing import Any

from sqlmodel import Session


async def initialize_project_specific_data(db: Session, **kwargs: Any) -> None:
    """
    Initialize project specific data

    Extends app.core.db.initialize_tables_and_initial_data() with project specific data
    """

    pass
