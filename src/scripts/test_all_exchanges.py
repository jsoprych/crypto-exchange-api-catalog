#!/usr/bin/env python3
"""
Comprehensive test for all four exchanges ticker normalization.
Tests Coinbase, Binance, Kraken, and Bitfinex WebSocket ticker data normalization
to verify vendor-specific fields are correctly mapped to canonical field names.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.normalization.normalization_engine import NormalizationEngine


def create_coinbase_ticker_sample() -> Dict[str, Any]:
    """Create sample Coinbase WebSocket ticker data."""
    return {
        "type": "ticker",
        "sequence": 5928281082,
        "product_id": "BTC-USD",
        "price": "43210.50",
        "open_24h": "42500.00",
        "volume_24h": "1234.5678",
        "low_24h": "42000.00",
        "high_24h": "43500.00",
        "volume_30d": "98765.4321",
        "best_bid": "43210.00",
        "best_ask": "43211.00",
        "side": "buy",
        "time": "2024-01-31T04:30:00.123456Z",
        "trade_id": 12345678,
        "last_size": "0.01"
    }


def create_binance_ticker_sample() -> Dict[str, Any]:
    """Create sample Binance WebSocket ticker data."""
    return {
        "e": "24hrTicker",
        "E": 1706675400123,  # Unix timestamp in milliseconds
        "s": "BTCUSDT",
        "p": "210.50",  # Price change
        "P": "0.49",    # Price change percent
        "w": "43100.25",  # Weighted average price
        "x": "42500.00",  # First trade price
        "c": "43210.50",  # Last price
        "Q": "0.01",     # Last quantity
        "b": "43210.00",  # Best bid price
        "B": "1.25",     # Best bid quantity
        "a": "43211.00",  # Best ask price
        "A": "0.75",     # Best ask quantity
        "o": "42500.00",  # Open price
        "h": "43500.00",  # High price
        "l": "42000.00",  # Low price
        "v": "1234.5678",  # Total traded base asset volume
        "q": "53245678.90",  # Total traded quote asset volume
        "O": 1706589000123,  # Statistics open time
        "C": 1706675400123,  # Statistics close time
        "F": 12345678,      # First trade ID
        "L": 12345700,      # Last trade ID
        "n": 234            # Total number of trades
    }


def create_kraken_ticker_sample() -> Dict[str, Any]:
    """Create sample Kraken WebSocket ticker data."""
    return {
        "channelID": 12345,
        "channelName": "ticker",
        "pair": "XBT/USD",
        "a": ["43211.00", "1000", "43211.00"],  # ask [price, whole_lot_volume, lot_volume]
        "b": ["43210.00", "2000", "43210.00"],  # bid [price, whole_lot_volume, lot_volume]
        "c": ["43210.50", "0.01"],              # close [price, lot_volume]
        "v": ["1500.25", "1234.5678"],          # volume [today, last_24_hours]
        "p": ["43100.25", "43100.50"],          # volume weighted average price [today, last_24_hours]
        "t": [150, 234],                        # number of trades [today, last_24_hours]
        "l": ["42000.00", "42000.00"],          # low [today, last_24_hours]
        "h": ["43500.00", "43500.00"],          # high [today, last_24_hours]
        "o": ["42500.00", "42500.00"]           # open [today, last_24_hours]
    }


def create_bitfinex_ticker_sample() -> Dict[str, Any]:
    """Create sample Bitfinex WebSocket ticker data."""
    return {
        "CHANNEL_ID": 12345,
        "BID": 43210.0,
        "BID_SIZE": 1.25,
        "ASK": 43211.0,
        "ASK_SIZE": 0.75,
        "DAILY_CHANGE": 210.5,
        "DAILY_CHANGE_RELATIVE": 0.0049,
        "LAST_PRICE": 43210.5,
        "VOLUME": 1234.5678,
        "HIGH": 43500.0,
        "LOW": 42000.0
    }


def test_exchange_normalization(
    engine: NormalizationEngine,
    vendor_name: str,
    sample_data: Dict[str, Any],
    expected_min_fields: List[str]
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Test normalization for a specific exchange.

    Args:
        engine: NormalizationEngine instance
        vendor_name: Exchange name (coinbase, binance, kraken, bitfinex)
        sample_data: Sample vendor data
        expected_min_fields: List of canonical fields expected in output

    Returns:
        Tuple of (success, test_result, normalized_data)
    """
    print(f"\n{'='*70}")
    print(f"TESTING {vendor_name.upper()} TICKER NORMALIZATION")
    print(f"{'='*70}")

    # Run test mapping
    test_result = engine.test_mapping(
        vendor_name=vendor_name,
        data_type='ticker',
        test_data=sample_data,
        source_type='websocket'
    )

    print(f"\nSample Data Keys: {list(sample_data.keys())}")
    print(f"Total mappings available: {test_result['total_mappings']}")
    print(f"Mappings applied: {test_result['applied_count']}")
    print(f"Mappings missed: {test_result['missed_count']}")

    if test_result['applied_mappings']:
        print(f"\nApplied mappings:")
        for mapping in test_result['applied_mappings'][:5]:  # Show first 5
            print(f"  {mapping['vendor_path']:15} → {mapping['canonical_field']:20} = {mapping['value_found']}")
        if len(test_result['applied_mappings']) > 5:
            print(f"  ... and {len(test_result['applied_mappings']) - 5} more")

    # Get normalized data
    normalized = test_result['normalized']

    if not normalized:
        print(f"\n✗ No data normalized for {vendor_name}")
        return False, test_result, {}

    print(f"\nNormalized output ({len(normalized)} fields):")
    for key, value in normalized.items():
        if key.startswith('_'):
            continue  # Skip metadata
        print(f"  {key:20} = {value}")

    # Check for expected fields
    missing_fields = []
    for field in expected_min_fields:
        if field not in normalized:
            missing_fields.append(field)

    if missing_fields:
        print(f"\n⚠  Missing {len(missing_fields)} expected fields: {', '.join(missing_fields)}")
    else:
        print(f"\n✅ All {len(expected_min_fields)} expected fields found!")

    # Check data types
    numeric_fields = ['bid_price', 'ask_price', 'last_price', 'volume_24h', 'high_24h', 'low_24h']
    type_issues = []

    for field in numeric_fields:
        if field in normalized:
            value = normalized[field]
            if not isinstance(value, (int, float)):
                type_issues.append(f"{field} ({type(value).__name__})")

    if type_issues:
        print(f"⚠  Type issues: {', '.join(type_issues)}")
    else:
        print(f"✅ All numeric fields correctly typed")

    success = len(missing_fields) == 0 and len(type_issues) == 0
    return success, test_result, normalized


def test_all_exchanges() -> Dict[str, bool]:
    """Test normalization for all four exchanges."""

    print("\n" + "="*70)
    print("COMPREHENSIVE EXCHANGE NORMALIZATION TEST")
    print("="*70)

    db_path = DATABASE_PATH

    if not db_path.exists():
        print(f"\n✗ Database not found at {db_path}")
        print("Please run 'python main.py init' and create mappings first.")
        return {}

    results = {}

    with NormalizationEngine(db_path) as engine:

        # First, show coverage statistics
        print("\nCOVERAGE STATISTICS:")
        print("-"*70)

        vendors = ['coinbase', 'binance', 'kraken', 'bitfinex']
        for vendor in vendors:
            coverage = engine.get_coverage_stats(vendor)
            if 'ticker' in coverage:
                stats = coverage['ticker']
                coverage_pct = stats['coverage_percent']
                status = "✓" if coverage_pct > 50 else "⚠" if coverage_pct > 0 else "✗"
                print(f"{vendor:10} {status} {coverage_pct:6.1f}% ({stats['fields_mapped']}/{stats['fields_defined']} fields)")

        print("\n" + "="*70)
        print("DETAILED NORMALIZATION TESTS")
        print("="*70)

        # Test Coinbase
        coinbase_sample = create_coinbase_ticker_sample()
        coinbase_expected = [
            'bid_price', 'ask_price', 'last_price', 'volume_24h',
            'high_24h', 'low_24h', 'open_24h', 'volume_30d',
            'symbol', 'timestamp', 'sequence'
        ]
        results['coinbase'] = test_exchange_normalization(
            engine, 'coinbase', coinbase_sample, coinbase_expected
        )[0]

        # Test Binance
        binance_sample = create_binance_ticker_sample()
        binance_expected = [
            'bid_price', 'ask_price', 'last_price', 'volume_24h',
            'high_24h', 'low_24h', 'open_24h',
            'symbol', 'timestamp'
        ]
        results['binance'] = test_exchange_normalization(
            engine, 'binance', binance_sample, binance_expected
        )[0]

        # Test Kraken
        kraken_sample = create_kraken_ticker_sample()
        kraken_expected = [
            'bid_price', 'ask_price', 'last_price', 'volume_24h',
            'high_24h', 'low_24h', 'open_24h',
            'symbol', 'sequence'
        ]
        results['kraken'] = test_exchange_normalization(
            engine, 'kraken', kraken_sample, kraken_expected
        )[0]

        # Test Bitfinex
        bitfinex_sample = create_bitfinex_ticker_sample()
        bitfinex_expected = [
            'bid_price', 'ask_price', 'last_price', 'volume_24h',
            'high_24h', 'low_24h',
            'sequence'
        ]
        results['bitfinex'] = test_exchange_normalization(
            engine, 'bitfinex', bitfinex_sample, bitfinex_expected
        )[0]

    return results


def main():
    """Main entry point."""

    print("\n" + "="*70)
    print("EXCHANGE NORMALIZATION TEST SUITE")
    print("="*70)
    print("Testing ticker field normalization for:")
    print("  • Coinbase  - String fields with descriptive names")
    print("  • Binance   - Single-letter fields (b, a, c, etc.)")
    print("  • Kraken    - Array fields (a[0], b[0], h[1], etc.)")
    print("  • Bitfinex  - Descriptive field names (BID, ASK, etc.)")
    print("="*70)

    results = test_all_exchanges()

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = True
    for exchange, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{exchange:10} {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*70)

    if all_passed:
        print("✅ ALL EXCHANGES PASSED NORMALIZATION TESTS!")
        print("\nThe canonical field mapping system is working correctly for all 4 exchanges.")
        print("Vendor-specific field names are successfully mapped to industry-standard names.")
    else:
        print("⚠  SOME TESTS FAILED")
        print("\nTroubleshooting steps:")
        print("1. Check that mappings exist in the database")
        print("2. Verify sample data matches actual API formats")
        print("3. Check transformation rules in field_mappings table")
        print("4. Run individual exchange tests for details")

    print("="*70)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
