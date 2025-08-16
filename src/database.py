from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuration for the database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./library_demo.db"  # Example for SQLite, update for your database

# Engine configuration
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


# Dependency for FastAPI
def get_db():
    db = SessionLocal()  # Create a session using the session_maker
    try:
        yield db  # Yield the session for use in the route
    finally:
        db.close()  # Close the session after use


# Optional: Context manager for standalone scripts or testing
@contextmanager
def get_session():
    """Context manager for database sessions outside FastAPI (e.g., scripts/tests)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()
