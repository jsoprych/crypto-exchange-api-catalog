# src/database/db_manager.py
"""
Database connection and initialization management.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from config.settings import DATABASE_PATH, PROJECT_ROOT
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and initialization.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file (defaults to config setting)
        """
        self.db_path = db_path or DATABASE_PATH
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection with proper configuration.

        Returns:
            SQLite connection object
        """
        if self.conn is None:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect with row factory for dict-like access
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Connected to database: {self.db_path}")

        return self.conn

    def initialize_schema(self):
        """
        Initialize database schema from SQL files.
        Creates tables, indexes, and views.
        """
        conn = self.connect()

        # Load and execute schema
        schema_path = PROJECT_ROOT / "sql" / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            conn.executescript(schema_sql)
            logger.info("Database schema initialized")
        else:
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        # Load and execute views
        views_path = PROJECT_ROOT / "sql" / "views" / "common_views.sql"
        if views_path.exists():
            with open(views_path, 'r') as f:
                views_sql = f.read()

            conn.executescript(views_sql)
            logger.info("Database views created")

        # Load and execute mapping schema
        mapping_schema_path = PROJECT_ROOT / "sql" / "mapping_schema.sql"
        if mapping_schema_path.exists():
            with open(mapping_schema_path, 'r') as f:
                mapping_schema_sql = f.read()

            conn.executescript(mapping_schema_sql)
            logger.info("Mapping schema initialized")

        conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            if self.conn:
                self.conn.rollback()
        self.close()
