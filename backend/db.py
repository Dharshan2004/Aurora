"""
Database configuration with MySQL SSL support for Aiven deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Read environment variables
AURORA_DB_URL = os.getenv("AURORA_DB_URL", "mysql+pymysql://aurora_user:aurora_pass@localhost:3306/aurora_db?charset=utf8mb4")
MYSQL_SSL_CA_PATH = os.getenv("MYSQL_SSL_CA_PATH", "/app/ca.pem")

def create_aurora_engine():
    """
    Create SQLAlchemy engine with SSL support and conservative pool settings for free tiers.
    """
    # SSL configuration for PyMySQL
    ssl_args = {}
    if "mysql+pymysql" in AURORA_DB_URL and os.path.exists(MYSQL_SSL_CA_PATH):
        ssl_args = {
            "ssl_ca": MYSQL_SSL_CA_PATH,
            "ssl_verify_cert": True,
            "ssl_verify_identity": False  # Set to True for stricter security if needed
        }
    
    # Create engine with conservative pool settings for free tiers
    engine = create_engine(
        AURORA_DB_URL,
        # Conservative pool settings for free tiers
        poolclass=QueuePool,
        pool_size=2,  # Small pool size for free tier
        max_overflow=3,  # Limited overflow
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=1800,  # Recycle connections every 30 minutes
        pool_timeout=30,  # Timeout for getting connection from pool
        # SSL configuration
        connect_args=ssl_args,
        # Additional settings
        future=True,
        echo=False  # Set to True for debugging
    )
    
    return engine

# Create the engine and session factory
engine = create_aurora_engine()
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db_session():
    """
    Dependency function to get database session.
    Use this in FastAPI dependencies.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """
    Initialize database tables.
    """
    Base.metadata.create_all(bind=engine)

# For backward compatibility - export the engine and SessionLocal
__all__ = ["engine", "SessionLocal", "Base", "get_db_session", "init_database"]
