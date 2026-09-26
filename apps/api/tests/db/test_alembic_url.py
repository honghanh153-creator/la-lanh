from alembic.config import Config
from sqlalchemy.engine import make_url

from app.db.alembic import escape_alembic_url


def test_percent_encoded_password_survives_alembic_config_interpolation() -> None:
    database_url = (
        "postgresql+asyncpg://postgres.example:%40strong%25password"
        "@pooler.example.com:5432/postgres?ssl=require"
    )
    config = Config()

    config.set_main_option("sqlalchemy.url", escape_alembic_url(database_url))

    configured_url = config.get_main_option("sqlalchemy.url")
    assert configured_url == database_url
    assert make_url(configured_url).password == "@strong%password"  # noqa: S105
