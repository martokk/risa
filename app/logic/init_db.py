from typing import Any

from sqlmodel import Session

from app import crud, models, settings


async def initialize_project_specific_data(db: Session, **kwargs: Any) -> None:
    """
    Initialize project specific data

    Extends app.core.db.initialize_tables_and_initial_data() with project specific data
    """

    network_env_list = ["dev", "local", "playground", "host"]

    for network_env in network_env_list:
        db_instance_network_env = await crud.instance_state.get_or_none(
            db,
            id=network_env,
        )
        if not db_instance_network_env:
            await crud.instance_state.create(
                db,
                obj_in=models.InstanceStateCreate(
                    id=network_env,
                    project_name=settings.PROJECT_NAME,
                    base_domain=settings.BASE_DOMAIN,
                ),
            )
