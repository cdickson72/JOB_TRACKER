from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from contextlib import contextmanager

APP_DIR = Path.home() / ".jobtracker"
DB_PATH = APP_DIR / "jobtracker.db"

try:
    APP_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # If we cannot create the dir, let the error surface; callers will see clearer exception
    raise

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Yield a database session and ensure it's closed afterwards.

    Use as: with get_db() as db: ...
    Commits/rollbacks should be handled by callers where appropriate.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
