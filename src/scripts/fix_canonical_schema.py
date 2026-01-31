#!/usr/bin/env python3
"""
Fix canonical schema by dropping and recreating tables with correct data types.
This script addresses the issue where 'decimal' in CHECK constraint conflicts
with 'numeric' values being inserted.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def drop_canonical_tables(conn):
    """Drop all canonical mapping tables and views."""
    cursor = conn.cursor()

    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Drop views first (depend on tables)
    cursor.execute("DROP VIEW IF EXISTS vendor_coverage_view")
    cursor.execute("DROP VIEW IF EXISTS vendor_mappings_view")

    # Drop tables in reverse dependency order
    cursor.execute("DROP TABLE IF EXISTS mapping_validation")
    cursor.execute("DROP TABLE IF EXISTS data_type_fields")
    cursor.execute("DROP TABLE IF EXISTS field_mappings")
    cursor.execute("DROP TABLE IF EXISTS canonical_data_types")
    cursor.execute("DROP TABLE IF EXISTS canonical_fields")

    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    logger.info("Dropped canonical tables and views")


def recreate_schema_from_file(conn):
    """Recreate schema from mapping_schema.sql file."""
    mapping_schema_path = project_root / "sql" / "mapping_schema.sql"

    if not mapping_schema_path.exists():
        logger.error(f"Mapping schema file not found: {mapping_schema_path}")
        return False

    with open(mapping_schema_path, 'r') as f:
        schema_sql = f.read()

    # Execute the schema SQL
    conn.executescript(schema_sql)
    logger.info(f"Recreated schema from {mapping_schema_path}")
    return True


def main():
    """Main entry point."""
    db_path = DATABASE_PATH

    if not db_path.exists():
        logger.error(f"Database not found at {db_path}. Please run 'python main.py init' first.")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    try:
        logger.info("Starting canonical schema fix...")

        # Step 1: Drop existing tables
        drop_canonical_tables(conn)

        # Step 2: Recreate schema from file
        if not recreate_schema_from_file(conn):
            sys.exit(1)

        conn.commit()

        print(f"\n✓ Canonical schema fix complete")
        print(f"  - Tables dropped and recreated")
        print(f"  - Schema updated with correct data types")

        # Step 3: Import the init script to insert data
        print(f"\nNow run 'python3 src/scripts/init_canonical_data.py' to insert canonical fields.")

    except Exception as e:
        logger.error(f"Schema fix failed: {e}")
        conn.rollback()
        print(f"\n✗ Schema fix failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
