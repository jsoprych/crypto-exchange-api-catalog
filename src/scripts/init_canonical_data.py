#!/usr/bin/env python3
"""
Initialize canonical fields and data types in the database.
Inserts core canonical fields for ticker, order_book, trade, candle data types.
"""

import sqlite3
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def init_canonical_fields(conn):
    """Insert core canonical fields."""
    cursor = conn.cursor()

    # Core ticker fields
    ticker_fields = [
        ('bid_price', 'Bid Price', 'Current best bid price', 'numeric', 'ticker', True, True),
        ('ask_price', 'Ask Price', 'Current best ask price', 'numeric', 'ticker', True, True),
        ('last_price', 'Last Price', 'Price of last trade', 'numeric', 'ticker', True, True),
        ('volume_24h', '24h Volume', '24-hour trading volume', 'numeric', 'ticker', True, True),
        ('high_24h', '24h High', '24-hour highest price', 'numeric', 'ticker', False, True),
        ('low_24h', '24h Low', '24-hour lowest price', 'numeric', 'ticker', False, True),
        ('open_24h', '24h Open', '24-hour opening price', 'numeric', 'ticker', False, True),
        ('volume_30d', '30d Volume', '30-day trading volume', 'numeric', 'ticker', False, False),
        ('best_bid_size', 'Best Bid Size', 'Size at best bid', 'numeric', 'ticker', False, True),
        ('best_ask_size', 'Best Ask Size', 'Size at best ask', 'numeric', 'ticker', False, True),
    ]

    # Core order book fields
    order_book_fields = [
        ('bid_price', 'Bid Price', 'Bid price level', 'numeric', 'order_book', True, True),
        ('bid_size', 'Bid Size', 'Bid size at price level', 'numeric', 'order_book', True, True),
        ('ask_price', 'Ask Price', 'Ask price level', 'numeric', 'order_book', True, True),
        ('ask_size', 'Ask Size', 'Ask size at price level', 'numeric', 'order_book', True, True),
        ('timestamp', 'Timestamp', 'Snapshot/update timestamp', 'datetime', 'order_book', True, True),
    ]

    # Core trade fields
    trade_fields = [
        ('trade_id', 'Trade ID', 'Unique trade identifier', 'string', 'trade', True, True),
        ('price', 'Price', 'Trade price', 'numeric', 'trade', True, True),
        ('size', 'Size', 'Trade size/volume', 'numeric', 'trade', True, True),
        ('side', 'Side', 'Trade side (buy/sell)', 'string', 'trade', True, True),
        ('timestamp', 'Timestamp', 'Trade timestamp', 'datetime', 'trade', True, True),
    ]

    # Core candle/OHLC fields
    candle_fields = [
        ('open', 'Open', 'Opening price', 'numeric', 'candle', True, True),
        ('high', 'High', 'Highest price', 'numeric', 'candle', True, True),
        ('low', 'Low', 'Lowest price', 'numeric', 'candle', True, True),
        ('close', 'Close', 'Closing price', 'numeric', 'candle', True, True),
        ('volume', 'Volume', 'Trading volume', 'numeric', 'candle', True, True),
        ('timestamp', 'Timestamp', 'Candle start time', 'datetime', 'candle', True, True),
        ('interval', 'Interval', 'Candle interval in seconds', 'integer', 'candle', True, True),
    ]

    # Common metadata fields
    common_fields = [
        ('symbol', 'Symbol', 'Trading pair symbol', 'string', 'common', True, True),
        ('timestamp', 'Timestamp', 'Data timestamp', 'datetime', 'common', True, True),
        ('sequence', 'Sequence', 'Message sequence number', 'integer', 'common', False, True),
        ('exchange', 'Exchange', 'Exchange name', 'string', 'common', True, True),
    ]

    all_fields = ticker_fields + order_book_fields + trade_fields + candle_fields + common_fields

    inserted = 0
    for field in all_fields:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO canonical_fields
                (field_name, display_name, description, data_type, category, is_required, is_core_field)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, field)
            inserted += cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error inserting field {field[0]}: {e}")

    logger.info(f"Inserted {inserted} canonical fields")
    return inserted


def init_canonical_data_types(conn):
    """Insert canonical data types and link fields to them."""
    cursor = conn.cursor()

    # Data types
    data_types = [
        ('ticker', 'Ticker', 'Real-time ticker/summary data', False),
        ('order_book', 'Order Book', 'Order book snapshot/update data', True),
        ('trade', 'Trade', 'Individual trade execution data', True),
        ('candle', 'Candle/OHLC', 'OHLC candle data', True),
    ]

    inserted_types = 0
    data_type_ids = {}

    for data_type_name, display_name, description, is_array_type in data_types:
        cursor.execute("""
            INSERT OR IGNORE INTO canonical_data_types
            (data_type_name, display_name, description, is_array_type)
            VALUES (?, ?, ?, ?)
        """, (data_type_name, display_name, description, is_array_type))

        if cursor.rowcount > 0:
            inserted_types += 1

        # Get the data_type_id
        cursor.execute("SELECT data_type_id FROM canonical_data_types WHERE data_type_name = ?", (data_type_name,))
        row = cursor.fetchone()
        if row:
            data_type_ids[data_type_name] = row[0]

    logger.info(f"Inserted {inserted_types} canonical data types")

    # Link fields to data types
    # Define which fields belong to which data types and whether they're required
    field_mappings = {
        'ticker': [
            ('bid_price', True),
            ('ask_price', True),
            ('last_price', True),
            ('volume_24h', True),
            ('high_24h', False),
            ('low_24h', False),
            ('open_24h', False),
            ('volume_30d', False),
            ('best_bid_size', False),
            ('best_ask_size', False),
            ('symbol', True),
            ('timestamp', True),
            ('exchange', True),
        ],
        'order_book': [
            ('bid_price', True),
            ('bid_size', True),
            ('ask_price', True),
            ('ask_size', True),
            ('timestamp', True),
            ('symbol', True),
            ('exchange', True),
        ],
        'trade': [
            ('trade_id', True),
            ('price', True),
            ('size', True),
            ('side', True),
            ('timestamp', True),
            ('symbol', True),
            ('exchange', True),
        ],
        'candle': [
            ('open', True),
            ('high', True),
            ('low', True),
            ('close', True),
            ('volume', True),
            ('timestamp', True),
            ('interval', True),
            ('symbol', True),
            ('exchange', True),
        ],
    }

    inserted_mappings = 0
    for data_type_name, fields in field_mappings.items():
        data_type_id = data_type_ids.get(data_type_name)
        if not data_type_id:
            logger.warning(f"Data type {data_type_name} not found, skipping field mappings")
            continue

        for field_order, (field_name, is_required) in enumerate(fields):
            # Get field_id
            cursor.execute("SELECT canonical_field_id FROM canonical_fields WHERE field_name = ?", (field_name,))
            field_row = cursor.fetchone()
            if not field_row:
                logger.warning(f"Field {field_name} not found, skipping")
                continue

            field_id = field_row[0]

            # Insert mapping
            cursor.execute("""
                INSERT OR IGNORE INTO data_type_fields
                (data_type_id, canonical_field_id, is_required, field_order)
                VALUES (?, ?, ?, ?)
            """, (data_type_id, field_id, is_required, field_order))

            if cursor.rowcount > 0:
                inserted_mappings += 1

    logger.info(f"Inserted {inserted_mappings} data type field mappings")
    return inserted_types, inserted_mappings


def main():
    """Main entry point."""
    db_path = DATABASE_PATH

    if not db_path.exists():
        logger.error(f"Database not found at {db_path}. Please run 'python main.py init' first.")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        logger.info("Initializing canonical data...")

        # Insert canonical fields
        fields_inserted = init_canonical_fields(conn)

        # Insert canonical data types and mappings
        types_inserted, mappings_inserted = init_canonical_data_types(conn)

        conn.commit()

        print(f"\n✓ Canonical data initialization complete:")
        print(f"  - Canonical fields: {fields_inserted}")
        print(f"  - Data types: {types_inserted}")
        print(f"  - Field mappings: {mappings_inserted}")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
