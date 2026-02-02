#!/usr/bin/env python3
"""
Create Bitstamp WebSocket ticker field mappings to canonical fields.
Maps Bitstamp-specific field names to industry-standard canonical field names.
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


class BitstampTickerMapper:
    """
    Maps Bitstamp WebSocket ticker fields to canonical fields.
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

    def get_vendor_id(self, vendor_name: str = 'bitstamp') -> Optional[int]:
        """
        Get vendor ID for Bitstamp.

        Args:
            vendor_name: Vendor name (default: 'bitstamp')

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
            vendor_field_path: Vendor-specific field path (e.g., 'data.bid')
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

    def map_bitstamp_ticker_fields(self):
        """
        Map Bitstamp WebSocket ticker fields to canonical fields.

        Returns:
            Number of mappings created
        """
        logger.info("Starting Bitstamp ticker field mapping...")

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('bitstamp')
        if not vendor_id:
            logger.error("Bitstamp vendor not found")
            return 0

        channel_id = self.get_websocket_channel_id(vendor_id, 'ticker')
        if not channel_id:
            logger.error("Bitstamp ticker channel not found")
            return 0

        # Define mappings: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
        # Based on Bitstamp WebSocket ticker schema: data.bid, data.ask, data.last, data.low, data.high,
        # data.volume, data.vwap, data.open, data.timestamp
        mappings = [
            # Bid price field (string to numeric conversion)
            ('data.bid', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),

            # Ask price field (string to numeric conversion)
            ('data.ask', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),

            # Last price field (string to numeric conversion)
            ('data.last', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),

            # 24-hour low price field (string to numeric conversion)
            ('data.low', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # 24-hour high price field (string to numeric conversion)
            ('data.high', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # 24-hour volume field (string to numeric conversion)
            ('data.volume', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # 24-hour open price field (string to numeric conversion)
            ('data.open', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # Timestamp field (string timestamp - may need conversion)
            ('data.timestamp', 'timestamp', {'type': 'string_to_numeric'}, 'ticker'),

            # VWAP (Volume Weighted Average Price) - map to derived field or note
            # Note: No direct canonical field for VWAP, skipping for now
            # ('data.vwap', 'vwap', {'type': 'string_to_numeric'}, 'ticker'),
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

        logger.info(f"Bitstamp ticker mapping complete: {created_count} created, {failed_count} failed")
        return created_count

    def map_bitstamp_live_trades_fields(self):
        """
        Map Bitstamp WebSocket live_trades fields to canonical fields.

        Returns:
            Number of mappings created
        """
        logger.info("Starting Bitstamp live_trades field mapping...")

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('bitstamp')
        if not vendor_id:
            logger.error("Bitstamp vendor not found")
            return 0

        channel_id = self.get_websocket_channel_id(vendor_id, 'live_trades')
        if not channel_id:
            logger.error("Bitstamp live_trades channel not found")
            return 0

        # Define mappings for trade data
        mappings = [
            # Trade ID field
            ('data.id', 'trade_id', {'type': 'identity'}, 'trade'),

            # Trade price field (string to numeric conversion)
            ('data.price', 'price', {'type': 'string_to_numeric'}, 'trade'),

            # Trade size/amount field (string to numeric conversion)
            ('data.amount', 'size', {'type': 'string_to_numeric'}, 'trade'),

            # Trade type/side (0=buy, 1=sell typically)
            ('data.type', 'side', {
                'type': 'value_mapping',
                'mapping': {'0': 'buy', '1': 'sell'}
            }, 'trade'),

            # Trade timestamp (string to numeric conversion)
            ('data.timestamp', 'timestamp', {'type': 'string_to_numeric'}, 'trade'),
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
                priority=10
            ):
                created_count += 1
            else:
                failed_count += 1

        # Commit all mappings
        self.conn.commit()

        logger.info(f"Bitstamp live_trades mapping complete: {created_count} created, {failed_count} failed")
        return created_count

    def verify_mappings(self) -> Dict[str, int]:
        """
        Verify created mappings by querying the database.

        Returns:
            Dictionary with verification statistics
        """
        cursor = self.conn.cursor()

        # Get vendor ID
        vendor_id = self.get_vendor_id('bitstamp')

        # Count total mappings for Bitstamp
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM field_mappings fm
            JOIN canonical_fields cf ON fm.canonical_field_id = cf.canonical_field_id
            WHERE fm.vendor_id = ?
        """, (vendor_id,))

        total_mappings = cursor.fetchone()['count']

        # Count by entity type
        cursor.execute("""
            SELECT fm.entity_type, COUNT(*) as count
            FROM field_mappings fm
            WHERE fm.vendor_id = ?
            GROUP BY fm.entity_type
        """, (vendor_id,))

        by_entity_type = {row['entity_type']: row['count'] for row in cursor.fetchall()}

        # Get coverage statistics for ticker
        cursor.execute("""
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = 'bitstamp' AND data_type_name = 'ticker'
        """)

        ticker_coverage = cursor.fetchone()

        # Get coverage statistics for trade
        cursor.execute("""
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = 'bitstamp' AND data_type_name = 'trade'
        """)

        trade_coverage = cursor.fetchone()

        return {
            'total_mappings': total_mappings,
            'by_entity_type': by_entity_type,
            'ticker_coverage': dict(ticker_coverage) if ticker_coverage else {},
            'trade_coverage': dict(trade_coverage) if trade_coverage else {}
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Map Bitstamp WebSocket fields to canonical fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create Bitstamp ticker mappings
  python create_bitstamp_mappings.py --ticker

  # Create Bitstamp trade mappings
  python create_bitstamp_mappings.py --trades

  # Create all mappings
  python create_bitstamp_mappings.py --all

  # Create mappings and verify results
  python create_bitstamp_mappings.py --all --verify

  # Dry run (show what would be mapped without actually creating)
  python create_bitstamp_mappings.py --all --dry-run
        """
    )

    parser.add_argument(
        '--ticker',
        action='store_true',
        help='Map ticker fields only'
    )

    parser.add_argument(
        '--trades',
        action='store_true',
        help='Map trade fields only'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Map all field types'
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

    # Determine what to map
    map_ticker = args.ticker or args.all
    map_trades = args.trades or args.all

    if not (map_ticker or map_trades):
        print("Error: No mapping options specified. Use --ticker, --trades, or --all")
        parser.print_help()
        sys.exit(1)

    with BitstampTickerMapper() as mapper:
        if args.dry_run:
            print("Dry run mode - would map the following fields:")
            print("=" * 60)

            # Get vendor ID for display
            vendor_id = mapper.get_vendor_id('bitstamp')
            print(f"Vendor: bitstamp (id={vendor_id})")
            print()

            total_mappings = 0

            if map_ticker:
                print("TICKER MAPPINGS:")
                print("-" * 40)

                # Get channel ID for ticker
                channel_id = mapper.get_websocket_channel_id(vendor_id, 'ticker')
                print(f"Channel: ticker (id={channel_id})")
                print()

                ticker_mappings = [
                    ('data.bid', 'bid_price', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.ask', 'ask_price', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.last', 'last_price', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.low', 'low_24h', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.high', 'high_24h', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.volume', 'volume_24h', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.open', 'open_24h', 'ticker', {'type': 'string_to_numeric'}),
                    ('data.timestamp', 'timestamp', 'ticker', {'type': 'string_to_numeric'}),
                ]

                for vendor_path, canonical_name, entity_type, transform in ticker_mappings:
                    field_id = mapper.get_canonical_field_id(canonical_name)
                    status = "✓" if field_id else "✗ (field not found)"
                    print(f"{vendor_path:30} → {canonical_name:20} [{entity_type:10}] {status}")
                    total_mappings += 1 if field_id else 0

                print(f"\nTotal ticker mappings: {len(ticker_mappings)} potential")

            if map_trades:
                print("\nTRADE MAPPINGS:")
                print("-" * 40)

                # Get channel ID for live_trades
                channel_id = mapper.get_websocket_channel_id(vendor_id, 'live_trades')
                print(f"Channel: live_trades (id={channel_id})")
                print()

                trade_mappings = [
                    ('data.id', 'trade_id', 'trade', {'type': 'identity'}),
                    ('data.price', 'price', 'trade', {'type': 'string_to_numeric'}),
                    ('data.amount', 'size', 'trade', {'type': 'string_to_numeric'}),
                    ('data.type', 'side', 'trade', {'type': 'value_mapping', 'mapping': {'0': 'buy', '1': 'sell'}}),
                    ('data.timestamp', 'timestamp', 'trade', {'type': 'string_to_numeric'}),
                ]

                for vendor_path, canonical_name, entity_type, transform in trade_mappings:
                    field_id = mapper.get_canonical_field_id(canonical_name)
                    status = "✓" if field_id else "✗ (field not found)"
                    print(f"{vendor_path:30} → {canonical_name:20} [{entity_type:10}] {status}")
                    total_mappings += 1 if field_id else 0

                print(f"\nTotal trade mappings: {len(trade_mappings)} potential")

            print(f"\nOverall total: {total_mappings} potential mappings")

        else:
            # Create mappings
            total_created = 0
            ticker_created = 0
            trades_created = 0

            if map_ticker:
                ticker_created = mapper.map_bitstamp_ticker_fields()
                total_created += ticker_created

            if map_trades:
                trades_created = mapper.map_bitstamp_live_trades_fields()
                total_created += trades_created

            if total_created > 0:
                print(f"\n✓ Created {total_created} Bitstamp field mappings:")
                if map_ticker:
                    print(f"  - Ticker: {ticker_created} mappings")
                if map_trades:
                    print(f"  - Trades: {trades_created} mappings")

                if args.verify:
                    print("\nVerification results:")
                    print("=" * 60)

                    stats = mapper.verify_mappings()

                    print(f"Total mappings: {stats['total_mappings']}")

                    if stats['by_entity_type']:
                        print("\nBy entity type:")
                        for entity_type, count in stats['by_entity_type'].items():
                            print(f"  {entity_type}: {count}")

                    if stats.get('ticker_coverage'):
                        cov = stats['ticker_coverage']
                        print(f"\nCoverage for ticker data type:")
                        print(f"  Fields defined: {cov['fields_defined']}")
                        print(f"  Fields mapped: {cov['fields_mapped']}")
                        print(f"  Coverage: {cov.get('coverage_percent', 0)}%")

                    if stats.get('trade_coverage'):
                        cov = stats['trade_coverage']
                        print(f"\nCoverage for trade data type:")
                        print(f"  Fields defined: {cov['fields_defined']}")
                        print(f"  Fields mapped: {cov['fields_mapped']}")
                        print(f"  Coverage: {cov.get('coverage_percent', 0)}%")

                    print()
            else:
                print("\n✗ No mappings were created")
                sys.exit(1)


if __name__ == '__main__':
    main()
