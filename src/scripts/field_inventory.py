#!/usr/bin/env python3
"""
Field Inventory Extraction Script
Extracts all field names from existing message_schema and response_schema
for the 4 target exchanges (Coinbase, Kraken, Binance, Bitfinex).
"""

import json
import sqlite3
from pathlib import Path
import sys
from typing import Dict, List, Set, Tuple, Any, Optional
import csv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class FieldInventoryExtractor:
    """
    Extracts field inventory from database schemas.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize extractor with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection."""
        if self.conn is None:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

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

    def extract_json_fields(self, json_str: str, base_path: str = "") -> Set[str]:
        """
        Recursively extract field names from JSON schema.

        Args:
            json_str: JSON string containing schema
            base_path: Current JSON path for nested fields

        Returns:
            Set of field paths in dot notation
        """
        fields = set()

        if not json_str or json_str.strip() == "":
            return fields

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return fields

        return self._extract_fields_from_dict(data, base_path)

    def _extract_fields_from_dict(self, data: Any, current_path: str = "") -> Set[str]:
        """
        Recursively extract fields from dictionary or list.

        Args:
            data: Dictionary, list, or primitive value
            current_path: Current JSON path

        Returns:
            Set of field paths
        """
        fields = set()

        if isinstance(data, dict):
            for key, value in data.items():
                # Skip type annotations like "string", "integer", "array"
                # But still add the field path if it's not a metadata key
                if key in ["type", "description", "format"]:
                    continue

                new_path = f"{current_path}.{key}" if current_path else key

                # Add the field path
                fields.add(new_path)

                # Recursively process nested structures
                if isinstance(value, (dict, list)):
                    fields.update(self._extract_fields_from_dict(value, new_path))
                elif isinstance(value, str) and value in ["string", "integer", "float", "decimal", "boolean", "datetime", "array", "object"]:
                    # This is a type annotation, keep the field path but don't recurse
                    pass

        elif isinstance(data, list):
            # Handle arrays - extract schema from first element if it's a dict
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    fields.update(self._extract_fields_from_dict(item, f"{current_path}[{i}]"))
                elif isinstance(item, str) and item not in ["string", "integer", "float", "decimal", "boolean", "datetime", "array", "object"]:
                    # Might be a field name reference
                    fields.add(f"{current_path}.{item}")

        return fields

    def get_vendor_websocket_fields(self, vendor_id: int, vendor_name: str) -> Dict[str, List[str]]:
        """
        Extract field names from WebSocket channels for a vendor.

        Args:
            vendor_id: Vendor ID from database
            vendor_name: Vendor name for logging

        Returns:
            Dictionary mapping channel names to list of field paths
        """
        cursor = self.conn.cursor()

        query = """
        SELECT channel_name, message_schema, message_types
        FROM websocket_channels
        WHERE vendor_id = ? AND status = 'active'
        """

        cursor.execute(query, (vendor_id,))
        rows = cursor.fetchall()

        channel_fields = {}

        for row in rows:
            channel_name = row['channel_name']
            message_schema = row['message_schema']
            message_types = row['message_types']

            fields = set()

            # Extract fields from main message_schema
            if message_schema:
                fields.update(self.extract_json_fields(message_schema, ""))

            # Parse message_types if it's a JSON array
            if message_types:
                try:
                    types_list = json.loads(message_types)
                    if isinstance(types_list, list):
                        for msg_type in types_list:
                            if msg_type not in ["snapshot", "update", "l2update", "ticker", "subscriptions"]:
                                fields.add(f"message_type.{msg_type}")
                except json.JSONDecodeError:
                    pass

            if fields:
                channel_fields[channel_name] = sorted(fields)
                logger.debug(f"  - {channel_name}: {len(fields)} fields")

        logger.info(f"Extracted {sum(len(f) for f in channel_fields.values())} WebSocket fields from {len(channel_fields)} channels for {vendor_name}")
        return channel_fields

    def get_vendor_rest_fields(self, vendor_id: int, vendor_name: str) -> Dict[str, List[str]]:
        """
        Extract field names from REST endpoints for a vendor.

        Args:
            vendor_id: Vendor ID from database
            vendor_name: Vendor name for logging

        Returns:
            Dictionary mapping endpoint paths to list of field paths
        """
        cursor = self.conn.cursor()

        query = """
        SELECT path, method, response_schema
        FROM rest_endpoints
        WHERE vendor_id = ? AND status = 'active'
        """

        cursor.execute(query, (vendor_id,))
        rows = cursor.fetchall()

        endpoint_fields = {}

        for row in rows:
            path = row['path']
            method = row['method']
            response_schema = row['response_schema']

            endpoint_key = f"{method} {path}"

            fields = set()

            # Extract fields from response_schema
            if response_schema:
                fields.update(self.extract_json_fields(response_schema, ""))

            # Also consider common fields from path patterns
            if '{' in path and '}' in path:
                # Extract path parameters
                import re
                path_params = re.findall(r'\{(.*?)\}', path)
                for param in path_params:
                    fields.add(f"path_param.{param}")

            if fields:
                endpoint_fields[endpoint_key] = sorted(fields)
                logger.debug(f"  - {endpoint_key}: {len(fields)} fields")

        logger.info(f"Extracted {sum(len(f) for f in endpoint_fields.values())} REST fields from {len(endpoint_fields)} endpoints for {vendor_name}")
        return endpoint_fields

    def extract_all_vendor_fields(self) -> Dict[str, Dict]:
        """
        Extract fields from all 4 target exchanges.

        Returns:
            Dictionary with vendor name as key and nested dict of WebSocket and REST fields
        """
        cursor = self.conn.cursor()

        # Get vendor IDs for our target exchanges
        query = """
        SELECT vendor_id, vendor_name
        FROM vendors
        WHERE vendor_name IN ('coinbase', 'kraken', 'binance', 'bitfinex')
        ORDER BY vendor_id
        """

        cursor.execute(query)
        vendors = cursor.fetchall()

        all_vendor_fields = {}

        for vendor in vendors:
            vendor_id = vendor['vendor_id']
            vendor_name = vendor['vendor_name']

            logger.info(f"Extracting fields for {vendor_name} (id={vendor_id})...")

            # Get WebSocket fields
            ws_fields = self.get_vendor_websocket_fields(vendor_id, vendor_name)

            # Get REST fields
            rest_fields = self.get_vendor_rest_fields(vendor_id, vendor_name)

            all_vendor_fields[vendor_name] = {
                'vendor_id': vendor_id,
                'websocket_fields': ws_fields,
                'rest_fields': rest_fields,
                'total_ws_fields': sum(len(f) for f in ws_fields.values()),
                'total_rest_fields': sum(len(f) for f in rest_fields.values())
            }

            logger.info(f"  Total for {vendor_name}: {all_vendor_fields[vendor_name]['total_ws_fields']} WS fields, {all_vendor_fields[vendor_name]['total_rest_fields']} REST fields")

        return all_vendor_fields

    def generate_summary_statistics(self, vendor_fields: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Generate summary statistics from extracted fields.

        Args:
            vendor_fields: Dictionary from extract_all_vendor_fields()

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_vendors': len(vendor_fields),
            'vendors': {},
            'overall_totals': {
                'total_websocket_fields': 0,
                'total_rest_fields': 0,
                'total_unique_field_paths': set()
            }
        }

        all_field_paths = set()

        for vendor_name, vendor_data in vendor_fields.items():
            # Collect all field paths for this vendor
            vendor_field_paths = set()

            for channel_name, fields in vendor_data['websocket_fields'].items():
                for field in fields:
                    full_path = f"{vendor_name}.websocket.{channel_name}.{field}"
                    vendor_field_paths.add(full_path)
                    all_field_paths.add(field)  # Add just the field path for unique counting

            for endpoint_key, fields in vendor_data['rest_fields'].items():
                for field in fields:
                    full_path = f"{vendor_name}.rest.{endpoint_key}.{field}"
                    vendor_field_paths.add(full_path)
                    all_field_paths.add(field)  # Add just the field path for unique counting

            summary['vendors'][vendor_name] = {
                'vendor_id': vendor_data['vendor_id'],
                'websocket_channels': len(vendor_data['websocket_fields']),
                'rest_endpoints': len(vendor_data['rest_fields']),
                'total_websocket_fields': vendor_data['total_ws_fields'],
                'total_rest_fields': vendor_data['total_rest_fields'],
                'total_fields': vendor_data['total_ws_fields'] + vendor_data['total_rest_fields'],
                'unique_field_paths_count': len(vendor_field_paths)
            }

            summary['overall_totals']['total_websocket_fields'] += vendor_data['total_ws_fields']
            summary['overall_totals']['total_rest_fields'] += vendor_data['total_rest_fields']

        summary['overall_totals']['total_fields'] = (
            summary['overall_totals']['total_websocket_fields'] +
            summary['overall_totals']['total_rest_fields']
        )
        summary['overall_totals']['total_unique_field_paths'] = len(all_field_paths)

        return summary

    def export_to_csv(self, vendor_fields: Dict[str, Dict], output_dir: Path):
        """
        Export field inventory to CSV files.

        Args:
            vendor_fields: Dictionary from extract_all_vendor_fields()
            output_dir: Directory to save CSV files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export per-vendor CSV
        for vendor_name, vendor_data in vendor_fields.items():
            csv_path = output_dir / f"{vendor_name}_field_inventory.csv"

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['source_type', 'source_name', 'field_path', 'vendor']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                # Write WebSocket fields
                for channel_name, fields in vendor_data['websocket_fields'].items():
                    for field in fields:
                        writer.writerow({
                            'source_type': 'websocket',
                            'source_name': channel_name,
                            'field_path': field,
                            'vendor': vendor_name
                        })

                # Write REST fields
                for endpoint_key, fields in vendor_data['rest_fields'].items():
                    for field in fields:
                        writer.writerow({
                            'source_type': 'rest',
                            'source_name': endpoint_key,
                            'field_path': field,
                            'vendor': vendor_name
                        })

            logger.info(f"Exported {vendor_name} field inventory to {csv_path}")

        # Export summary CSV
        summary_path = output_dir / "field_inventory_summary.csv"

        with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['vendor', 'websocket_channels', 'rest_endpoints',
                         'total_ws_fields', 'total_rest_fields', 'total_fields']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for vendor_name, vendor_data in vendor_fields.items():
                writer.writerow({
                    'vendor': vendor_name,
                    'websocket_channels': len(vendor_data['websocket_fields']),
                    'rest_endpoints': len(vendor_data['rest_fields']),
                    'total_ws_fields': vendor_data['total_ws_fields'],
                    'total_rest_fields': vendor_data['total_rest_fields'],
                    'total_fields': vendor_data['total_ws_fields'] + vendor_data['total_rest_fields']
                })

        logger.info(f"Exported summary to {summary_path}")

    def export_to_json(self, vendor_fields: Dict[str, Dict], output_dir: Path):
        """
        Export field inventory to JSON file.

        Args:
            vendor_fields: Dictionary from extract_all_vendor_fields()
            output_dir: Directory to save JSON file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Add summary statistics
        result = {
            'extracted_at': None,  # Will be set below
            'summary': self.generate_summary_statistics(vendor_fields),
            'vendor_fields': vendor_fields
        }

        import datetime
        result['extracted_at'] = datetime.datetime.utcnow().isoformat() + 'Z'

        json_path = output_dir / "field_inventory.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)

        logger.info(f"Exported field inventory to {json_path}")


def main():
    """Main entry point for field inventory extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract field inventory from vendor API specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all fields and save to default output directory
  python field_inventory.py

  # Extract and export to specific directory
  python field_inventory.py --output ./field_inventory

  # Export only to JSON format
  python field_inventory.py --format json

  # Export only to CSV format
  python field_inventory.py --format csv

  # Export to both formats
  python field_inventory.py --format both
        """
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=project_root / "output" / "field_inventory",
        help='Output directory for extracted field inventory (default: ./output/field_inventory)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    parser.add_argument(
        '--print-summary',
        action='store_true',
        default=True,
        help='Print summary to console (default: True)'
    )

    args = parser.parse_args()

    # Create extractor and process
    with FieldInventoryExtractor() as extractor:
        logger.info("Starting field inventory extraction...")

        # Extract all vendor fields
        vendor_fields = extractor.extract_all_vendor_fields()

        # Generate and print summary
        summary = extractor.generate_summary_statistics(vendor_fields)

        if args.print_summary:
            print("\n" + "="*60)
            print("FIELD INVENTORY SUMMARY")
            print("="*60)

            print(f"\nOverall Totals:")
            print(f"  Total vendors: {summary['total_vendors']}")
            print(f"  Total WebSocket fields: {summary['overall_totals']['total_websocket_fields']}")
            print(f"  Total REST fields: {summary['overall_totals']['total_rest_fields']}")
            print(f"  Total fields: {summary['overall_totals']['total_fields']}")
            print(f"  Unique field paths: {summary['overall_totals']['total_unique_field_paths']}")

            print(f"\nPer Vendor Breakdown:")
            for vendor_name, vendor_stats in summary['vendors'].items():
                print(f"\n  {vendor_name.upper()}:")
                print(f"    WebSocket channels: {vendor_stats['websocket_channels']}")
                print(f"    REST endpoints: {vendor_stats['rest_endpoints']}")
                print(f"    WebSocket fields: {vendor_stats['total_websocket_fields']}")
                print(f"    REST fields: {vendor_stats['total_rest_fields']}")
                print(f"    Total fields: {vendor_stats['total_fields']}")
                print(f"    Unique field paths: {vendor_stats['unique_field_paths_count']}")

            print("\n" + "="*60)

        # Export to requested formats
        args.output.mkdir(parents=True, exist_ok=True)

        if args.format in ['json', 'both']:
            extractor.export_to_json(vendor_fields, args.output)

        if args.format in ['csv', 'both']:
            extractor.export_to_csv(vendor_fields, args.output)

        logger.info(f"Field inventory extraction complete. Output saved to: {args.output}")


if __name__ == '__main__':
    main()
