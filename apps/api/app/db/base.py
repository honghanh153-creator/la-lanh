from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for production database models."""


# Import model modules so Alembic sees their metadata.
from app.domains.birth import tables as birth_tables  # noqa: E402,F401
from app.domains.guest import tables as guest_tables  # noqa: E402,F401
