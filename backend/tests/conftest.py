# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import hash_password
from app.database import SessionLocal
from app.dependencies import get_db
from app.main import app
from app.models import Admin, Base

from sqlalchemy.pool import StaticPool
from app.main import limiter as main_limiter
from app.routers.inscricao import limiter as inscricao_limiter

# Desativa o rate limit durante os testes
main_limiter.enabled = False
inscricao_limiter.enabled = False

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function", autouse=False)
def db():
    """Cria tabelas em memória e retorna sessão limpa por teste."""
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db):
    """TestClient do FastAPI usando o banco de testes."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db, client):
    """Cria um admin e retorna o JWT."""
    admin = Admin(username="testadmin", password_hash=hash_password("secret"))
    db.add(admin)
    db.commit()

    resp = client.post("/api/admin/login", data={"username": "testadmin", "password": "secret"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
