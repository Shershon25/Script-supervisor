import logging
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql.base import PGDialect
from app.config import settings

logger = logging.getLogger("script_supervisor.db")

# Patch SQLAlchemy PostgreSQL dialect to handle CockroachDB version strings
_orig_get_server_version_info = PGDialect._get_server_version_info

def _patched_get_server_version_info(self, connection):
    try:
        return _orig_get_server_version_info(self, connection)
    except Exception:
        # CockroachDB returns version strings like 'CockroachDB CCL v26.3.0...'
        # Default to PostgreSQL 14.0 compatibility version tuple
        return (14, 0, 0)

PGDialect._get_server_version_info = _patched_get_server_version_info

Base = declarative_base()

def get_engine(db_url: str):
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False, "timeout": 30}
    return create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)

# Define absolute path for SQLite fallback so all CWDs point to the exact same file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FALLBACK_SQLITE_PATH = ROOT_DIR / "script_supervisor.db"
FALLBACK_SQLITE_URL = f"sqlite:///{FALLBACK_SQLITE_PATH.as_posix()}"

def auto_create_postgres_db(db_url: str):
    """Attempts to auto-create CockroachDB/PostgreSQL database using psycopg2."""
    if psycopg2 is None:
        return
    if ("postgresql" in db_url or "postgres" in db_url) and "script_supervisor" in db_url:
        try:
            # Replace database target with defaultdb or postgres
            base_url = db_url.replace("/script_supervisor", "/defaultdb")
            if "?" in base_url:
                conn_str = base_url.split("?")[0]
            else:
                conn_str = base_url

            # Direct psycopg2 autocommit connection
            conn = psycopg2.connect(conn_str)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("CREATE DATABASE IF NOT EXISTS script_supervisor;")
            conn.close()
            logger.info("Successfully created CockroachDB database 'script_supervisor'.")
        except Exception as err:
            logger.warning(f"CockroachDB auto-creation attempt notice: {err}")

try:
    auto_create_postgres_db(settings.DATABASE_URL)
    engine = get_engine(settings.DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        logger.info(f"Database connected using CockroachDB/PostgreSQL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
except Exception as e:
    logger.warning(f"Could not connect to configured DATABASE_URL ({settings.DATABASE_URL}): {e}. Falling back to SQLite at {FALLBACK_SQLITE_PATH}.")
    engine = get_engine(FALLBACK_SQLITE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
