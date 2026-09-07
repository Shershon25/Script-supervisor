import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

# Create isolated in-memory SQLite database for test suite execution
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

import app.db.database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db

from app.services.rate_limiter import limiter

@pytest.fixture(autouse=True, scope="session")
def setup_db():
    """Ensure database tables are created once before test suite runs."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter counts between tests."""
    limiter.reset_all()
    yield
    limiter.reset_all()

from app.db.models import User
from app.core.security import hash_password, create_access_token

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    u = db_session.query(User).filter(User.username == "testuser").first()
    if not u:
        u = User(username="testuser", hashed_password=hash_password("testpass123"))
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
    return u

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user.id, "username": test_user.username})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def client(auth_headers):
    with TestClient(app, headers=auth_headers) as c:
        yield c
