#!/usr/bin/env python3
"""
Create Crypto.com Exchange WebSocket ticker field mappings to canonical fields.
Maps Crypto.com-specific field names to industry-standard canonical field names.
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


class CryptoComTickerMapper:
    """
    Maps Crypto.com Exchange WebSocket ticker fields to canonical fields.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.exchange_name = 'crypto_com'

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

    def get_vendor_id(self, vendor_name: str = 'crypto_com') -> Optional[int]:
        """
        Get vendor ID for Crypto.com Exchange.

        Args:
            vendor_name: Vendor name (default: 'crypto_com')

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
            vendor_field_path: Vendor-specific field path (e.g., 'c' for direct field)
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

    def map_crypto_com_ticker_fields(self):
        """
        Map Crypto.com Exchange WebSocket ticker fields to canonical fields.

        Based on Crypto.com Exchange WebSocket ticker format from adapter and database:
        {
            "e": "ticker",            // Event type
            "E": 1234567890000,       // Event time (timestamp)
            "s": "BTC_USDT",          // Symbol
            "p": "100.00",            // Price change
            "P": "0.50",              // Price change percent
            "c": "20000.00",          // Last price
            "v": "1000.00",           // Volume (base volume)
            "q": "20000000.00"        // Quote volume
        }

        Note: This is based on the schema stored in the database. Actual fields may vary.
        Additional fields like high_24h, low_24h, bid_price, ask_price may be available
        in different message formats or channels.

        Returns:
            Number of mappings created
        """
        logger.info("Starting Crypto.com Exchange ticker field mapping...")

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('crypto_com')
        if not vendor_id:
            logger.error("Crypto.com Exchange vendor not found")
            return 0

        channel_id = self.get_websocket_channel_id(vendor_id, 'ticker')
        if not channel_id:
            logger.error("Crypto.com Exchange ticker channel not found")
            return 0

        # Define mappings: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
        # Based on the schema from the database and common Crypto.com Exchange WebSocket format
        mappings = [
            # Symbol field (direct mapping)
            ('s', 'symbol', {'type': 'identity'}, 'ticker'),

            # Price fields (string to numeric conversion)
            ('c', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),

            # Volume fields (string to numeric conversion) - both base and quote volume map to volume_24h
            ('v', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),  # Base volume
            ('q', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),  # Quote volume (alternative)

            # Price change fields (string to numeric conversion)
            ('p', 'price_change_24h', {'type': 'string_to_numeric'}, 'ticker'),  # Absolute price change
            # Note: 'P' (price change percent) doesn't have a direct canonical field match

            # Timestamp field (integer to datetime conversion)
            ('E', 'timestamp', {'type': 'integer_to_datetime'}, 'ticker'),

            # Event type field (for debugging/monitoring, not for normalization)
            ('e', 'event_type', {'type': 'identity'}, 'ticker'),
        ]

        # Note: Additional fields that might be available in other formats:
        # - high_24h (h), low_24h (l), bid_price (b), ask_price (k), open_interest (oi)
        # These are not in the current schema but might be in actual WebSocket messages
        # Adding them as optional mappings with lower priority
        optional_mappings = [
            ('h', 'high_24h', {'type': 'string_to_numeric'}, 'ticker', 5),  # Lower priority
            ('l', 'low_24h', {'type': 'string_to_numeric'}, 'ticker', 5),
            ('b', 'bid_price', {'type': 'string_to_numeric'}, 'ticker', 5),
            ('k', 'ask_price', {'type': 'string_to_numeric'}, 'ticker', 5),
            ('oi', 'open_interest', {'type': 'string_to_numeric'}, 'ticker', 5),
        ]

        created_count = 0
        failed_count = 0

        # Process standard mappings
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

        # Process optional mappings
        for vendor_path, canonical_name, transform_rule, entity_type, priority in optional_mappings:
            # Get canonical field ID
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.debug(f"Optional canonical field not found: {canonical_name}")
                continue  # Skip but don't count as failure

            # Create mapping with lower priority
            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                channel_id=channel_id,
                entity_type=entity_type,
                transformation_rule=transform_rule,
                priority=priority  # Lower priority for optional mappings
            ):
                created_count += 1
            else:
                failed_count += 1

        # Commit all mappings
        self.conn.commit()

        logger.info(f"Crypto.com Exchange ticker mapping complete: {created_count} created, {failed_count} failed")
        return created_count

    def verify_mappings(self) -> Dict[str, Dict]:
        """
        Verify created mappings by querying the database.

        Returns:
            Dictionary with verification statistics
        """
        cursor = self.conn.cursor()

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('crypto_com')
        channel_id = self.get_websocket_channel_id(vendor_id, 'ticker')

        # Count total mappings for Crypto.com ticker
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

        # Get coverage statistics for ticker
        cursor.execute("""
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = 'crypto_com' AND data_type_name = 'ticker'
        """)

        coverage = cursor.fetchone()

        return {
            'total_mappings': total_mappings,
            'by_entity_type': by_entity_type,
            'coverage': dict(coverage) if coverage else {}
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Map Crypto.com Exchange WebSocket ticker fields to canonical fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create Crypto.com Exchange ticker mappings
  python create_crypto_com_mappings.py

  # Create mappings and verify results
  python create_crypto_com_mappings.py --verify

  # Dry run (show what would be mapped without actually creating)
  python create_crypto_com_mappings.py --dry-run

  # Force creation even if some fields missing
  python create_crypto_com_mappings.py --force
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

    parser.add_argument(
        '--force',
        action='store_true',
        help='Create mappings even if some canonical fields are missing'
    )

    args = parser.parse_args()

    with CryptoComTickerMapper() as mapper:
        if args.dry_run:
            print("Dry run mode - would map the following fields:")
            print("=" * 60)

            # Get vendor and channel IDs for display
            vendor_id = mapper.get_vendor_id('crypto_com')
            channel_id = mapper.get_websocket_channel_id(vendor_id, 'ticker')

            print(f"Vendor: crypto_com (id={vendor_id})")
            print(f"Channel: ticker (id={channel_id})")
            print()

            # Show standard mappings
            print("Standard mappings (priority 10):")
            standard_mappings = [
                ('s', 'symbol', 'ticker'),
                ('c', 'last_price', 'ticker'),
                ('v', 'volume_24h', 'ticker'),
                ('q', 'volume_24h', 'ticker'),
                ('p', 'price_change_24h', 'ticker'),
                ('E', 'timestamp', 'ticker'),
                ('e', 'event_type', 'ticker'),
            ]

            for vendor_path, canonical_name, entity_type in standard_mappings:
                field_id = mapper.get_canonical_field_id(canonical_name)
                status = "✓" if field_id else "✗ (field not found)"
                print(f"  {vendor_path:5} → {canonical_name:25} [{entity_type:10}] {status}")

            # Show optional mappings
            print("\nOptional mappings (priority 5, if fields exist):")
            optional_mappings = [
                ('h', 'high_24h', 'ticker'),
                ('l', 'low_24h', 'ticker'),
                ('b', 'bid_price', 'ticker'),
                ('k', 'ask_price', 'ticker'),
                ('oi', 'open_interest', 'ticker'),
            ]

            for vendor_path, canonical_name, entity_type in optional_mappings:
                field_id = mapper.get_canonical_field_id(canonical_name)
                status = "✓" if field_id else "✗ (field not found)"
                print(f"  {vendor_path:5} → {canonical_name:25} [{entity_type:10}] {status}")

            print()
            print(f"Total: {len(standard_mappings) + len(optional_mappings)} potential mappings")

        else:
            # Create mappings
            created = mapper.map_crypto_com_ticker_fields()

            if created > 0:
                print(f"\n✓ Created {created} Crypto.com Exchange ticker field mappings")

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
                        print(f"  Fields defined: {cov.get('fields_defined', 'N/A')}")
                        print(f"  Fields mapped: {cov.get('fields_mapped', 'N/A')}")
                        coverage_pct = cov.get('coverage_percent', 0)
                        print(f"  Coverage: {coverage_pct}%")

                        # Coverage interpretation
                        if coverage_pct >= 70:
                            print(f"  Status: Excellent coverage")
                        elif coverage_pct >= 50:
                            print(f"  Status: Good coverage")
                        elif coverage_pct >= 30:
                            print(f"  Status: Moderate coverage")
                        else:
                            print(f"  Status: Low coverage - consider adding more mappings")

                    print()
            else:
                print("\n✗ No mappings were created")
                if not args.force:
                    print("  Use --force to attempt creation even with missing fields")
                sys.exit(1)


if __name__ == '__main__':
    main()
