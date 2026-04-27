"""Database configuration module (PostgreSQL only)."""
import os
from typing import List, Dict


DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URI")


DB_CONFIG = {
    "engine": "postgresql",
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "intelligrocery"),
    "password": os.getenv("DB_PASSWORD", "IntelliGrocery@2010"),
    "database": os.getenv("DB_NAME", "intelligrocery"),
}

DB_CONNECTION_STRING = DATABASE_URL or (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)


def _candidate_db_configs() -> List[Dict[str, object]]:
    """Return connection profiles ordered by preference."""
    host = DB_CONFIG["host"]
    port = DB_CONFIG["port"]

    candidates = [
        # 1) Current environment/default config
        DB_CONFIG,
        # 2) Docker compose profile used in this project
        {
            "engine": "postgresql",
            "host": host,
            "port": port,
            "user": "intelligrocery",
            "password": "IntelliGrocery@2010",
            "database": "intelligrocery",
        },
        # 3) Legacy local profile found in .env.example
        {
            "engine": "postgresql",
            "host": host,
            "port": port,
            "user": "postgres",
            "password": "ravikiran",
            "database": "intelligrocery_db",
        },
        {
            "engine": "postgresql",
            "host": host,
            "port": port,
            "user": "postgres",
            "password": "ravikiran",
            "database": "postgres",
        },
        # 4) Very common local postgres fallback
        {
            "engine": "postgresql",
            "host": host,
            "port": port,
            "user": "postgres",
            "password": "postgres",
            "database": "postgres",
        },
    ]

    # Deduplicate exact repeated profiles while preserving order.
    unique = []
    seen = set()
    for cfg in candidates:
        key = (cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["database"])
        if key not in seen:
            seen.add(key)
            unique.append(cfg)
    return unique


def get_db_connection():
    """Get a PostgreSQL connection.

    Tries the configured profile first, then known project fallback profiles.
    """
    import psycopg2

    last_err = None

    if DATABASE_URL:
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as exc:
            last_err = exc

    for cfg in _candidate_db_configs():
        try:
            return psycopg2.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
            )
        except Exception as exc:
            last_err = exc

    raise RuntimeError(
        "Unable to connect to PostgreSQL with configured or fallback profiles. "
        "On Render, add a PostgreSQL database service and set DATABASE_URL, or set "
        "DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME in your environment. "
        f"Last error: {last_err}"
    )


def get_db_type() -> str:
    """Get current database type."""
    return "postgres"
