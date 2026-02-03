# src/adapters/deribit_adapter.py
"""
Template adapter for new cryptocurrency exchange implementations.

This file serves as a starting point for implementing new exchange adapters.
Copy this file to a new filename (e.g., `bybit_adapter.py`), rename the class,
and implement the three required abstract methods.

Key Principles:
1. Live API Discovery: Always fetch real data from the exchange API when possible
2. Documentation-First: Base implementations on official API documentation
3. Error Handling: Implement robust error handling with meaningful messages
4. Rate Limiting: Respect exchange rate limits in discovery process

Required Methods to Implement:
- discover_rest_endpoints(): Find all REST API endpoints
- discover_websocket_channels(): Map WebSocket channels and message formats
- discover_products(): Fetch live trading pairs/products from API

See CONTRIBUTING.md for detailed implementation guidelines.
"""

from typing import Dict, List, Any, Optional
from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DeribitAdapter(BaseVendorAdapter):
    """
    Template adapter for Deribit Exchange API.

    Replace all occurrences of:
    - 'DeribitAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Deribit' with actual exchange name (e.g., 'Bybit')
    - 'https://www.deribit.com/api/v2' with actual REST API base URL
    - 'wss://www.deribit.com/ws/api/v2' with actual WebSocket URL
    - Documentation URLs and endpoint patterns

    Configuration Example (add to config/settings.py):
    "[exchange_id]": {
        "enabled": True,
        "display_name": "[Exchange Display Name]",
        "base_url": "https://api.exchange.com",
        "websocket_url": "wss://ws.exchange.com",
        "documentation_url": "https://docs.exchange.com/api",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/api/v3/exchangeInfo",  # Example product endpoint
            "time": "/api/v3/time",              # Server time endpoint
        },
        "rate_limits": {
            "public": 10  # Requests per second (approximate)
        }
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Deribit REST API endpoints.

        Currently returns empty list as Deribit's REST API uses JSON-RPC over HTTP.
        TODO: Implement proper endpoint discovery when documentation is available.
        """
        logger.info("Discovering Deribit REST endpoints (placeholder)")
        return []


    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        '''
        Discover Deribit WebSocket channels.

        Currently returns empty list as Deribit's WebSocket API is not yet mapped.
        TODO: Implement proper channel discovery when documentation is available.
        '''
        logger.info('Discovering Deribit WebSocket channels (placeholder)')
        return []

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Deribit trading products/instruments from live API.

        Deribit uses JSON-RPC over HTTP. The /public/get_instruments endpoint
        returns all instruments (options, futures, spot) with their details.
        """
        logger.info("Discovering Deribit products from live API")

        try:
            # Deribit uses JSON-RPC over HTTP GET with query parameters
            # We'll fetch all instruments (no filter)
            url = f"{self.base_url}/public/get_instruments"
            logger.debug(f"Fetching instruments from: {url}")

            # Make GET request (Deribit accepts GET with query params)
            response = self.http_client.get(url)

            # Check JSON-RPC response structure
            if not isinstance(response, dict) or 'result' not in response:
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Deribit")

            instruments_data = response['result']
            if not isinstance(instruments_data, list):
                logger.error(f"Unexpected result format: {type(instruments_data)}")
                raise Exception(f"Unexpected result format from Deribit")

            products = []

            for instrument in instruments_data:
                try:
                    # Extract symbol (instrument_name)
                    symbol = instrument.get('instrument_name')

                    # Deribit may not have explicit base/quote currency fields
                    # Try to extract from price_index (e.g., "btc_usd")
                    price_index = instrument.get('price_index', '')
                    base_currency = None
                    quote_currency = None

                    if price_index and '_' in price_index:
                        parts = price_index.split('_')
                        if len(parts) >= 2:
                            base_currency = parts[0].upper()
                            quote_currency = parts[1].upper()

                    # Fallback: parse from instrument_name (e.g., "BTC-4FEB26-70000-C")
                    if not base_currency and symbol and '-' in symbol:
                        base_currency = symbol.split('-')[0]

                    # Status mapping
                    state = instrument.get('state', '').lower()
                    if state == 'open':
                        status = 'online'
                    elif state == 'closed':
                        status = 'offline'
                    else:
                        status = 'offline'

                    # Trading limits
                    min_order_size = None
                    price_increment = None

                    min_trade_amount = instrument.get('min_trade_amount')
                    if min_trade_amount is not None:
                        try:
                            min_order_size = float(min_trade_amount)
                        except (ValueError, TypeError):
                            pass

                    tick_size = instrument.get('tick_size')
                    if tick_size is not None:
                        try:
                            price_increment = float(tick_size)
                        except (ValueError, TypeError):
                            pass

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": None,  # Deribit doesn't provide max order size
                        "price_increment": price_increment,
                        "vendor_metadata": instrument  # Store full raw data
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"]]):
                        logger.warning(f"Skipping instrument with missing required fields: {instrument}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse instrument {instrument.get('instrument_name', 'unknown')}: {e}")
                    continue

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in API response")

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise Exception(f"Product discovery failed for Deribit: {e}")

    # ============================================================================
    # OPTIONAL HELPER METHODS
    # ============================================================================

    def get_candle_intervals(self) -> List[int]:
        """
        Get available candle intervals for this exchange.

        Returns:
            List of granularity values in seconds
        """
        # Common intervals in seconds
        # Adjust based on exchange documentation
        return [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 28800, 43200, 86400, 259200, 604800]

    def validate_endpoint(self, endpoint: Dict[str, Any]) -> bool:
        """
        Validate that an endpoint is accessible (optional override).

        Can be used to test endpoints during discovery.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            True if endpoint is accessible, False otherwise
        """
        try:
            url = self.base_url + endpoint['path']

            # Test with minimal parameters
            test_params = {}
            if 'query_parameters' in endpoint:
                # Build minimal valid parameters for testing
                for param_name, param_info in endpoint['query_parameters'].items():
                    if param_info.get('required', False):
                        # Provide dummy/default value for required parameters
                        if param_info.get('type') == 'string':
                            test_params[param_name] = 'test'
                        elif param_info.get('type') == 'integer':
                            test_params[param_name] = 1
                        elif 'enum' in param_info:
                            test_params[param_name] = param_info['enum'][0]

            # Make test request
            self.http_client.get(url, params=test_params)
            return True

        except Exception as e:
            logger.debug(f"Endpoint validation failed for {endpoint['path']}: {e}")
            return False

    def test_websocket_channel(self, channel: Dict[str, Any]) -> bool:
        """
        Test WebSocket channel connectivity (optional override).

        Can be implemented to actually connect and test WebSocket channels.

        Args:
            channel: Channel dictionary

        Returns:
            True if channel is accessible, False otherwise
        """
        # Basic implementation - override for actual WebSocket testing
        logger.debug(f"WebSocket test not implemented for {channel['channel_name']}")
        return True
