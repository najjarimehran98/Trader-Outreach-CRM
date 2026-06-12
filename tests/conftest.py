import pytest
import tempfile
import os
import sys
from pathlib import Path

# Ensure project root is on Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True, scope="session")
def test_db():
    """Create a temporary database for all tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    import database
    database.DB_PATH = db_path
    import main
    main.DB_PATH = db_path
    yield db_path
    db_path.unlink(missing_ok=True)


@pytest.fixture
def client(test_db):
    """Create a test client with fresh database state."""
    import sqlite3
    from fastapi.testclient import TestClient
    from main import app

    # Create tables by hitting the app once
    with TestClient(app) as c:
        # Clear data between tests (tables now exist from lifespan)
        conn = sqlite3.connect(str(test_db))
        conn.execute("DELETE FROM outreach_logs")
        conn.execute("DELETE FROM traders")
        conn.commit()
        conn.close()
        yield c
