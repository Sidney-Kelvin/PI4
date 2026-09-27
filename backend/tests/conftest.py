import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from tests import rossmann_sintetico

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Nos testes (SQLite) a estrutura vem direto dos modelos; em execução real, do Alembic.
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def pasta_csv_sintetico(tmp_path_factory):
    """CSVs artificiais no formato do Rossmann (somente para testes)."""
    return rossmann_sintetico.gerar(tmp_path_factory.mktemp("rossmann") / "raw")


@pytest.fixture(scope="session")
def dados_varejo(pasta_csv_sintetico):
    """Importa os CSVs sintéticos no banco de testes uma única vez."""
    from app.ml.ingest import importar

    return importar(engine_test, pasta_csv_sintetico.parent)
