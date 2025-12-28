import sys
from pathlib import Path

import pytest

try:
    from jobtracker import db as dbmod
except Exception:
    # If running tests from repo root, ensure repo root is on PYTHONPATH
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from jobtracker import db as dbmod


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Create an in-memory SQLite DB and patch jobtracker.db.SessionLocal to use it.

    This fixture is autouse so tests run against an isolated DB by default.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", future=True)
    # Create tables
    dbmod.Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(dbmod, "SessionLocal", TestSessionLocal)

    yield


@pytest.fixture
def session():
    """Return a fresh SQLAlchemy Session bound to the in-memory DB."""
    sess = dbmod.SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def runner():
    from typer.testing import CliRunner

    return CliRunner()
