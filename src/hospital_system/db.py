"""Database setup and session management for the hospital system."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .exceptions import DatabaseConnectionError


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def create_sqlite_engine(database_url: str = "sqlite:///./hospital.db"):
    """Create a SQLite engine and verify the connection."""
    try:
        engine = create_engine(database_url, echo=False, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError("Failed to connect to the database.") from exc


engine = create_sqlite_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
