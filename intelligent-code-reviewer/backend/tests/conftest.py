import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from typing import Generator

from app.models.sql_models import Base
from app.db.session import get_db


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    
    This fixture creates all tables, yields a database session,
    and then cleans up by dropping all tables.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    db = TestSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables to ensure clean state for next test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> TestClient:
    """
    Create a test client with database dependency override.
    
    This fixture overrides the get_db dependency to use the test database.
    """
    # Create a clean FastAPI app for testing without startup events
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.main import router as api_router
    from app.core.config import settings
    
    test_app = FastAPI(
        title=settings.app_name + " (Test)",
        version=settings.app_version,
        debug=settings.debug,
    )
    
    # Add CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    test_app.include_router(api_router)
    
    @test_app.get("/")
    async def root():
        return {"message": "Test API", "status": "healthy"}
    
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "test"}
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def sample_task_id() -> str:
    """Return a sample task ID for testing."""
    return "test-task-12345"


@pytest.fixture
def sample_git_url() -> str:
    """Return a sample Git URL for testing."""
    return "https://github.com/example/test-repo.git"


@pytest.fixture
def sample_report_content() -> dict:
    """Return sample report content for testing."""
    return {
        "summary": "Test analysis completed",
        "findings": [
            {
                "type": "code_smell",
                "severity": "medium",
                "description": "Long method detected",
                "file": "test.py",
                "line": 42
            }
        ],
        "recommendations": [
            "Consider breaking down the long method into smaller functions"
        ]
    } 