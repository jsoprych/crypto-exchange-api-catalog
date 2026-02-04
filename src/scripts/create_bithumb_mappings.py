#!/usr/bin/env python3
"""
Create Bithumb WebSocket ticker field mappings to canonical fields.
Maps Bithumb-specific field names to industry-standard canonical field names.
"""

import argparse
import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class BithumbTickerMapper:
    """
    Maps Bithumb WebSocket ticker fields to canonical fields.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.exchange_name = "bithumb"

    def connect(self):
        """Establish database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Database connection closed")

    def get_vendor_id(self) -> Optional[int]:
        """
        Get vendor ID for Bithumb.

        Returns:
            Vendor ID or None if not found
        """
        self.connect()
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            ("bithumb",)
        )
        result = cursor.fetchone()
        return result["vendor_id"] if result else None

    def get_websocket_channels(self, vendor_id: int) -> List[Dict]:
        """
        Get WebSocket channels for Bithumb.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of channel dictionaries
        """
        cursor = self.conn.execute(
            """
            SELECT channel_id, channel_name, message_schema
            FROM websocket_channels
            WHERE vendor_id = ? AND channel_name LIKE '%ticker%'
            """,
            (vendor_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def extract_fields_from_schema(self, message_schema: str) -> List[str]:
        """
        Extract field names from message schema JSON.

        Args:
            message_schema: JSON string of message schema

        Returns:
            List of field paths
        """
        try:
            schema = json.loads(message_schema)
            # TODO: Implement schema traversal to extract field paths
            # This depends on the actual Bithumb WebSocket message format
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message schema: {e}")
            return []

    def propose_mappings(self, vendor_id: int) -> List[Tuple[str, str, str]]:
        """
        Propose field mappings for Bithumb.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of (vendor_field_path, canonical_field_id, transformation) tuples
        """
        # Based on Bithumb WebSocket ticker API documentation
        # Field paths are root-level in the ticker message JSON
        # Mapped to existing canonical fields
        proposed_mappings = [
            # Symbol field
            ("code", "symbol", '{"type": "identity"}'),

            # Price fields
            ("trade_price", "last_price", '{"type": "string_to_numeric"}'),
            ("high_price", "high_24h", '{"type": "string_to_numeric"}'),
            ("low_price", "low_24h", '{"type": "string_to_numeric"}'),
            ("opening_price", "open_24h", '{"type": "string_to_numeric"}'),
            ("prev_closing_price", "close", '{"type": "string_to_numeric"}'),

            # Volume fields
            ("trade_volume", "volume_24h", '{"type": "string_to_numeric"}'),
            ("acc_trade_volume", "volume_24h", '{"type": "string_to_numeric"}'),
            ("acc_trade_volume_24h", "volume_24h", '{"type": "string_to_numeric"}'),

            # Timestamp fields
            ("timestamp", "timestamp", '{"type": "ms_to_datetime"}'),
            ("trade_timestamp", "timestamp", '{"type": "ms_to_datetime"}'),

            # Trade side (ASK/BID to sell/buy) - use identity for now
            ("ask_bid", "side", '{"type": "identity"}'),

            # Market state - no direct canonical equivalents, map to status-like fields
            # ("market_state", "symbol_status", '{"type": "identity"}'),  # No canonical field
            # ("is_trading_suspended", "symbol_status", '{"type": "identity"}'),  # No canonical field

            # 52-week high/low - no direct canonical equivalents
            # ("highest_52_week_price", "high_52w", '{"type": "string_to_numeric"}'),  # No canonical field
            # ("lowest_52_week_price", "low_52w", '{"type": "string_to_numeric"}'),  # No canonical field

            # Accumulated trade values - no direct canonical equivalents
            # ("acc_trade_price", "quote_volume_24h", '{"type": "string_to_numeric"}'),  # No canonical field
            # ("acc_trade_price_24h", "quote_volume_24h", '{"type": "string_to_numeric"}'),  # No canonical field
        ]
        return proposed_mappings

    def get_canonical_field_id(self, field_name: str) -> Optional[int]:
        """
        Get canonical field ID by field name.

        Args:
            field_name: Canonical field name

        Returns:
            Canonical field ID or None if not found
        """
        cursor = self.conn.execute(
            "SELECT canonical_field_id FROM canonical_fields WHERE field_name = ?",
            (field_name,)
        )
        result = cursor.fetchone()
        return result["canonical_field_id"] if result else None

    def create_mappings(self, dry_run: bool = True):
        """
        Create field mappings in database.

        Args:
            dry_run: If True, only show proposed mappings without saving
        """
        vendor_id = self.get_vendor_id()
        if not vendor_id:
            logger.error(f"Vendor 'bithumb' not found in database")
            return

        logger.info(f"Creating mappings for Bithumb (vendor_id: {vendor_id})")

        # Get WebSocket channels - specifically ticker channel
        channels = self.get_websocket_channels(vendor_id)
        if not channels:
            logger.warning(f"No WebSocket channels found for Bithumb")
            return

        # Get ticker channel ID (assume first ticker channel)
        ticker_channel_id = None
        for channel in channels:
            if 'ticker' in channel['channel_name'].lower():
                ticker_channel_id = channel['channel_id']
                break

        if not ticker_channel_id:
            logger.warning("No ticker channel found for Bithumb")
            return

        # Propose mappings
        proposed_mappings = self.propose_mappings(vendor_id)

        if dry_run:
            logger.info("DRY RUN - Proposed mappings (not saved):")
            for vendor_field, canonical_field, transform in proposed_mappings:
                canonical_id = self.get_canonical_field_id(canonical_field)
                if canonical_id:
                    logger.info(f"  {vendor_field} -> {canonical_field} (id: {canonical_id}, transform: {transform})")
                else:
                    logger.warning(f"  {vendor_field} -> {canonical_field} (CANONICAL FIELD NOT FOUND, transform: {transform})")
            return

        # Create actual mappings
        created_count = 0
        for vendor_field, canonical_field, transform in proposed_mappings:
            try:
                canonical_id = self.get_canonical_field_id(canonical_field)
                if not canonical_id:
                    logger.warning(f"Canonical field '{canonical_field}' not found, skipping mapping for {vendor_field}")
                    continue

                # Check if mapping already exists
                cursor = self.conn.execute(
                    """
                    SELECT mapping_id FROM field_mappings
                    WHERE vendor_id = ? AND vendor_field_path = ? AND canonical_field_id = ?
                    """,
                    (vendor_id, vendor_field, canonical_id)
                )
                if cursor.fetchone():
                    logger.debug(f"Mapping already exists: {vendor_field} -> {canonical_field}")
                    continue

                # Insert new mapping
                self.conn.execute(
                    """
                    INSERT INTO field_mappings
                    (vendor_id, vendor_field_path, canonical_field_id, transformation_rule, source_type, entity_type, channel_id)
                    VALUES (?, ?, ?, ?, 'websocket', 'ticker', ?)
                    """,
                    (vendor_id, vendor_field, canonical_id, transform, ticker_channel_id)
                )
                created_count += 1
                logger.debug(f"Created mapping: {vendor_field} -> {canonical_field} (transform: {transform})")

            except Exception as e:
                logger.error(f"Failed to create mapping {vendor_field} -> {canonical_field}: {e}")

        self.conn.commit()
        logger.info(f"Created {created_count} mappings for Bithumb")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description=f"Create Bithumb field mappings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed mappings without saving to database"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create mappings in database (requires --dry-run false)"
    )

    args = parser.parse_args()

    # If --create is specified, --dry-run must be false
    if args.create:
        args.dry_run = False

    mapper = BithumbTickerMapper()

    try:
        if args.create:
            logger.info(f"Creating Bithumb mappings...")
            mapper.create_mappings(dry_run=False)
        else:
            logger.info(f"Proposing Bithumb mappings (dry run)...")
            mapper.create_mappings(dry_run=True)
    except Exception as e:
        logger.error(f"Failed to create mappings: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
