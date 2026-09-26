def escape_alembic_url(database_url: str) -> str:
    """Escape percent signs before storing a URL in Alembic's ConfigParser."""

    return database_url.replace("%", "%%")
