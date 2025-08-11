"""
Database connection and session management for the Philanthropic Ideas Generator.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
from typing import Generator

from config.settings import settings
from storage.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database engine and session factory."""
        try:
            # Create engine
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite configuration for development
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False  # Set to True for SQL debugging
                )
            else:
                # PostgreSQL configuration for production
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get a database session directly (caller must manage cleanup)."""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Session:
    """Dependency function for FastAPI to get database session."""
    return db_manager.get_session_direct()


def init_database():
    """Initialize the database (create tables, etc.)."""
    db_manager.create_tables()
    return db_manager.test_connection()


def cleanup_database():
    """Clean up database connections."""
    if db_manager.engine:
        db_manager.engine.dispose()
        logger.info("Database connections cleaned up")
