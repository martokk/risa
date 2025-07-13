from sqlmodel import Session, select

from vcore.backend import models
from vcore.backend.core import security

from .base import BaseCRUD


class UserCRUD(BaseCRUD[models.User, models.UserCreate, models.UserUpdate]):
    async def _create_with_password(
        self, db: Session, *, obj_in: models.UserCreateWithPassword
    ) -> models.User:
        """
        Create a new user by generating a hashed password from the provided password.

        Args:
            db (Session): The database session.
            obj_in (models.UserCreateWithPassword): The user to create.

        Returns:
            models.User: The created user.
        """
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        obj_in_data["hashed_password"] = security.get_password_hash(obj_in_data["password"])
        del obj_in_data["password"]

        out_obj = models.UserCreate(**obj_in_data)
        return await self.create(db, obj_in=out_obj)

    async def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> models.User | None:
        """
        Authenticate a user by checking the provided password against the hashed password.

        Args:
            db (Session): The database session.
            username (str): The username to authenticate.
            password (str): The password to authenticate.

        Returns:
            models.User | None: The authenticated user or None if the user does not exist or
                the password is incorrect.
        """
        _user = await self.get_or_none(db, username=username)
        if not _user:
            return None
        if not security.verify_password(
            plain_password=password, hashed_password=_user.hashed_password
        ):
            return None
        return _user

    def is_active(self, _user: models.User) -> bool:
        return _user.is_active

    def is_superuser(self, *, user_: models.User) -> bool:
        return user_.is_superuser

    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        return security.get_password_hash(password)

    async def get_non_superusers(self, db: Session) -> list[models.User]:
        """Get all non-superuser users."""
        return list(
            db.exec(
                select(models.User).where(models.User.is_superuser == False)  # noqa: E712
            ).all()
        )


user = UserCRUD(model=models.User)
