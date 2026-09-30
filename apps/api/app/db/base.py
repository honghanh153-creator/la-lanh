from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for production database models."""


# Import model modules so Alembic sees their metadata.
from app.domains.birth import tables as birth_tables  # noqa: E402,F401
from app.domains.content import tables as content_tables  # noqa: E402,F401
from app.domains.experiments import tables as experiment_tables  # noqa: E402,F401
from app.domains.guest import tables as guest_tables  # noqa: E402,F401
from app.domains.identity import tables as identity_tables  # noqa: E402,F401
from app.domains.la_chung import tables as la_chung_tables  # noqa: E402,F401
from app.domains.matching import tables as matching_tables  # noqa: E402,F401
from app.domains.radar import tables as radar_tables  # noqa: E402,F401
from app.domains.readings import tables as reading_tables  # noqa: E402,F401
from app.domains.resonance import tables as resonance_tables  # noqa: E402,F401
from app.domains.saved import tables as saved_tables  # noqa: E402,F401
from app.domains.share import tables as share_tables  # noqa: E402,F401
from app.domains.tarot import tables as tarot_tables  # noqa: E402,F401
