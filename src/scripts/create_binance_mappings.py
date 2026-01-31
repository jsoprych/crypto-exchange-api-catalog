#!/usr/bin/env python3
"""
Create Binance WebSocket ticker field mappings to canonical fields.
Maps Binance-specific field names (single letters) to industry-standard canonical field names.
"""

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


class BinanceTickerMapper:
    """
    Maps Binance WebSocket ticker fields to canonical fields.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None

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
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_vendor_id(self, vendor_name: str = 'binance') -> Optional[int]:
        """
        Get vendor ID for Binance.

        Args:
            vendor_name: Vendor name (default: 'binance')

        Returns:
            vendor_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            (vendor_name,)
        )
        row = cursor.fetchone()
        return row['vendor_id'] if row else None

    def get_websocket_channel_id(self, vendor_id: int, channel_name: str = 'ticker') -> Optional[int]:
        """
        Get WebSocket channel ID for ticker channel.

        Args:
            vendor_id: Vendor ID
            channel_name: Channel name (default: 'ticker')

        Returns:
            channel_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT channel_id FROM websocket_channels WHERE vendor_id = ? AND channel_name = ?",
            (vendor_id, channel_name)
        )
        row = cursor.fetchone()
        return row['channel_id'] if row else None

    def get_canonical_field_id(self, field_name: str) -> Optional[int]:
        """
        Get canonical field ID by field name.

        Args:
            field_name: Canonical field name (e.g., 'bid_price')

        Returns:
            canonical_field_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT canonical_field_id FROM canonical_fields WHERE field_name = ?",
            (field_name,)
        )
        row = cursor.fetchone()
        return row['canonical_field_id'] if row else None

    def create_field_mapping(
        self,
        vendor_id: int,
        canonical_field_id: int,
        vendor_field_path: str,
        channel_id: int,
        entity_type: str = 'ticker',
        transformation_rule: Optional[Dict] = None,
        priority: int = 0
    ) -> bool:
        """
        Create a field mapping entry.

        Args:
            vendor_id: Vendor ID
            canonical_field_id: Canonical field ID
            vendor_field_path: Vendor-specific field path (e.g., 'b' for Binance bid price)
            channel_id: WebSocket channel ID
            entity_type: Data type (ticker, order_book, trade, candle)
            transformation_rule: Optional transformation rules JSON
            priority: Mapping priority (higher = preferred)

        Returns:
            True if mapping created or already exists, False on error
        """
        cursor = self.conn.cursor()

        # Check if mapping already exists
        cursor.execute("""
            SELECT mapping_id FROM field_mappings
            WHERE vendor_id = ? AND canonical_field_id = ?
            AND vendor_field_path = ? AND channel_id = ?
        """, (vendor_id, canonical_field_id, vendor_field_path, channel_id))

        if cursor.fetchone():
            logger.debug(f"Mapping already exists: {vendor_field_path} -> {canonical_field_id}")
            return True

        try:
            cursor.execute("""
                INSERT INTO field_mappings (
                    vendor_id, canonical_field_id, source_type,
                    entity_type, vendor_field_path, channel_id,
                    transformation_rule, priority, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id,
                canonical_field_id,
                'websocket',  # source_type
                entity_type,
                vendor_field_path,
                channel_id,
                json.dumps(transformation_rule) if transformation_rule else None,
                priority,
                True
            ))
            logger.info(f"Created mapping: {vendor_field_path} -> canonical field {canonical_field_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to create mapping for {vendor_field_path}: {e}")
            return False

    def map_binance_ticker_fields(self):
        """
        Map Binance WebSocket ticker fields to canonical fields.

        Returns:
            Number of mappings created
        """
        logger.info("Starting Binance ticker field mapping...")

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('binance')
        if not vendor_id:
            logger.error("Binance vendor not found")
            return 0

        channel_id = self.get_websocket_channel_id(vendor_id, 'ticker')
        if not channel_id:
            logger.error("Binance ticker channel not found")
            return 0

        # Define mappings for Binance 24hrTicker
        # Format: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
        mappings = [
            # Price fields - Binance uses string format for numbers
            ('b', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('B', 'best_bid_size', {'type': 'string_to_numeric'}, 'ticker'),
            ('a', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('A', 'best_ask_size', {'type': 'string_to_numeric'}, 'ticker'),
            ('c', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),

            # OHLCV fields
            ('h', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('l', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('o', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('v', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # Symbol field
            ('s', 'symbol', {'type': 'identity'}, 'ticker'),

            # Timestamp field - Binance uses Unix timestamp in milliseconds
            ('E', 'timestamp', {'type': 'ms_to_datetime'}, 'ticker'),

            # Trade-related fields (could map to trade entity)
            ('F', 'trade_id', {'type': 'string_to_integer'}, 'trade'),  # First trade ID
            ('L', 'trade_id', {'type': 'string_to_integer'}, 'trade'),  # Last trade ID
            ('n', 'sequence', {'type': 'string_to_integer'}, 'trade'),  # Total number of trades (as sequence)

            # Additional price info
            ('x', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),  # First trade price (alternative open)

            # Quote volume (alternative volume measure)
            ('q', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),  # Total traded quote asset volume
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            # Get canonical field ID
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            # Create mapping
            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                channel_id=channel_id,
                entity_type=entity_type,
                transformation_rule=transform_rule,
                priority=10  # High priority for direct mappings
            ):
                created_count += 1
            else:
                failed_count += 1

        # Commit all mappings
        self.conn.commit()

        logger.info(f"Binance ticker mapping complete: {created_count} created, {failed_count} failed")
        return created_count

    def verify_mappings(self) -> Dict[str, int]:
        """
        Verify created mappings by querying the database.

        Returns:
            Dictionary with verification statistics
        """
        cursor = self.conn.cursor()

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('binance')
        channel_id = self.get_websocket_channel_id(vendor_id, 'ticker')

        # Count total mappings for Binance ticker
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM field_mappings fm
            JOIN canonical_fields cf ON fm.canonical_field_id = cf.canonical_field_id
            WHERE fm.vendor_id = ? AND fm.channel_id = ?
        """, (vendor_id, channel_id))

        total_mappings = cursor.fetchone()['count']

        # Count by entity type
        cursor.execute("""
            SELECT fm.entity_type, COUNT(*) as count
            FROM field_mappings fm
            WHERE fm.vendor_id = ? AND fm.channel_id = ?
            GROUP BY fm.entity_type
        """, (vendor_id, channel_id))

        by_entity_type = {row['entity_type']: row['count'] for row in cursor.fetchall()}

        # Get coverage statistics
        cursor.execute("""
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = 'binance' AND data_type_name = 'ticker'
        """)

        coverage = cursor.fetchone()

        return {
            'total_mappings': total_mappings,
            'by_entity_type': by_entity_type,
            'coverage': dict(coverage) if coverage else {}
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Map Binance WebSocket ticker fields to canonical fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create Binance ticker mappings
  python create_binance_mappings.py

  # Create mappings and verify results
  python create_binance_mappings.py --verify

  # Dry run (show what would be mapped without actually creating)
  python create_binance_mappings.py --dry-run
        """
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify mappings after creation'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be mapped without creating actual entries'
    )

    args = parser.parse_args()

    with BinanceTickerMapper() as mapper:
        if args.dry_run:
            print("Dry run mode - would map the following fields:")
            print("=" * 60)

            # Get vendor and channel IDs for display
            vendor_id = mapper.get_vendor_id('binance')
            channel_id = mapper.get_websocket_channel_id(vendor_id, 'ticker')

            print(f"Vendor: binance (id={vendor_id})")
            print(f"Channel: ticker (id={channel_id})")
            print()

            # Show what would be mapped
            mappings = [
                ('b', 'bid_price', 'ticker'),
                ('B', 'best_bid_size', 'ticker'),
                ('a', 'ask_price', 'ticker'),
                ('A', 'best_ask_size', 'ticker'),
                ('c', 'last_price', 'ticker'),
                ('h', 'high_24h', 'ticker'),
                ('l', 'low_24h', 'ticker'),
                ('o', 'open_24h', 'ticker'),
                ('v', 'volume_24h', 'ticker'),
                ('s', 'symbol', 'ticker'),
                ('E', 'timestamp', 'ticker'),
                ('F', 'trade_id', 'trade'),
                ('L', 'trade_id', 'trade'),
                ('n', 'sequence', 'trade'),
                ('x', 'open_24h', 'ticker'),
                ('q', 'volume_24h', 'ticker'),
            ]

            for vendor_path, canonical_name, entity_type in mappings:
                field_id = mapper.get_canonical_field_id(canonical_name)
                status = "✓" if field_id else "✗ (field not found)"
                print(f"{vendor_path:5} → {canonical_name:20} [{entity_type:10}] {status}")

            print()
            print("Total: 16 potential mappings")

        else:
            # Create mappings
            created = mapper.map_binance_ticker_fields()

            if created > 0:
                print(f"\n✓ Created {created} Binance ticker field mappings")

                if args.verify:
                    print("\nVerification results:")
                    print("=" * 60)

                    stats = mapper.verify_mappings()

                    print(f"Total mappings: {stats['total_mappings']}")

                    if stats['by_entity_type']:
                        print("\nBy entity type:")
                        for entity_type, count in stats['by_entity_type'].items():
                            print(f"  {entity_type}: {count}")

                    if stats.get('coverage'):
                        cov = stats['coverage']
                        print(f"\nCoverage for ticker data type:")
                        print(f"  Fields defined: {cov['fields_defined']}")
                        print(f"  Fields mapped: {cov['fields_mapped']}")
                        print(f"  Coverage: {cov['coverage_percent']}%")

                    print()
            else:
                print("\n✗ No mappings were created")
                sys.exit(1)


if __name__ == '__main__':
    main()
