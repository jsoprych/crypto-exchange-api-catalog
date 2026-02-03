# src/adapters/phemex_adapter.py
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


class PhemexAdapter(BaseVendorAdapter):
    """
    Template adapter for Phemex Exchange API.

    Replace all occurrences of:
    - 'PhemexAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Phemex' with actual exchange name (e.g., 'Bybit')
    - 'https://api.phemex.com' with actual REST API base URL
    - 'wss://ws.phemex.com' with actual WebSocket URL
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
        Discover Phemex REST API endpoints.

        Currently returns empty list as Phemex's REST API requires further research.
        TODO: Implement proper endpoint discovery when documentation is available.
        """
        logger.info("Discovering Phemex REST endpoints (placeholder)")
        return []

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        '''
        Discover Phemex WebSocket channels.

        Currently returns empty list as Phemex's WebSocket API is not yet mapped.
        TODO: Implement proper channel discovery when documentation is available.
        '''
        logger.info('Discovering Phemex WebSocket channels (placeholder)')
        return []

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Phemex trading products/symbols from live API.

        Phemex provides products through the /public/products endpoint.
        Returns spot and perpetual products with detailed metadata.

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Phemex products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # Phemex uses /public/products endpoint
            products_url = f"{self.base_url}/public/products"
            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE
            # ========================================================================

            # Check response structure
            if not isinstance(response, dict) or 'data' not in response:
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Phemex")

            data = response['data']
            if 'products' not in data:
                logger.error(f"Missing 'products' in response data: {list(data.keys())}")
                raise Exception(f"Missing products data in Phemex response")

            raw_products = data['products']
            if not isinstance(raw_products, list):
                logger.error(f"Unexpected products format: {type(raw_products)}")
                raise Exception(f"Unexpected products format from Phemex")

            products = []

            # ========================================================================
            # 3. PROCESS EACH PRODUCT
            # ========================================================================

            for prod in raw_products:
                try:
                    # Extract symbol (e.g., "BTCUSD", "sBTCUSDT", "cETHUSD")
                    symbol = prod.get('symbol')
                    if not symbol:
                        logger.warning(f"Skipping product with missing symbol: {prod}")
                        continue

                    # Determine product type
                    product_type = prod.get('type', '').lower()

                    # Determine base and quote currencies based on product type and symbol
                    base_currency = None
                    quote_currency = None

                    if product_type == 'spot':
                        # Spot products: symbol starts with 's' (e.g., sBTCUSDT)
                        # Remove 's' prefix and split
                        clean_symbol = symbol[1:] if symbol.startswith('s') else symbol
                        # Try to extract from quoteCurrency field
                        quote_currency = prod.get('quoteCurrency')
                        # Base currency might be inferred from symbol
                        if quote_currency and clean_symbol.endswith(quote_currency):
                            base_currency = clean_symbol[:-len(quote_currency)]

                    elif product_type == 'perpetual':
                        # Perpetual products: may have settleCurrency and quoteCurrency
                        settle_currency = prod.get('settleCurrency')
                        quote_currency = prod.get('quoteCurrency')

                        if settle_currency and quote_currency:
                            base_currency = settle_currency
                        elif symbol and '_' in symbol:
                            # Some perpetuals use underscore (e.g., BTC_USD)
                            parts = symbol.split('_')
                            if len(parts) >= 2:
                                base_currency = parts[0]
                                quote_currency = parts[1]

                    # Fallback: try to parse from symbol
                    if not base_currency and symbol:
                        # Remove 's' or 'c' prefix
                        clean_symbol = symbol[1:] if symbol.startswith(('s', 'c')) else symbol
                        # Look for currency pairs (USD, USDT, BTC, ETH, etc.)
                        # This is a simple heuristic
                        if clean_symbol.endswith('USDT'):
                            base_currency = clean_symbol[:-4]
                            quote_currency = 'USDT'
                        elif clean_symbol.endswith('USD'):
                            base_currency = clean_symbol[:-3]
                            quote_currency = 'USD'
                        elif clean_symbol.endswith('BTC'):
                            base_currency = clean_symbol[:-3]
                            quote_currency = 'BTC'

                    # Status mapping
                    status_raw = prod.get('status', '').lower()
                    if status_raw == 'listed':
                        status = 'online'
                    elif status_raw in ['halt', 'halted', 'unlisted']:
                        status = 'offline'
                    elif status_raw in ['delisted', 'expired']:
                        status = 'delisted'
                    else:
                        status = 'offline'

                    # Trading limits/precision
                    min_order_size = None
                    price_increment = None

                    # Extract from tickSize and lotSize
                    tick_size = prod.get('tickSize')
                    lot_size = prod.get('lotSize')

                    if tick_size is not None:
                        try:
                            price_increment = float(tick_size)
                        except (ValueError, TypeError):
                            pass

                    if lot_size is not None:
                        try:
                            min_order_size = float(lot_size)
                        except (ValueError, TypeError):
                            pass

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": None,  # Phemex doesn't provide max order size
                        "price_increment": price_increment,
                        "vendor_metadata": prod  # Store full raw data
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {prod}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse product {prod.get('symbol', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in API response")

            logger.info(f"Discovered {len(products)} products")

            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise Exception(f"Product discovery failed for Phemex: {e}")

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
