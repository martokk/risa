from collections.abc import Generator
from typing import Any

from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

from app import crud, logger, models, paths, settings
from app.logic.init_db import initialize_project_specific_data as _initialize_project_specific_data


db_url = f"sqlite:///{paths.DATABASE_FILE}"
engine = create_engine(
    db_url,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """
    A generator function that creates a new database session.

    Yields:
        db: A new database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_all(engine: Engine = engine, sqlmodel_create_all: bool = False) -> None:
    """
    Create all tables in the database.

    Args:
        engine (Engine): database engine.
        sqlmodel_create_all (bool): whether to create all tables using SQLModel.

    Returns:
        None
    """
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line or use
    # sqlmodel_create_all=True
    if sqlmodel_create_all:
        logger.debug("Initializing database...")
        SQLModel.metadata.create_all(bind=engine)
    return


async def initialize_tables_and_initial_data(db: Session, **kwargs: Any) -> None:
    """Initialize database with initial data"""

    await create_all(**kwargs)

    superuser = await crud.user.get_or_none(db=db, username=settings.FIRST_SUPERUSER_USERNAME)
    if not superuser:
        user_create = models.UserCreateWithPassword(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        superuser = await crud.user._create_with_password(db=db, obj_in=user_create)

    await _initialize_project_specific_data(db=db)
