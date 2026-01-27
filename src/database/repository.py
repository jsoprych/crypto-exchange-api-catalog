# src/database/repository.py
"""
Database repository for vendor API specifications.
Provides data access layer for all database operations.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpecificationRepository:
    """
    Repository for vendor API specification data access.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    # ===========================================
    # VENDOR OPERATIONS
    # ===========================================

    def get_or_create_vendor(self, vendor_config: Dict[str, Any]) -> int:
        """
        Get existing vendor or create new one.

        Args:
            vendor_config: Vendor configuration dictionary

        Returns:
            vendor_id
        """
        vendor_name = vendor_config['vendor_name']

        # Check if vendor exists
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            (vendor_name,)
        )
        row = cursor.fetchone()

        if row:
            return row['vendor_id']

        # Create new vendor
        cursor = self.conn.execute("""
            INSERT INTO vendors (
                vendor_name, display_name, base_url,
                websocket_url, documentation_url, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            vendor_name,
            vendor_config.get('display_name', vendor_name),
            vendor_config.get('base_url'),
            vendor_config.get('websocket_url'),
            vendor_config.get('documentation_url'),
            'active'
        ))

        vendor_id = cursor.lastrowid
        self.conn.commit()

        logger.info(f"Created vendor: {vendor_name} (id={vendor_id})")
        return vendor_id

    def get_vendor_id(self, vendor_name: str) -> Optional[int]:
        """
        Get vendor ID by name.

        Args:
            vendor_name: Vendor name

        Returns:
            vendor_id or None if not found
        """
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            (vendor_name,)
        )
        row = cursor.fetchone()
        return row['vendor_id'] if row else None

    # ===========================================
    # DISCOVERY RUN OPERATIONS
    # ===========================================

    def start_discovery_run(
        self,
        vendor_id: int,
        discovery_method: str = 'hybrid'
    ) -> int:
        """
        Create a new discovery run record.

        Args:
            vendor_id: Vendor ID
            discovery_method: Discovery method used

        Returns:
            run_id
        """
        cursor = self.conn.execute("""
            INSERT INTO discovery_runs (
                vendor_id, discovery_method, success
            ) VALUES (?, ?, 0)
        """, (vendor_id, discovery_method))

        run_id = cursor.lastrowid
        self.conn.commit()

        logger.info(f"Started discovery run {run_id} for vendor_id={vendor_id}")
        return run_id

    def complete_discovery_run(
        self,
        run_id: int,
        duration_seconds: float,
        stats: Dict[str, int],
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Mark discovery run as complete with statistics.

        Args:
            run_id: Discovery run ID
            duration_seconds: Run duration
            stats: Statistics (endpoints_discovered, etc.)
            success: Whether run was successful
            error_message: Error message if failed
            metadata: Additional metadata
        """
        self.conn.execute("""
            UPDATE discovery_runs SET
                duration_seconds = ?,
                endpoints_discovered = ?,
                websocket_channels_discovered = ?,
                products_discovered = ?,
                success = ?,
                error_message = ?,
                metadata = ?
            WHERE run_id = ?
        """, (
            duration_seconds,
            stats.get('endpoints_discovered', 0),
            stats.get('websocket_channels_discovered', 0),
            stats.get('products_discovered', 0),
            1 if success else 0,
            error_message,
            json.dumps(metadata) if metadata else None,
            run_id
        ))

        self.conn.commit()

        status = "successfully" if success else "with errors"
        logger.info(f"Completed discovery run {run_id} {status}")

    # ===========================================
    # REST ENDPOINT OPERATIONS
    # ===========================================

    def save_rest_endpoint(
        self,
        vendor_id: int,
        endpoint_data: Dict[str, Any],
        run_id: int
    ) -> int:
        """
        Insert or update REST endpoint.

        Args:
            vendor_id: Vendor ID
            endpoint_data: Endpoint information
            run_id: Discovery run ID

        Returns:
            endpoint_id
        """
        # Check if endpoint exists
        cursor = self.conn.execute("""
            SELECT endpoint_id, first_discovered_run_id
            FROM rest_endpoints
            WHERE vendor_id = ? AND path = ? AND method = ?
        """, (vendor_id, endpoint_data['path'], endpoint_data['method']))

        existing = cursor.fetchone()

        if existing:
            # Update existing endpoint
            endpoint_id = existing['endpoint_id']
            first_discovered_run_id = existing['first_discovered_run_id']

            self.conn.execute("""
                UPDATE rest_endpoints SET
                    authentication_required = ?,
                    description = ?,
                    rate_limit_tier = ?,
                    path_parameters = ?,
                    query_parameters = ?,
                    request_schema = ?,
                    response_schema = ?,
                    vendor_metadata = ?,
                    last_validated_run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE endpoint_id = ?
            """, (
                endpoint_data.get('authentication_required', False),
                endpoint_data.get('description'),
                endpoint_data.get('rate_limit_tier'),
                json.dumps(endpoint_data.get('path_parameters')),
                json.dumps(endpoint_data.get('query_parameters')),
                json.dumps(endpoint_data.get('request_schema')),
                json.dumps(endpoint_data.get('response_schema')),
                json.dumps(endpoint_data.get('vendor_metadata')),
                run_id,
                endpoint_id
            ))
        else:
            # Insert new endpoint
            cursor = self.conn.execute("""
                INSERT INTO rest_endpoints (
                    vendor_id, path, method, authentication_required,
                    description, rate_limit_tier, path_parameters,
                    query_parameters, request_schema, response_schema,
                    vendor_metadata, first_discovered_run_id,
                    last_validated_run_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                vendor_id,
                endpoint_data['path'],
                endpoint_data['method'],
                endpoint_data.get('authentication_required', False),
                endpoint_data.get('description'),
                endpoint_data.get('rate_limit_tier'),
                json.dumps(endpoint_data.get('path_parameters')),
                json.dumps(endpoint_data.get('query_parameters')),
                json.dumps(endpoint_data.get('request_schema')),
                json.dumps(endpoint_data.get('response_schema')),
                json.dumps(endpoint_data.get('vendor_metadata')),
                run_id,
                run_id
            ))
            endpoint_id = cursor.lastrowid

        self.conn.commit()
        return endpoint_id

    # ===========================================
    # WEBSOCKET CHANNEL OPERATIONS
    # ===========================================

    def save_websocket_channel(
        self,
        vendor_id: int,
        channel_data: Dict[str, Any],
        run_id: int
    ) -> int:
        """
        Insert or update WebSocket channel.

        Args:
            vendor_id: Vendor ID
            channel_data: Channel information
            run_id: Discovery run ID

        Returns:
            channel_id
        """
        # Check if channel exists
        cursor = self.conn.execute("""
            SELECT channel_id
            FROM websocket_channels
            WHERE vendor_id = ? AND channel_name = ?
        """, (vendor_id, channel_data['channel_name']))

        existing = cursor.fetchone()

        if existing:
            # Update existing channel
            channel_id = existing['channel_id']

            self.conn.execute("""
                UPDATE websocket_channels SET
                    authentication_required = ?,
                    description = ?,
                    subscribe_format = ?,
                    unsubscribe_format = ?,
                    message_types = ?,
                    message_schema = ?,
                    vendor_metadata = ?,
                    last_validated_run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE channel_id = ?
            """, (
                channel_data.get('authentication_required', False),
                channel_data.get('description'),
                json.dumps(channel_data.get('subscribe_format')),
                json.dumps(channel_data.get('unsubscribe_format')),
                json.dumps(channel_data.get('message_types')),
                json.dumps(channel_data.get('message_schema')),
                json.dumps(channel_data.get('vendor_metadata')),
                run_id,
                channel_id
            ))
        else:
            # Insert new channel
            cursor = self.conn.execute("""
                INSERT INTO websocket_channels (
                    vendor_id, channel_name, authentication_required,
                    description, subscribe_format, unsubscribe_format,
                    message_types, message_schema, vendor_metadata,
                    first_discovered_run_id, last_validated_run_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                vendor_id,
                channel_data['channel_name'],
                channel_data.get('authentication_required', False),
                channel_data.get('description'),
                json.dumps(channel_data.get('subscribe_format')),
                json.dumps(channel_data.get('unsubscribe_format')),
                json.dumps(channel_data.get('message_types')),
                json.dumps(channel_data.get('message_schema')),
                json.dumps(channel_data.get('vendor_metadata')),
                run_id,
                run_id
            ))
            channel_id = cursor.lastrowid

        self.conn.commit()
        return channel_id

    # ===========================================
    # PRODUCT OPERATIONS
    # ===========================================

    def save_product(
        self,
        vendor_id: int,
        product_data: Dict[str, Any],
        run_id: int
    ) -> int:
        """
        Insert or update product.

        Args:
            vendor_id: Vendor ID
            product_data: Product information
            run_id: Discovery run ID

        Returns:
            product_id
        """
        # Check if product exists
        cursor = self.conn.execute("""
            SELECT product_id
            FROM products
            WHERE vendor_id = ? AND symbol = ?
        """, (vendor_id, product_data['symbol']))

        existing = cursor.fetchone()

        if existing:
            # Update existing product
            product_id = existing['product_id']

            self.conn.execute("""
                UPDATE products SET
                    base_currency = ?,
                    quote_currency = ?,
                    status = ?,
                    min_order_size = ?,
                    max_order_size = ?,
                    price_increment = ?,
                    vendor_metadata = ?,
                    last_validated_run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            """, (
                product_data['base_currency'],
                product_data['quote_currency'],
                product_data.get('status', 'online'),
                product_data.get('min_order_size'),
                product_data.get('max_order_size'),
                product_data.get('price_increment'),
                json.dumps(product_data.get('vendor_metadata')),
                run_id,
                product_id
            ))
        else:
            # Insert new product
            cursor = self.conn.execute("""
                INSERT INTO products (
                    vendor_id, symbol, base_currency, quote_currency,
                    status, min_order_size, max_order_size, price_increment,
                    vendor_metadata, first_discovered_run_id, last_validated_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id,
                product_data['symbol'],
                product_data['base_currency'],
                product_data['quote_currency'],
                product_data.get('status', 'online'),
                product_data.get('min_order_size'),
                product_data.get('max_order_size'),
                product_data.get('price_increment'),
                json.dumps(product_data.get('vendor_metadata')),
                run_id,
                run_id
            ))
            product_id = cursor.lastrowid

        self.conn.commit()
        return product_id

    def link_product_to_endpoint(
        self,
        product_id: int,
        endpoint_id: int,
        feed_type: str,
        intervals: Optional[List[int]] = None
    ):
        """
        Link a product to a REST endpoint (feed).

        Args:
            product_id: Product ID
            endpoint_id: Endpoint ID
            feed_type: Type of feed (ticker, candles, trades, orderbook)
            intervals: List of intervals for candles (optional)
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO product_rest_feeds (
                product_id, endpoint_id, feed_type, intervals
            ) VALUES (?, ?, ?, ?)
        """, (product_id, endpoint_id, feed_type, json.dumps(intervals)))

        self.conn.commit()

    def link_product_to_ws_channel(
        self,
        product_id: int,
        channel_id: int
    ):
        """
        Link a product to a WebSocket channel.

        Args:
            product_id: Product ID
            channel_id: Channel ID
        """
        self.conn.execute("""
            INSERT OR IGNORE INTO product_ws_channels (
                product_id, channel_id
            ) VALUES (?, ?)
        """, (product_id, channel_id))

        self.conn.commit()
