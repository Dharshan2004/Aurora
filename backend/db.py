"""
Database configuration with MySQL SSL support for Aiven deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Ensure PyMySQL is used as MySQLdb
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Read environment variables - AURORA_DB_URL is required
AURORA_DB_URL = os.getenv("AURORA_DB_URL")
if not AURORA_DB_URL:
    raise ValueError(
        "AURORA_DB_URL environment variable is required. "
        "Please set it to your MySQL connection string (e.g., mysql+pymysql://user:pass@host:port/db)"
    )

MYSQL_SSL_CA_PATH = os.getenv("MYSQL_SSL_CA_PATH", "/app/ca.pem")

def create_aurora_engine():
    """
    Create SQLAlchemy engine with SSL support and conservative pool settings for free tiers.
    """
    print(f"Creating database engine with URL: {AURORA_DB_URL[:50]}...")
    print(f"SSL CA path: {MYSQL_SSL_CA_PATH}")
    print(f"SSL CA exists: {os.path.exists(MYSQL_SSL_CA_PATH)}")
    
    # Verify MySQL dialect
    if not AURORA_DB_URL.startswith("mysql"):
        from urllib.parse import urlparse
        parsed = urlparse(AURORA_DB_URL)
        host_port = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
        raise ValueError(
            f"Database dialect must be MySQL, but got: {parsed.scheme} "
            f"(host: {host_port}). Please set AURORA_DB_URL to a MySQL connection string "
            f"in your Hugging Face Space environment variables."
        )
    
    # Ensure we're using PyMySQL dialect and clean the URL
    db_url = AURORA_DB_URL
    if db_url.startswith("mysql://") and not db_url.startswith("mysql+pymysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
        print(f"Converted URL to PyMySQL format: {db_url[:50]}...")
    
    # Remove any existing SSL parameters from URL to avoid conflicts
    from urllib.parse import urlparse, urlunparse, parse_qs
    parsed = urlparse(db_url)
    query_params = parse_qs(parsed.query)
    
    # Remove SSL-related parameters from URL
    ssl_params_to_remove = ['ssl-mode', 'ssl_ca', 'ssl_verify_cert', 'ssl_verify_identity', 'ssl_disabled']
    for param in ssl_params_to_remove:
        query_params.pop(param, None)
    
    # Rebuild URL without SSL parameters
    clean_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, parsed.fragment))
    
    if clean_url != db_url:
        print(f"Cleaned URL: {clean_url[:50]}...")
        db_url = clean_url
    
    # SSL configuration for PyMySQL
    ssl_args = {}
    if "mysql+pymysql" in db_url and os.path.exists(MYSQL_SSL_CA_PATH):
        ssl_args = {
            "ssl_ca": MYSQL_SSL_CA_PATH,
            "ssl_verify_cert": True,
            "ssl_verify_identity": False
        }
        print(f"SSL configuration: {ssl_args}")
    else:
        print("No SSL configuration applied")
    
    # Create engine with conservative pool settings for free tiers
    try:
        engine = create_engine(
            db_url,
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
        print("Database engine created successfully")
        # Log dialect information
        dialect_name = engine.dialect.name
        print(f"✅ Database dialect: {dialect_name}")
        return engine
    except Exception as e:
        print(f"Error creating database engine with SSL: {e}")
        # Fallback: try without SSL
        print("Attempting fallback without SSL...")
        try:
            fallback_engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=2,
                max_overflow=3,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_timeout=30,
                future=True,
                echo=False
            )
            print("Fallback engine created successfully")
            # Log dialect information
            dialect_name = fallback_engine.dialect.name
            print(f"✅ Database dialect: {dialect_name}")
            return fallback_engine
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            # Last resort: try with minimal configuration
            print("Attempting minimal configuration...")
            minimal_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                future=True,
                echo=False
            )
            print("Minimal engine created")
            # Log dialect information
            dialect_name = minimal_engine.dialect.name
            print(f"✅ Database dialect: {dialect_name}")
            return minimal_engine

# Lazy-loaded engine and session factory
_engine = None
Base = declarative_base()

def get_engine():
    """Get or create the database engine with fallback handling."""
    global _engine
    if _engine is None:
        _engine = create_aurora_engine()
    return _engine

def get_session_local():
    """Get or create the session factory."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)

# For backward compatibility
SessionLocal = get_session_local()
engine = get_engine()

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
    Initialize database tables. Gracefully handles read-only databases.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        error_msg = str(e).lower()
        if "readonly" in error_msg or "read-only" in error_msg or "permission denied" in error_msg:
            print("⚠️  Database is read-only - skipping table creation")
            print("   This is normal for cloud database services with restricted access")
        else:
            print(f"❌ Database initialization failed: {e}")
            raise

# For backward compatibility - export the engine and SessionLocal
__all__ = ["engine", "SessionLocal", "Base", "get_db_session", "init_database"]