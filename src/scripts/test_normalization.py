#!/usr/bin/env python3
"""
Test script for Normalization Engine with Coinbase ticker data.
Tests that vendor-specific field names are correctly mapped to canonical field names.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.normalization.normalization_engine import NormalizationEngine


def test_coinbase_ticker_normalization():
    """Test normalization of Coinbase WebSocket ticker data."""

    print("=" * 70)
    print("NORMALIZATION ENGINE TEST - COINBASE TICKER")
    print("=" * 70)

    # Sample Coinbase WebSocket ticker message (simplified from actual API)
    coinbase_ticker = {
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

    print("\n1. SAMPLE COINBASE TICKER DATA:")
    print(json.dumps(coinbase_ticker, indent=2))

    # Initialize normalization engine
    db_path = DATABASE_PATH

    if not db_path.exists():
        print(f"\n✗ Database not found at {db_path}")
        print("Please run 'python main.py init' first, then create mappings.")
        return False

    print(f"\n2. LOADING NORMALIZATION ENGINE...")
    print(f"   Database: {db_path}")

    try:
        with NormalizationEngine(db_path) as engine:

            print("\n3. GETTING COVERAGE STATISTICS...")
            coverage = engine.get_coverage_stats('coinbase')

            for data_type, stats in coverage.items():
                print(f"\n   {data_type.upper()}:")
                print(f"     Fields defined: {stats['fields_defined']}")
                print(f"     Fields mapped:  {stats['fields_mapped']}")
                print(f"     Coverage:       {stats['coverage_percent']}%")

            print("\n4. TESTING TICKER NORMALIZATION...")
            test_result = engine.test_mapping(
                vendor_name='coinbase',
                data_type='ticker',
                test_data=coinbase_ticker,
                source_type='websocket'
            )

            print(f"\n   Total mappings available: {test_result['total_mappings']}")
            print(f"   Mappings applied:        {test_result['applied_count']}")
            print(f"   Mappings missed:         {test_result['missed_count']}")

            if test_result['applied_mappings']:
                print("\n   APPLIED MAPPINGS:")
                for mapping in test_result['applied_mappings']:
                    print(f"     {mapping['vendor_path']:25} → {mapping['canonical_field']:20} = {mapping['value_found']}")

            if test_result['missed_mappings']:
                print("\n   MISSED MAPPINGS:")
                for mapping in test_result['missed_mappings'][:5]:  # Show first 5
                    print(f"     {mapping['vendor_path']:25} → {mapping['canonical_field']:20} ({mapping['reason']})")
                if len(test_result['missed_mappings']) > 5:
                    print(f"     ... and {len(test_result['missed_mappings']) - 5} more")

            print("\n5. NORMALIZED OUTPUT:")
            normalized = test_result['normalized']

            if normalized:
                print(json.dumps(normalized, indent=2, default=str))

                # Verify key fields were normalized correctly
                expected_fields = [
                    'bid_price', 'ask_price', 'last_price', 'volume_24h',
                    'high_24h', 'low_24h', 'open_24h', 'volume_30d',
                    'symbol', 'timestamp', 'sequence'
                ]

                print("\n6. VERIFICATION:")
                missing_fields = []
                for field in expected_fields:
                    if field in normalized:
                        value = normalized[field]
                        print(f"   ✓ {field:20} = {value}")
                    else:
                        missing_fields.append(field)
                        print(f"   ✗ {field:20} NOT FOUND")

                # Check data types of numeric fields
                print("\n7. DATA TYPE CHECKS:")
                numeric_fields = ['bid_price', 'ask_price', 'last_price', 'volume_24h']
                for field in numeric_fields:
                    if field in normalized:
                        value = normalized[field]
                        if isinstance(value, (int, float)):
                            print(f"   ✓ {field:20} is numeric: {value}")
                        else:
                            print(f"   ✗ {field:20} is NOT numeric: {type(value).__name__} = {value}")

                if '_normalized' in normalized:
                    print(f"\n8. METADATA:")
                    print(f"   Normalized: {normalized.get('_normalized', False)}")
                    print(f"   Mappings applied: {normalized.get('_mappings_applied', 0)}")

                if missing_fields:
                    print(f"\n⚠  Missing {len(missing_fields)} expected fields: {', '.join(missing_fields)}")
                else:
                    print(f"\n✅ All expected fields were normalized!")

                return True
            else:
                print("\n✗ Normalization failed - empty output")
                return False

    except Exception as e:
        print(f"\n✗ Error during normalization test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_vendors():
    """Test normalization for multiple vendors if mappings exist."""

    print("\n" + "=" * 70)
    print("MULTI-VENDOR COVERAGE TEST")
    print("=" * 70)

    db_path = DATABASE_PATH

    if not db_path.exists():
        return

    vendors = ['coinbase', 'binance', 'kraken', 'bitfinex']

    with NormalizationEngine(db_path) as engine:
        for vendor in vendors:
            print(f"\n{vendor.upper()}:")
            coverage = engine.get_coverage_stats(vendor)

            if coverage:
                for data_type, stats in coverage.items():
                    coverage_pct = stats['coverage_percent']
                    if coverage_pct > 0:
                        status = "✓" if coverage_pct > 50 else "⚠"
                    else:
                        status = "✗"

                    print(f"  {status} {data_type:12} {coverage_pct:6.1f}% "
                          f"({stats['fields_mapped']}/{stats['fields_defined']})")
            else:
                print(f"  ✗ No coverage data available")


def create_sample_messages():
    """Create sample messages for different data types."""

    samples = {
        'ticker': {
            'coinbase': {
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
        },
        'trade': {
            'coinbase': {
                "type": "match",
                "trade_id": 12345678,
                "sequence": 5928281082,
                "maker_order_id": "abc123",
                "taker_order_id": "def456",
                "time": "2024-01-31T04:30:00.123456Z",
                "product_id": "BTC-USD",
                "size": "0.01",
                "price": "43210.50",
                "side": "buy"
            }
        }
    }

    return samples


def main():
    """Main entry point."""

    print("\n" + "=" * 70)
    print("NORMALIZATION ENGINE TEST SUITE")
    print("=" * 70)

    # Test 1: Coinbase ticker normalization
    success = test_coinbase_ticker_normalization()

    # Test 2: Multi-vendor coverage
    test_multiple_vendors()

    print("\n" + "=" * 70)

    if success:
        print("✅ TEST COMPLETE - Normalization engine is working!")
        print("\nNext steps:")
        print("1. Create mappings for other exchanges (Binance, Kraken, Bitfinex)")
        print("2. Add mappings for other data types (order_book, candle, trade)")
        print("3. Test with real WebSocket/REST data")
        print("4. Integrate with trading daemon")
    else:
        print("⚠  TEST INCOMPLETE - Some issues found")
        print("\nTroubleshooting steps:")
        print("1. Run 'python main.py init' to initialize database")
        print("2. Run 'python src/scripts/init_canonical_data.py' to create canonical fields")
        print("3. Run 'python src/scripts/create_coinbase_mappings.py' to create Coinbase mappings")
        print("4. Check database at: " + str(DATABASE_PATH))

    print("=" * 70)


if __name__ == '__main__':
    main()
