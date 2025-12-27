"""Database setup and session management for the hospital system."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import shutil
import warnings

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.engine import make_url

from .exceptions import DatabaseConnectionError


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _load_env_file() -> None:
    """Load a local .env file without overriding existing environment variables."""
    env_locations = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for env_path in env_locations:
        if not env_path.exists():
            continue
        try:
            lines = env_path.read_text().splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        break


_load_env_file()


def _resolve_default_db_url() -> str:
    env_url = os.environ.get("HOSPITAL_DB_URL")
    if env_url:
        return env_url
    default_path = Path.cwd() / "data" / "hospital.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_path}"


def _ensure_writable_sqlite_url(url: str) -> str:
    """Ensure the SQLite file is writable; if not, fall back to a user-local copy."""
    parsed = make_url(url)
    if parsed.drivername != "sqlite":
        return url

    db_path = Path(parsed.database or "hospital.db")
    target_path = db_path

    def is_writable(path: Path) -> bool:
        return os.access(path if path.exists() else path.parent, os.W_OK)

    if not is_writable(db_path):
        fallback_dir = Path.home() / ".hospital_system"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        target_path = fallback_dir / db_path.name
        if db_path.exists():
            try:
                shutil.copy2(db_path, target_path)
            except Exception:
                # If copy fails, continue with empty file
                pass
        warnings.warn(
            f"Database path {db_path} not writable; using fallback {target_path}",
            RuntimeWarning,
            stacklevel=2,
        )
    return f"sqlite:///{target_path}"


def create_sqlite_engine(database_url: str | None = None):
    """Create a SQLite engine and verify the connection."""
    raw_url = database_url or _resolve_default_db_url()
    db_url = _ensure_writable_sqlite_url(raw_url)
    try:
        engine = create_engine(db_url, echo=False, future=True)
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
