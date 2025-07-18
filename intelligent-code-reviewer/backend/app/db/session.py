from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager

from ..core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    This function creates a new database session for each request
    and automatically closes it when the request is finished.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session():
    """
    Context manager that provides a database session.
    
    This is used for non-FastAPI code that needs database access.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    
    This function creates all tables defined in the SQLAlchemy models.
    It should be called during application startup.
    """
    # Import both model files to ensure all tables are created
    from ..models.sql_models import Base as SqlBase
    from ..models.analysis import Base as AnalysisBase
    
    # Create tables from both base classes
    SqlBase.metadata.create_all(bind=engine)
    AnalysisBase.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all database tables.
    
    This function drops all tables. Use with caution!
    """
    from ..models.sql_models import Base as SqlBase
    from ..models.analysis import Base as AnalysisBase
    
    SqlBase.metadata.drop_all(bind=engine)
    AnalysisBase.metadata.drop_all(bind=engine) 