#!/usr/bin/env python3
"""
Configurable exchange coverage test script.
Tests normalization for any number of exchanges with flexible configuration.

Usage:
  python test_exchange_coverage.py                       # Test all exchanges
  python test_exchange_coverage.py coinbase binance      # Test specific exchanges
  python test_exchange_coverage.py --list                # List all available exchanges
  python test_exchange_coverage.py --exclude kraken      # Test all except Kraken
  python test_exchange_coverage.py --data-type order_book # Test order_book data type
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.normalization.normalization_engine import NormalizationEngine


def get_all_exchanges() -> List[str]:
    """
    Dynamically discover all supported exchanges from adapter files.

    Returns:
        List of exchange names sorted alphabetically
    """
    import os
    from pathlib import Path

    # Find adapters directory relative to this script
    script_dir = Path(__file__).parent
    adapters_dir = script_dir.parent.parent / 'src' / 'adapters'

    if not adapters_dir.exists():
        # Fallback to static list if adapters directory doesn't exist
        return [
            'coinbase', 'binance', 'kraken', 'bitfinex',
            'bybit', 'okx', 'kucoin', 'gateio', 'huobi'
        ]

    # Files to exclude (base classes, templates, etc.)
    exclude_files = {'__init__.py', 'base_adapter.py', 'template_adapter.py'}

    exchanges = []

    for file_path in adapters_dir.glob('*.py'):
        if file_path.name not in exclude_files:
            # Extract exchange name from filename: "coinbase_adapter.py" -> "coinbase"
            exchange_name = file_path.name.replace('_adapter.py', '')
            if exchange_name and exchange_name not in exchanges:
                exchanges.append(exchange_name)

    return sorted(exchanges)


# Default list of ALL supported exchanges (dynamically discovered)
ALL_EXCHANGES = get_all_exchanges()


def get_available_exchanges_from_db(db_path: Path) -> List[str]:
    """
    Get list of exchanges available in the database.

    Args:
        db_path: Path to SQLite database

    Returns:
        List of exchange names
    """
    import sqlite3

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT vendor_name FROM vendors ORDER BY vendor_name")
        rows = cursor.fetchall()

        exchanges = [row['vendor_name'] for row in rows]
        conn.close()
        return exchanges
    except Exception as e:
        print(f"Error reading database: {e}")
        return []


def create_exchange_sample_data(
    exchange_name: str,
    data_type: str = 'ticker'
) -> Dict[str, Any]:
    """
    Create sample data for a specific exchange and data type.

    Args:
        exchange_name: Name of the exchange
        data_type: Type of data (ticker, trade, order_book, candle)

    Returns:
        Sample data dictionary
    """
    # Common sample values
    base_values = {
        'bid_price': 43210.0,
        'ask_price': 43211.0,
        'last_price': 43210.5,
        'volume_24h': 1234.5678,
        'high_24h': 43500.0,
        'low_24h': 42000.0,
        'open_24h': 42500.0,
        'sequence': 5928281082,
        'symbol': 'BTC-USD' if '-' in exchange_name else 'BTCUSDT',
        'timestamp_ms': 1706675400123,
    }

    if exchange_name == 'coinbase':
        if data_type == 'ticker':
            return {
                "type": "ticker",
                "sequence": base_values['sequence'],
                "product_id": base_values['symbol'],
                "price": str(base_values['last_price']),
                "open_24h": str(base_values['open_24h']),
                "volume_24h": str(base_values['volume_24h']),
                "low_24h": str(base_values['low_24h']),
                "high_24h": str(base_values['high_24h']),
                "volume_30d": "98765.4321",
                "best_bid": str(base_values['bid_price']),
                "best_ask": str(base_values['ask_price']),
                "side": "buy",
                "time": "2024-01-31T04:30:00.123456Z",
                "trade_id": 12345678,
                "last_size": "0.01"
            }

    elif exchange_name == 'binance':
        if data_type == 'ticker':
            return {
                "e": "24hrTicker",
                "E": base_values['timestamp_ms'],  # Event time
                "s": base_values['symbol'],
                "p": "210.50",  # Price change
                "P": "0.49",    # Price change percent
                "w": "43100.25",  # Weighted average price
                "x": "42500.00",  # First trade price
                "c": str(base_values['last_price']),  # Last price
                "Q": "0.01",     # Last quantity
                "b": str(base_values['bid_price']),   # Best bid price
                "B": "1.25",     # Best bid quantity
                "a": str(base_values['ask_price']),   # Best ask price
                "A": "0.75",     # Best ask quantity
                "o": str(base_values['open_24h']),    # Open price
                "h": str(base_values['high_24h']),    # High price
                "l": str(base_values['low_24h']),     # Low price
                "v": str(base_values['volume_24h']),  # Volume
                "q": "53245678.90",  # Quote volume
                "O": 1706589000123,  # Statistics open time
                "C": base_values['timestamp_ms'],  # Statistics close time
                "F": 12345678,      # First trade ID
                "L": 12345700,      # Last trade ID
                "n": 234            # Total number of trades
            }

    elif exchange_name == 'kraken':
        if data_type == 'ticker':
            return {
                "channelID": int(base_values['sequence']),
                "channelName": "ticker",
                "pair": "XBT/USD",
                "a": [str(base_values['ask_price']), "1000", str(base_values['ask_price'])],
                "b": [str(base_values['bid_price']), "2000", str(base_values['bid_price'])],
                "c": [str(base_values['last_price']), "0.01"],
                "v": ["1500.25", str(base_values['volume_24h'])],
                "p": ["43100.25", "43100.50"],
                "t": [150, 234],
                "l": [str(base_values['low_24h']), str(base_values['low_24h'])],
                "h": [str(base_values['high_24h']), str(base_values['high_24h'])],
                "o": [str(base_values['open_24h']), str(base_values['open_24h'])]
            }

    elif exchange_name == 'bitfinex':
        if data_type == 'ticker':
            return {
                "CHANNEL_ID": int(base_values['sequence']),
                "BID": base_values['bid_price'],
                "BID_SIZE": 1.25,
                "ASK": base_values['ask_price'],
                "ASK_SIZE": 0.75,
                "DAILY_CHANGE": 210.5,
                "DAILY_CHANGE_RELATIVE": 0.0049,
                "LAST_PRICE": base_values['last_price'],
                "VOLUME": base_values['volume_24h'],
                "HIGH": base_values['high_24h'],
                "LOW": base_values['low_24h']
            }

    elif exchange_name == 'okx':
        if data_type == 'ticker':
            return {
                "arg": {
                    "channel": "tickers",
                    "instId": base_values['symbol']
                },
                "data": [{
                    "instId": base_values['symbol'],
                    "last": str(base_values['last_price']),
                    "lastSz": "0.01",
                    "askPx": str(base_values['ask_price']),
                    "askSz": "0.75",
                    "bidPx": str(base_values['bid_price']),
                    "bidSz": "1.25",
                    "open24h": str(base_values['open_24h']),
                    "high24h": str(base_values['high_24h']),
                    "low24h": str(base_values['low_24h']),
                    "volCcy24h": "53245678.90",
                    "vol24h": str(base_values['volume_24h']),
                    "ts": str(base_values['timestamp_ms'])
                }]
            }

    elif exchange_name == 'kucoin':
        if data_type == 'ticker':
            return {
                "type": "message",
                "topic": f"/market/ticker:{base_values['symbol']}",
                "subject": "trade.ticker",
                "data": {
                    "sequence": str(base_values['sequence']),
                    "price": str(base_values['last_price']),
                    "size": "0.01",
                    "bestAsk": str(base_values['ask_price']),
                    "bestAskSize": "0.75",
                    "bestBid": str(base_values['bid_price']),
                    "bestBidSize": "1.25",
                    "time": str(base_values['timestamp_ms'] * 1000000)  # nanoseconds
                }
            }

    elif exchange_name == 'gateio':
        if data_type == 'ticker':
            return {
                "time": base_values['timestamp_ms'],
                "time_ms": base_values['timestamp_ms'],
                "channel": "spot.tickers",
                "event": "update",
                "result": {
                    "currency_pair": base_values['symbol'],
                    "last": str(base_values['last_price']),
                    "lowest_ask": str(base_values['ask_price']),
                    "highest_bid": str(base_values['bid_price']),
                    "change_percentage": "0.49",
                    "base_volume": str(base_values['volume_24h']),
                    "quote_volume": "53245678.90",
                    "high_24h": str(base_values['high_24h']),
                    "low_24h": str(base_values['low_24h'])
                }
            }

    elif exchange_name == 'huobi':
        if data_type == 'ticker':
            return {
                "e": "24hrTicker",
                "E": base_values['timestamp_ms'],
                "s": base_values['symbol'],
                "p": "210.50",
                "P": "0.49",
                "c": str(base_values['last_price']),
                "v": str(base_values['volume_24h']),
                "q": "53245678.90"
            }

    elif exchange_name == 'bybit':
        if data_type == 'ticker':
            return {
                "topic": f"tickers.{base_values['symbol']}",
                "ts": base_values['timestamp_ms'],
                "type": "snapshot",
                "data": {
                    "symbol": base_values['symbol'],
                    "lastPrice": str(base_values['last_price']),
                    "highPrice24h": str(base_values['high_24h']),
                    "lowPrice24h": str(base_values['low_24h']),
                    "volume24h": str(base_values['volume_24h']),
                    "turnover24h": "53245678.90",
                    "price24hPcnt": "0.49"
                }
            }

    # Default/fallback sample (minimal structure)
    return {
        "symbol": base_values['symbol'],
        "price": str(base_values['last_price']),
        "timestamp": base_values['timestamp_ms']
    }


def test_exchange_normalization(
    engine: NormalizationEngine,
    exchange_name: str,
    data_type: str = 'ticker',
    source_type: str = 'websocket'
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Test normalization for a specific exchange.

    Args:
        engine: NormalizationEngine instance
        exchange_name: Exchange name
        data_type: Data type to test
        source_type: Source type (websocket or rest)

    Returns:
        Tuple of (success, test_result, normalized_data)
    """
    # Create sample data for this exchange
    sample_data = create_exchange_sample_data(exchange_name, data_type)

    # Get coverage statistics first
    coverage_stats = engine.get_coverage_stats(exchange_name)

    # Run test mapping
    try:
        test_result = engine.test_mapping(
            vendor_name=exchange_name,
            data_type=data_type,
            test_data=sample_data,
            source_type=source_type
        )
    except Exception as e:
        print(f"✗ Error testing {exchange_name}: {e}")
        return False, {}, {}

    # Get normalized data
    normalized = test_result['normalized']

    # Determine success based on coverage and mappings applied
    if data_type in coverage_stats:
        type_stats = coverage_stats[data_type]
        fields_defined = type_stats['fields_defined']
        fields_mapped = type_stats['fields_mapped']
        coverage_percent = type_stats['coverage_percent']

        # Success if we have some coverage or applied some mappings
        success = fields_mapped > 0 or test_result['applied_count'] > 0
    else:
        # No coverage defined for this data type
        success = test_result['applied_count'] > 0

    return success, test_result, normalized


def print_exchange_test_results(
    exchange_name: str,
    test_result: Dict[str, Any],
    normalized: Dict[str, Any],
    coverage_stats: Dict[str, Any],
    data_type: str = 'ticker',
    verbose: bool = False
):
    """
    Print formatted test results for an exchange.

    Args:
        exchange_name: Exchange name
        test_result: Test result dictionary
        normalized: Normalized data
        coverage_stats: Coverage statistics
        data_type: Data type tested
        verbose: Whether to print detailed information
    """
    print(f"\n{'='*80}")
    print(f"EXCHANGE: {exchange_name.upper()} - {data_type.upper()} DATA")
    print(f"{'='*80}")

    # Coverage information
    if data_type in coverage_stats:
        stats = coverage_stats[data_type]
        print(f"\nCoverage: {stats['coverage_percent']:.1f}% "
              f"({stats['fields_mapped']}/{stats['fields_defined']} fields)")
    else:
        print(f"\nCoverage: No {data_type} mappings defined")

    # Test results
    print(f"\nTest Results:")
    print(f"  Mappings available: {test_result['total_mappings']}")
    print(f"  Mappings applied:   {test_result['applied_count']}")
    print(f"  Mappings missed:    {test_result['missed_count']}")

    if verbose and test_result['applied_mappings']:
        print(f"\nApplied mappings:")
        for mapping in test_result['applied_mappings'][:10]:  # Show first 10
            print(f"  {mapping['vendor_path']:30} → {mapping['canonical_field']:20}")
        if len(test_result['applied_mappings']) > 10:
            print(f"  ... and {len(test_result['applied_mappings']) - 10} more")

    # Normalized fields
    if normalized:
        non_meta_fields = {k: v for k, v in normalized.items() if not k.startswith('_')}
        if non_meta_fields:
            print(f"\nNormalized fields ({len(non_meta_fields)}):")
            for key, value in list(non_meta_fields.items())[:15]:  # Show first 15
                print(f"  {key:20} = {value}")
            if len(non_meta_fields) > 15:
                print(f"  ... and {len(non_meta_fields) - 15} more")
    else:
        print(f"\n✗ No data normalized")

    # Check for common issues
    if normalized and 'timestamp' not in normalized:
        print(f"\n⚠  Warning: timestamp field missing in normalized data")
    if normalized and 'symbol' not in normalized:
        print(f"\n⚠  Warning: symbol field missing in normalized data")

    print(f"{'-'*80}")


def test_exchanges(
    exchanges: List[str],
    data_type: str = 'ticker',
    source_type: str = 'websocket',
    verbose: bool = False,
    db_path: Path = DATABASE_PATH
) -> Dict[str, bool]:
    """
    Test normalization for multiple exchanges.

    Args:
        exchanges: List of exchange names to test
        data_type: Data type to test
        source_type: Source type
        verbose: Whether to print detailed information
        db_path: Path to database

    Returns:
        Dictionary with test results (exchange -> success)
    """
    if not db_path.exists():
        print(f"\n✗ Database not found at {db_path}")
        print("Please run 'python main.py init' and create mappings first.")
        return {}

    results = {}

    print(f"\n{'='*80}")
    print(f"TESTING {len(exchanges)} EXCHANGES - {data_type.upper()} DATA")
    print(f"{'='*80}")

    with NormalizationEngine(db_path) as engine:
        for exchange in exchanges:
            try:
                # Get coverage stats for this exchange
                coverage_stats = engine.get_coverage_stats(exchange)

                # Test normalization
                success, test_result, normalized = test_exchange_normalization(
                    engine, exchange, data_type, source_type
                )

                # Print results
                print_exchange_test_results(
                    exchange, test_result, normalized,
                    coverage_stats, data_type, verbose
                )

                results[exchange] = success

            except Exception as e:
                print(f"\n{'='*80}")
                print(f"EXCHANGE: {exchange.upper()} - ERROR")
                print(f"{'='*80}")
                print(f"✗ Error: {e}")
                print(f"{'-'*80}")
                results[exchange] = False

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test normalization for multiple exchanges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all exchanges (default)
  python test_exchange_coverage.py

  # Test specific exchanges
  python test_exchange_coverage.py coinbase binance kraken

  # Test all except some exchanges
  python test_exchange_coverage.py --exclude bitfinex bybit

  # Test with verbose output
  python test_exchange_coverage.py --verbose

  # Test order_book data type
  python test_exchange_coverage.py --data-type order_book

  # List available exchanges
  python test_exchange_coverage.py --list
        """
    )

    # Exchange selection arguments
    parser.add_argument(
        'exchanges',
        nargs='*',
        default=['all'],
        help='Exchange names to test (default: all)'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=[],
        help='Exclude specific exchanges from testing'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available exchanges and exit'
    )

    # Test configuration arguments
    parser.add_argument(
        '--data-type',
        choices=['ticker', 'trade', 'order_book', 'candle'],
        default='ticker',
        help='Data type to test (default: ticker)'
    )
    parser.add_argument(
        '--source-type',
        choices=['websocket', 'rest'],
        default='websocket',
        help='Source type to test (default: websocket)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print verbose output including applied mappings'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DATABASE_PATH,
        help=f'Path to database (default: {DATABASE_PATH})'
    )

    args = parser.parse_args()

    # List available exchanges if requested
    if args.list:
        available = get_available_exchanges_from_db(args.db_path)
        print(f"\nAvailable exchanges in database ({len(available)}):")
        for exchange in available:
            print(f"  • {exchange}")

        print(f"\nAll supported exchanges ({len(ALL_EXCHANGES)}):")
        for exchange in ALL_EXCHANGES:
            status = "✓" if exchange in available else "✗"
            print(f"  {status} {exchange}")
        return

    # Determine which exchanges to test
    if 'all' in args.exchanges or not args.exchanges:
        # Start with all supported exchanges
        exchanges_to_test = ALL_EXCHANGES.copy()
    else:
        # Use specified exchanges
        exchanges_to_test = args.exchanges

    # Get available exchanges from database
    available_exchanges = get_available_exchanges_from_db(args.db_path)

    # Filter exchanges: must be in database and not excluded
    filtered_exchanges = []
    for exchange in exchanges_to_test:
        if exchange not in available_exchanges:
            print(f"⚠  Exchange '{exchange}' not found in database, skipping")
            continue
        if exchange in args.exclude:
            print(f"⚠  Exchange '{exchange}' excluded by user")
            continue
        filtered_exchanges.append(exchange)

    if not filtered_exchanges:
        print(f"\n✗ No exchanges to test")
        print(f"Available exchanges: {', '.join(available_exchanges)}")
        return

    # Test the exchanges
    results = test_exchanges(
        exchanges=filtered_exchanges,
        data_type=args.data_type,
        source_type=args.source_type,
        verbose=args.verbose,
        db_path=args.db_path
    )

    # Print summary
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY - {args.data_type.upper()} DATA")
    print(f"{'='*80}")

    passed = [e for e, s in results.items() if s]
    failed = [e for e, s in results.items() if not s]

    print(f"\nExchanges tested: {len(results)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if passed:
        print(f"\n✅ Passed exchanges:")
        for exchange in sorted(passed):
            print(f"  • {exchange}")

    if failed:
        print(f"\n✗ Failed exchanges:")
        for exchange in sorted(failed):
            print(f"  • {exchange}")

    # Overall coverage statistics
    if results and args.db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(args.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(DISTINCT vendor_name) as total_vendors,
                    SUM(CASE WHEN fields_mapped > 0 THEN 1 ELSE 0 END) as vendors_with_mappings,
                    AVG(coverage_percent) as avg_coverage
                FROM vendor_coverage_view
                WHERE data_type_name = ?
            """, (args.data_type,))

            stats = cursor.fetchone()
            conn.close()

            if stats:
                print(f"\n{'='*80}")
                print(f"OVERALL COVERAGE STATISTICS")
                print(f"{'='*80}")
                print(f"Total vendors with {args.data_type} mappings: "
                      f"{stats['vendors_with_mappings']}/{stats['total_vendors']}")
                print(f"Average coverage: {stats['avg_coverage']:.1f}%")

        except Exception as e:
            print(f"\nNote: Could not retrieve overall coverage statistics: {e}")

    print(f"\n{'='*80}")

    # Exit with appropriate code
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
