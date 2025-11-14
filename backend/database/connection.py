"""
Database connection setup for player props ML system
Uses SQLite for local development, PostgreSQL for production
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database configuration
DATABASE_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite or postgresql

if DATABASE_TYPE == "sqlite":
    # Local development - SQLite database
    DATABASE_URL = "sqlite:///backend/data/player_props.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # Production - PostgreSQL
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/player_props"
    )
    engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db_session():
    """
    Get database session
    Usage:
        db = get_db_session()
        try:
            # ... database operations
            db.commit()
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def init_database():
    """
    Initialize database - create all tables
    Run this once to set up the database schema
    """
    try:
        from database.models import (
            PlayerPropsLine,
            PlayerPropsResult,
            PlayerPropsPrediction,
            PlayerStatsCache
        )
    except ImportError:
        # Fallback for different import contexts
        from backend.database.models import (
            PlayerPropsLine,
            PlayerPropsResult,
            PlayerPropsPrediction,
            PlayerStatsCache
        )

    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at {DATABASE_URL}")
    print(f"✓ Tables created: player_props_lines, player_props_results, player_props_predictions, player_stats_cache")


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
