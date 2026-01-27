# src/export/json_exporter.py
"""
JSON export functionality for vendor API specifications.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from config.settings import OUTPUT_CONFIG
from src.utils.naming import convert_dict_keys
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """
    Export vendor API specifications from database to JSON format.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize JSON exporter.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def export_vendor_spec(
        self,
        vendor_name: str,
        naming_convention: str = OUTPUT_CONFIG['naming_convention'],
        include_metadata: bool = OUTPUT_CONFIG['include_vendor_metadata']
    ) -> Dict[str, Any]:
        """
        Export complete vendor specification as dictionary.

        Args:
            vendor_name: Vendor name to export
            naming_convention: 'snake_case' or 'camelCase'
            include_metadata: Include vendor-specific metadata

        Returns:
            Complete specification dictionary
        """
        logger.info(f"Exporting specification for {vendor_name}")

        # Get vendor info
        vendor = self._get_vendor_info(vendor_name)
        if not vendor:
            raise ValueError(f"Vendor not found: {vendor_name}")

        # Build specification
        spec = {
            "spec_metadata": {
                "vendor": vendor_name,
                "display_name": vendor['display_name'],
                "spec_version": OUTPUT_CONFIG['schema_version'],
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "naming_convention": naming_convention,
                "base_url": vendor['base_url'],
                "websocket_url": vendor['websocket_url'],
                "documentation_url": vendor['documentation_url']
            },
            "rest_api": {
                "base_url": vendor['base_url'],
                "endpoints": self._export_rest_endpoints(vendor['vendor_id'], include_metadata)
            },
            "websocket_api": {
                "url": vendor['websocket_url'],
                "channels": self._export_websocket_channels(vendor['vendor_id'], include_metadata)
            },
            "products": self._export_products(vendor['vendor_id'], include_metadata)
        }

        # Convert to desired naming convention
        if naming_convention != 'snake_case':
            spec = convert_dict_keys(spec, naming_convention)

        logger.info(f"Exported specification for {vendor_name}")
        return spec

    def export_to_file(
        self,
        spec: Dict[str, Any],
        output_path: Path,
        pretty_print: bool = OUTPUT_CONFIG['pretty_print']
    ):
        """
        Write specification to JSON file.

        Args:
            spec: Specification dictionary
            output_path: Output file path
            pretty_print: Format JSON with indentation
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            if pretty_print:
                json.dump(spec, f, indent=OUTPUT_CONFIG['indent'], sort_keys=False)
            else:
                json.dump(spec, f)

        logger.info(f"Specification written to {output_path}")

    def _get_vendor_info(self, vendor_name: str) -> Optional[Dict]:
        """
        Get vendor information from database.

        Args:
            vendor_name: Vendor name

        Returns:
            Vendor info dictionary or None
        """
        cursor = self.conn.execute("""
            SELECT vendor_id, vendor_name, display_name, base_url,
                   websocket_url, documentation_url, status
            FROM vendors
            WHERE vendor_name = ?
        """, (vendor_name,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def _export_rest_endpoints(
        self,
        vendor_id: int,
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """
        Export REST endpoints for vendor.

        Args:
            vendor_id: Vendor ID
            include_metadata: Include vendor metadata

        Returns:
            List of endpoint dictionaries
        """
        cursor = self.conn.execute("""
            SELECT path, method, authentication_required, description,
                   rate_limit_tier, path_parameters, query_parameters,
                   response_schema, vendor_metadata
            FROM rest_endpoints
            WHERE vendor_id = ? AND status = 'active'
            ORDER BY path, method
        """, (vendor_id,))

        endpoints = []
        for row in cursor.fetchall():
            endpoint = {
                "path": row['path'],
                "method": row['method'],
                "authentication_required": bool(row['authentication_required']),
                "description": row['description'],
                "rate_limit_tier": row['rate_limit_tier']
            }

            # Parse JSON fields
            if row['path_parameters']:
                endpoint['path_parameters'] = json.loads(row['path_parameters'])

            if row['query_parameters']:
                endpoint['query_parameters'] = json.loads(row['query_parameters'])

            if row['response_schema']:
                endpoint['response_schema'] = json.loads(row['response_schema'])

            if include_metadata and row['vendor_metadata']:
                endpoint['vendor_metadata'] = json.loads(row['vendor_metadata'])

            endpoints.append(endpoint)

        return endpoints

    def _export_websocket_channels(
        self,
        vendor_id: int,
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """
        Export WebSocket channels for vendor.

        Args:
            vendor_id: Vendor ID
            include_metadata: Include vendor metadata

        Returns:
            List of channel dictionaries
        """
        cursor = self.conn.execute("""
            SELECT channel_name, authentication_required, description,
                   subscribe_format, unsubscribe_format, message_types,
                   message_schema, vendor_metadata
            FROM websocket_channels
            WHERE vendor_id = ? AND status = 'active'
            ORDER BY channel_name
        """, (vendor_id,))

        channels = []
        for row in cursor.fetchall():
            channel = {
                "channel_name": row['channel_name'],
                "authentication_required": bool(row['authentication_required']),
                "description": row['description']
            }

            # Parse JSON fields
            if row['subscribe_format']:
                channel['subscribe_format'] = json.loads(row['subscribe_format'])

            if row['unsubscribe_format']:
                channel['unsubscribe_format'] = json.loads(row['unsubscribe_format'])

            if row['message_types']:
                channel['message_types'] = json.loads(row['message_types'])

            if row['message_schema']:
                channel['message_schema'] = json.loads(row['message_schema'])

            if include_metadata and row['vendor_metadata']:
                channel['vendor_metadata'] = json.loads(row['vendor_metadata'])

            channels.append(channel)

        return channels

    def _export_products(
        self,
        vendor_id: int,
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """
        Export products with their feeds for vendor.

        Args:
            vendor_id: Vendor ID
            include_metadata: Include vendor metadata

        Returns:
            List of product dictionaries with feeds
        """
        cursor = self.conn.execute("""
            SELECT product_id, symbol, base_currency, quote_currency,
                   status, min_order_size, max_order_size, price_increment,
                   vendor_metadata
            FROM products
            WHERE vendor_id = ? AND status = 'online'
            ORDER BY symbol
        """, (vendor_id,))

        products = []
        for row in cursor.fetchall():
            product = {
                "symbol": row['symbol'],
                "base_currency": row['base_currency'],
                "quote_currency": row['quote_currency'],
                "status": row['status'],
                "min_order_size": row['min_order_size'],
                "max_order_size": row['max_order_size'],
                "price_increment": row['price_increment']
            }

            # Get REST feeds for this product
            product['available_rest_feeds'] = self._get_product_rest_feeds(
                row['product_id']
            )

            # Get WebSocket channels for this product
            product['available_ws_channels'] = self._get_product_ws_channels(
                row['product_id']
            )

            if include_metadata and row['vendor_metadata']:
                product['vendor_metadata'] = json.loads(row['vendor_metadata'])

            products.append(product)

        return products

    def _get_product_rest_feeds(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Get REST feeds for a product.

        Args:
            product_id: Product ID

        Returns:
            List of feed dictionaries
        """
        cursor = self.conn.execute("""
            SELECT e.path, e.method, prf.feed_type, prf.intervals
            FROM product_rest_feeds prf
            JOIN rest_endpoints e ON prf.endpoint_id = e.endpoint_id
            WHERE prf.product_id = ?
            ORDER BY prf.feed_type
        """, (product_id,))

        feeds = []
        for row in cursor.fetchall():
            feed = {
                "type": row['feed_type'],
                "endpoint": row['path'],
                "method": row['method']
            }

            if row['intervals']:
                feed['intervals'] = json.loads(row['intervals'])

            feeds.append(feed)

        return feeds

    def _get_product_ws_channels(self, product_id: int) -> List[str]:
        """
        Get WebSocket channels for a product.

        Args:
            product_id: Product ID

        Returns:
            List of channel names
        """
        cursor = self.conn.execute("""
            SELECT w.channel_name
            FROM product_ws_channels pwc
            JOIN websocket_channels w ON pwc.channel_id = w.channel_id
            WHERE pwc.product_id = ?
            ORDER BY w.channel_name
        """, (product_id,))

        return [row['channel_name'] for row in cursor.fetchall()]
