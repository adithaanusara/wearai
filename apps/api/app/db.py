from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""


# connect_timeout: when the database cannot be reached, a request fails after 10 seconds (and the
# health check says so) instead of waiting on the operating system's connect timeout, minutes.
# pool_timeout: a request waiting for a free connection gives up after 10 seconds, not 30.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_timeout=10,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that gives each request its own database session."""
    with SessionLocal() as session:
        yield session
