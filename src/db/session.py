from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


# Database URL: Adjust as needed for your environment
DATABASE_URL = "postgresql://username:password@localhost/options_db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# SessionLocal: A factory for creating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


@contextmanager
def get_db():
    """Provide a transactional scope for database operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
