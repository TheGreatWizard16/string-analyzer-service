"""
Database setup module.
- Uses SQLModel (built on SQLAlchemy) with SQLite by default.
- You can switch to PostgreSQL by changing DATABASE_URL.
"""

from sqlmodel import SQLModel, create_engine, Session
import os

# Database URL (SQLite by default, can override via environment variable)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./strings.db")

# SQLite requires a special argument for threading; others don't.
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

# Create SQLAlchemy engine
engine = create_engine(DB_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create all database tables."""
    from . import models  # ensures models are imported before creating tables
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new database session."""
    return Session(engine)
