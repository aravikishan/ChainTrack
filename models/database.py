"""SQLite database setup using SQLAlchemy."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def _build_url() -> str:
    """Return the database URL, creating the instance directory if needed."""
    url = config.SQLALCHEMY_DATABASE_URI
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "")
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    return url


engine = create_engine(
    _build_url(),
    connect_args={"check_same_thread": False},
    echo=config.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables that do not yet exist."""
    from models.schemas import Product, ChainBlock, Shipment, Location  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
