# main.py
"""
Main entry point for Vendor API Specification Generator.
Command-line interface for discovering and exporting API specifications.
"""

import argparse
import sys
from pathlib import Path

from config.settings import VENDORS, DATABASE_PATH, OUTPUT_DIR, OUTPUT_CONFIG
from src.database.db_manager import DatabaseManager
from src.database.repository import SpecificationRepository
from src.discovery.spec_generator import SpecificationGenerator
from src.export.json_exporter import JSONExporter
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def cmd_init(args):
    """
    Initialize the database schema.
    """
    logger.info("Initializing database")

    db_manager = DatabaseManager()
    db_manager.connect()
    db_manager.initialize_schema()
    db_manager.close()

    print(f"✓ Database initialized: {DATABASE_PATH}")


def cmd_discover(args):
    """
    Discover API specification for a vendor.
    """
    vendor_name = args.vendor

    # Check if vendor is configured
    if vendor_name not in VENDORS:
        print(f"✗ Unknown vendor: {vendor_name}")
        print(f"Available vendors: {', '.join(VENDORS.keys())}")
        sys.exit(1)

    vendor_config = VENDORS[vendor_name]

    if not vendor_config.get('enabled', False):
        print(f"✗ Vendor {vendor_name} is not enabled")
        sys.exit(1)

    logger.info(f"Starting discovery for {vendor_name}")
    print(f"Discovering {vendor_config['display_name']} API...")

    # Connect to database
    db_manager = DatabaseManager()
    conn = db_manager.connect()

    try:
        # Run discovery
        repository = SpecificationRepository(conn)
        generator = SpecificationGenerator(repository)

        result = generator.generate_specification(vendor_name, vendor_config)

        print(f"\n✓ Discovery complete:")
        print(f"  - Products: {result['products_discovered']}")
        print(f"  - REST endpoints: {result['endpoints_discovered']}")
        print(f"  - WebSocket channels: {result['websocket_channels_discovered']}")
        print(f"  - Duration: {result['duration']:.2f}s")
        print(f"  - Run ID: {result['run_id']}")

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        print(f"\n✗ Discovery failed: {e}")
        sys.exit(1)
    finally:
        db_manager.close()


def cmd_export(args):
    """
    Export API specification to JSON file.
    """
    vendor_name = args.vendor
    naming_convention = args.format
    output_file = args.output

    logger.info(f"Exporting specification for {vendor_name}")
    print(f"Exporting {vendor_name} specification...")

    # Connect to database
    db_manager = DatabaseManager()
    conn = db_manager.connect()

    try:
        # Export specification
        exporter = JSONExporter(conn)
        spec = exporter.export_vendor_spec(
            vendor_name,
            naming_convention=naming_convention,
            include_metadata=args.include_metadata
        )

        # Determine output path
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = OUTPUT_DIR / vendor_name / f"{vendor_name}_api_spec.json"

        # Write to file
        exporter.export_to_file(spec, output_path)

        # Access keys based on naming convention
        products_key = 'products'
        rest_api_key = 'rest_api' if naming_convention == 'snake_case' else 'restApi'
        websocket_api_key = 'websocket_api' if naming_convention == 'snake_case' else 'websocketApi'
        endpoints_key = 'endpoints'
        channels_key = 'channels'

        print(f"\n✓ Specification exported:")
        print(f"  - File: {output_path}")
        print(f"  - Format: {naming_convention}")
        print(f"  - Products: {len(spec[products_key])}")
        print(f"  - REST endpoints: {len(spec[rest_api_key][endpoints_key])}")
        print(f"  - WebSocket channels: {len(spec[websocket_api_key][channels_key])}")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        print(f"\n✗ Export failed: {e}")
        sys.exit(1)
    finally:
        db_manager.close()


def cmd_list_vendors(args):
    """
    List all configured vendors.
    """
    print("Configured vendors:\n")

    for vendor_name, config in VENDORS.items():
        status = "✓ enabled" if config.get('enabled', False) else "✗ disabled"
        print(f"  {vendor_name:15} {config['display_name']:30} {status}")


def cmd_query(args):
    """
    Execute SQL query against the database.
    """
    query = args.query

    db_manager = DatabaseManager()
    conn = db_manager.connect()

    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()

        if rows:
            # Print column headers
            columns = [desc[0] for desc in cursor.description]
            print(" | ".join(columns))
            print("-" * (sum(len(col) for col in columns) + len(columns) * 3))

            # Print rows
            for row in rows:
                print(" | ".join(str(val) for val in row))

            print(f"\n{len(rows)} rows")
        else:
            print("No results")

    except Exception as e:
        logger.error(f"Query failed: {e}")
        print(f"✗ Query failed: {e}")
        sys.exit(1)
    finally:
        db_manager.close()


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(
        description="Vendor API Specification Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python main.py init

  # Discover Coinbase API
  python main.py discover --vendor coinbase

  # Export specification to JSON (Python format)
  python main.py export --vendor coinbase --format snake_case

  # Export specification to JSON (Go format)
  python main.py export --vendor coinbase --format camelCase --output coinbase_go.json

  # List all vendors
  python main.py list-vendors

  # Query database
  python main.py query "SELECT * FROM vendors"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    subparsers.add_parser('init', help='Initialize database schema')

    # Discover command
    parser_discover = subparsers.add_parser('discover', help='Discover vendor API specification')
    parser_discover.add_argument('--vendor', required=True, help='Vendor name (e.g., coinbase)')

    # Export command
    parser_export = subparsers.add_parser('export', help='Export specification to JSON')
    parser_export.add_argument('--vendor', required=True, help='Vendor name')
    parser_export.add_argument(
        '--format',
        choices=['snake_case', 'camelCase'],
        default='snake_case',
        help='Naming convention (default: snake_case)'
    )
    parser_export.add_argument('--output', help='Output file path (optional)')
    parser_export.add_argument(
        '--include-metadata',
        action='store_true',
        default=True,
        help='Include vendor metadata (default: True)'
    )

    # List vendors command
    subparsers.add_parser('list-vendors', help='List all configured vendors')

    # Query command
    parser_query = subparsers.add_parser('query', help='Execute SQL query')
    parser_query.add_argument('query', help='SQL query to execute')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'discover':
        cmd_discover(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'list-vendors':
        cmd_list_vendors(args)
    elif args.command == 'query':
        cmd_query(args)


if __name__ == '__main__':
    main()
