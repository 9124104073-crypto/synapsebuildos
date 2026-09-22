from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

_url = settings().database_url
# Hosts hand out postgres:// URLs; SQLAlchemy 2 wants the driver named.
if _url.startswith("postgres://"):
    _url = "postgresql+psycopg://" + _url.split("://", 1)[1]
elif _url.startswith("postgresql://"):
    _url = "postgresql+psycopg://" + _url.split("://", 1)[1]
_engine = create_engine(
    _url,
    echo=False,
    future=True,
    # SQLite only: FastAPI serves requests on a threadpool, and the default
    # same-thread check rejects that.
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    from . import models  # noqa: F401  — register mappers before create_all

    Base.metadata.create_all(_engine)
