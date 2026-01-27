# src/discovery/spec_generator.py
"""
Vendor API specification generator.
Orchestrates the discovery process for vendor APIs.
"""

import time
from typing import Dict, Any, Optional

from src.adapters.base_adapter import BaseVendorAdapter
from src.adapters.coinbase_adapter import CoinbaseAdapter
from src.database.repository import SpecificationRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpecificationGenerator:
    """
    Orchestrates the API specification discovery process.
    """

    def __init__(self, repository: SpecificationRepository):
        """
        Initialize specification generator.

        Args:
            repository: Database repository instance
        """
        self.repository = repository

    def generate_specification(
        self,
        vendor_name: str,
        vendor_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete API specification for a vendor.

        Args:
            vendor_name: Vendor name
            vendor_config: Vendor configuration

        Returns:
            Dictionary with discovery statistics and results
        """
        logger.info(f"Starting API specification generation for {vendor_name}")
        start_time = time.time()

        # Add vendor_name to config
        vendor_config['vendor_name'] = vendor_name

        # Get or create vendor in database
        vendor_id = self.repository.get_or_create_vendor(vendor_config)

        # Start discovery run
        run_id = self.repository.start_discovery_run(
            vendor_id,
            discovery_method='live_api_probing'
        )

        try:
            # Create vendor adapter
            adapter = self._create_adapter(vendor_name, vendor_config)

            # Phase 1: Discover REST endpoints
            logger.info("Phase 1: Discovering REST endpoints")
            endpoints = adapter.discover_rest_endpoints()
            endpoint_ids = self._save_endpoints(vendor_id, endpoints, run_id)

            # Phase 2: Discover WebSocket channels
            logger.info("Phase 2: Discovering WebSocket channels")
            channels = adapter.discover_websocket_channels()
            channel_ids = self._save_channels(vendor_id, channels, run_id)

            # Phase 3: Discover products
            logger.info("Phase 3: Discovering products")
            products = adapter.discover_products()
            product_ids = self._save_products(vendor_id, products, run_id)

            # Phase 4: Link products to feeds
            logger.info("Phase 4: Linking products to endpoints and channels")
            self._link_product_feeds(
                vendor_name,
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )

            # Calculate statistics
            duration = time.time() - start_time
            stats = {
                'endpoints_discovered': len(endpoints),
                'websocket_channels_discovered': len(channels),
                'products_discovered': len(products)
            }

            # Mark discovery run as complete
            self.repository.complete_discovery_run(
                run_id,
                duration,
                stats,
                success=True
            )

            logger.info(
                f"Specification generation complete: "
                f"{stats['products_discovered']} products, "
                f"{stats['endpoints_discovered']} endpoints, "
                f"{stats['websocket_channels_discovered']} channels "
                f"in {duration:.2f}s"
            )

            return {
                'success': True,
                'run_id': run_id,
                'vendor_id': vendor_id,
                'duration': duration,
                **stats
            }

        except Exception as e:
            # Mark discovery run as failed
            duration = time.time() - start_time
            self.repository.complete_discovery_run(
                run_id,
                duration,
                {'endpoints_discovered': 0, 'websocket_channels_discovered': 0, 'products_discovered': 0},
                success=False,
                error_message=str(e)
            )

            logger.error(f"Specification generation failed: {e}")
            raise

    def _create_adapter(
        self,
        vendor_name: str,
        vendor_config: Dict[str, Any]
    ) -> BaseVendorAdapter:
        """
        Create appropriate adapter for vendor.

        Args:
            vendor_name: Vendor name
            vendor_config: Vendor configuration

        Returns:
            Vendor adapter instance
        """
        if vendor_name == 'coinbase':
            return CoinbaseAdapter(vendor_config)
        else:
            raise ValueError(f"Unknown vendor: {vendor_name}")

    def _save_endpoints(
        self,
        vendor_id: int,
        endpoints: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save REST endpoints to database.

        Args:
            vendor_id: Vendor ID
            endpoints: List of endpoint dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping endpoint paths to endpoint IDs
        """
        endpoint_ids = {}

        for endpoint in endpoints:
            endpoint_id = self.repository.save_rest_endpoint(
                vendor_id,
                endpoint,
                run_id
            )
            key = f"{endpoint['method']} {endpoint['path']}"
            endpoint_ids[key] = endpoint_id

            logger.debug(f"Saved endpoint: {key}")

        return endpoint_ids

    def _save_channels(
        self,
        vendor_id: int,
        channels: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save WebSocket channels to database.

        Args:
            vendor_id: Vendor ID
            channels: List of channel dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping channel names to channel IDs
        """
        channel_ids = {}

        for channel in channels:
            channel_id = self.repository.save_websocket_channel(
                vendor_id,
                channel,
                run_id
            )
            channel_ids[channel['channel_name']] = channel_id

            logger.debug(f"Saved channel: {channel['channel_name']}")

        return channel_ids

    def _save_products(
        self,
        vendor_id: int,
        products: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save products to database.

        Args:
            vendor_id: Vendor ID
            products: List of product dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping symbols to product IDs
        """
        product_ids = {}

        for product in products:
            product_id = self.repository.save_product(
                vendor_id,
                product,
                run_id
            )
            product_ids[product['symbol']] = product_id

            logger.debug(f"Saved product: {product['symbol']}")

        return product_ids

    def _link_product_feeds(
        self,
        vendor_name: str,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link products to their available endpoints and channels.

        Args:
            vendor_name: Vendor name
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: Vendor adapter instance
        """
        # Vendor-specific linking logic
        if vendor_name == 'coinbase':
            self._link_coinbase_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )

    def _link_coinbase_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: CoinbaseAdapter
    ):
        """
        Link Coinbase products to their feeds.

        Args:
            product_ids: Product IDs by symbol
            endpoint_ids: Endpoint IDs by key
            channel_ids: Channel IDs by name
            adapter: Coinbase adapter instance
        """
        # Get candle intervals
        candle_intervals = adapter.get_candle_intervals()

        # Link each product to available feeds
        for symbol, product_id in product_ids.items():
            # REST feeds
            # Ticker
            ticker_key = "GET /products/{product_id}/ticker"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Candles
            candles_key = "GET /products/{product_id}/candles"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles',
                    intervals=candle_intervals
                )

            # Trades
            trades_key = "GET /products/{product_id}/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Order book
            book_key = "GET /products/{product_id}/book"
            if book_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[book_key],
                    'orderbook'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                if channel_name != 'status':  # Status channel doesn't use product_ids
                    self.repository.link_product_to_ws_channel(
                        product_id,
                        channel_id
                    )

        logger.info(f"Linked {len(product_ids)} products to feeds")
