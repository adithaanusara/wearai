from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine

import app.models  # noqa: F401
from app.db import Base


def test_models_and_migrations_are_in_sync(engine: Engine) -> None:
    """Fails when a model changes without a matching Alembic migration."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, Base.metadata) == []
