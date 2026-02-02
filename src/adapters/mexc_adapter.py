# src/adapters/template_adapter.py
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


class MexcAdapter(BaseVendorAdapter):
    """
    MEXC exchange adapter.

    This adapter implements discovery for MEXC cryptocurrency exchange.

    Configuration (add to config/settings.py):
    "mexc": {
        "enabled": True,
        "display_name": "MEXC Exchange",
        "base_url": "https://api.mexc.com",
        "websocket_url": "wss://wbs.mexc.com/ws",
        "documentation_url": "https://mexcdevelop.github.io/apidocs/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "exchange_info": "/api/v3/exchangeInfo",
            "time": "/api/v3/time",
            "tickers": "/api/v3/ticker/24hr"
        },
        "rate_limits": {
            "public": 20  # Requests per second (approximate)
        }
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover MEXC REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering MEXC REST endpoints")

        endpoints = []

        # Market data endpoints (public)
        market_endpoints = [
            {
                "path": "/api/v3/ping",
                "method": "GET",
                "authentication_required": False,
                "description": "Test connectivity to the Rest API",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Test connectivity and get server time",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/exchangeInfo",
                "method": "GET",
                "authentication_required": False,
                "description": "Current exchange trading rules and symbol information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth",
                "query_parameters": {
                    "symbol": "string (required)",
                    "limit": "integer (5, 10, 20, 50, 100, 500, 1000, 5000)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trades list",
                "query_parameters": {
                    "symbol": "string (required)",
                    "limit": "integer (default 500, max 1000)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/klines",
                "method": "GET",
                "authentication_required": False,
                "description": "Kline/candlestick bars for a symbol",
                "query_parameters": {
                    "symbol": "string (required)",
                    "interval": "string (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)",
                    "limit": "integer (default 500, max 1000)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/24hr",
                "method": "GET",
                "authentication_required": False,
                "description": "24 hour rolling window price change statistics",
                "query_parameters": {
                    "symbol": "string (optional - omit for all symbols)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/price",
                "method": "GET",
                "authentication_required": False,
                "description": "Latest price for a symbol",
                "query_parameters": {
                    "symbol": "string (optional)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/bookTicker",
                "method": "GET",
                "authentication_required": False,
                "description": "Best price/qty on the order book",
                "query_parameters": {
                    "symbol": "string (optional)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover MEXC WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering MEXC WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public)
        # ============================================================================

        # Ticker channel
        channels.append({
            "channel_name": "ticker",
            "authentication_required": False,
            "description": "Real-time ticker updates for trading pairs",
            "subscribe_format": {
                "type": "subscribe",
                "method": "SUBSCRIPTION",
                "params": ["ticker@<symbol>"],  # Replace <symbol> with actual pair
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "UNSUBSCRIBE",
                "params": ["ticker@<symbol>"],
                "id": 2
            },
            "message_types": ["ticker", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "e": {"type": "string", "description": "Event type"},
                    "E": {"type": "integer", "description": "Event time"},
                    "s": {"type": "string", "description": "Symbol"},
                    "p": {"type": "string", "description": "Price change"},
                    "P": {"type": "string", "description": "Price change percent"},
                    "c": {"type": "string", "description": "Last price"},
                    "v": {"type": "string", "description": "Volume"},
                    "q": {"type": "string", "description": "Quote volume"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "ticker@{}",  # {} will be replaced with symbol
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Order book channel
        channels.append({
            "channel_name": "depth",
            "authentication_required": False,
            "description": "Real-time order book updates (level 2)",
            "subscribe_format": {
                "type": "subscribe",
                "method": "SUBSCRIPTION",
                "params": ["depth@<symbol>"],
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "UNSUBSCRIBE",
                "params": ["depth@<symbol>"],
                "id": 2
            },
            "message_types": ["depthUpdate", "snapshot", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "e": {"type": "string", "description": "Event type"},
                    "E": {"type": "integer", "description": "Event time"},
                    "s": {"type": "string", "description": "Symbol"},
                    "U": {"type": "integer", "description": "First update ID"},
                    "u": {"type": "integer", "description": "Final update ID"},
                    "b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "description": "Bids"
                    },
                    "a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "description": "Asks"
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "depth@{}",
                "levels": "full",  # or "partial" for top N levels
                "update_type": "delta"  # or "snapshot" for full book
            }
        })

        # Trade channel
        channels.append({
            "channel_name": "trade",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "type": "subscribe",
                "method": "SUBSCRIPTION",
                "params": ["trade@<symbol>"],
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "UNSUBSCRIBE",
                "params": ["trade@<symbol>"],
                "id": 2
            },
            "message_types": ["trade", "aggregateTrade", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "e": {"type": "string", "description": "Event type"},
                    "E": {"type": "integer", "description": "Event time"},
                    "s": {"type": "string", "description": "Symbol"},
                    "t": {"type": "integer", "description": "Trade ID"},
                    "p": {"type": "string", "description": "Price"},
                    "q": {"type": "string", "description": "Quantity"},
                    "m": {"type": "boolean", "description": "Is buyer maker?"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "trade@{}",
                "trade_type": "individual",  # or "aggregate" for combined trades
                "include_maker_info": True
            }
        })

        # Kline/candlestick channel
        channels.append({
            "channel_name": "kline",
            "authentication_required": False,
            "description": "Real-time candlestick updates",
            "subscribe_format": {
                "type": "subscribe",
                "method": "SUBSCRIPTION",
                "params": ["kline_<interval>@<symbol>"],  # e.g., kline_1m@BTCUSDT
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "UNSUBSCRIBE",
                "params": ["kline_<interval>@<symbol>"],
                "id": 2
            },
            "message_types": ["kline", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "e": {"type": "string", "description": "Event type"},
                    "E": {"type": "integer", "description": "Event time"},
                    "s": {"type": "string", "description": "Symbol"},
                    "k": {
                        "type": "object",
                        "properties": {
                            "t": {"type": "integer", "description": "Kline start time"},
                            "T": {"type": "integer", "description": "Kline close time"},
                            "o": {"type": "string", "description": "Open price"},
                            "c": {"type": "string", "description": "Close price"},
                            "h": {"type": "string", "description": "High price"},
                            "l": {"type": "string", "description": "Low price"},
                            "v": {"type": "string", "description": "Volume"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "kline_{}@{}",  # interval then symbol
                "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"],
                "update_frequency": "interval-based"
            }
        })

        # ============================================================================
        # 2. HEARTBEAT/CONNECTION MANAGEMENT
        # ============================================================================

        channels.append({
            "channel_name": "heartbeat",
            "authentication_required": False,
            "description": "Connection heartbeat/ping-pong messages",
            "subscribe_format": {
                "type": "subscribe",
                "method": "LISTEN",
                "params": ["heartbeat"]
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "UNLISTEN",
                "params": ["heartbeat"]
            },
            "message_types": ["heartbeat", "pong", "connection"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type"},
                    "time": {"type": "integer", "description": "Timestamp"}
                }
            },
            "vendor_metadata": {
                "keepalive_interval": 30000,  # milliseconds
                "auto_reconnect": True
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account updates (balance changes, orders, etc.)",
            "subscribe_format": {
                "type": "auth",
                "method": "LOGIN",
                "params": ["api_key", "signature", "timestamp"]
            },
            "message_types": ["outboundAccountInfo", "executionReport", "balanceUpdate"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "requires_signature": True,
                "update_types": ["balance", "order", "trade"]
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover MEXC trading products/symbols from live API.

        IMPORTANT: This method MUST make live API calls to fetch actual products.
        Do not hardcode products. Fetch from exchange's product endpoint.

        Implementation Steps:
        1. Call the exchange's product/info endpoint (e.g., /api/v3/exchangeInfo)
        2. Parse the response to extract symbol information
        3. Map to our standard product format
        4. Handle pagination if needed
        5. Implement error handling and retry logic

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering MEXC products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # Most exchanges have an endpoint like /api/v3/exchangeInfo or /products
            # Check the exchange documentation for the correct endpoint
            products_url = f"{self.base_url}/api/v3/exchangeInfo"

            # If the exchange uses a different endpoint, update this:
            # products_url = f"{self.base_url}/products"
            # products_url = f"{self.base_url}/v2/public/symbols"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASON ON EXCHANGE FORMAT
            # ========================================================================

            products = []

            # Common response format patterns:
            # Pattern 1: Binance-style (response['symbols'] contains list)
            if 'symbols' in response:
                symbols_data = response['symbols']
            # Pattern 2: Direct array response
            elif isinstance(response, list):
                symbols_data = response
            # Pattern 3: Nested under 'data' or 'result'
            elif 'data' in response:
                symbols_data = response['data']
            elif 'result' in response:
                symbols_data = response['result']
            else:
                # Default to trying to use the response directly
                symbols_data = response

            # Ensure we have an iterable
            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                raise Exception(f"Unexpected response format from MEXC")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for symbol_info in symbols_data:
                try:
                    # Extract common fields with fallbacks for different exchange formats

                    # Symbol/ID field (different exchanges use different keys)
                    symbol = (
                        symbol_info.get('symbol') or
                        symbol_info.get('id') or
                        symbol_info.get('name') or
                        symbol_info.get('pair')
                    )

                    # Base currency (what you're buying/selling)
                    base_currency = (
                        symbol_info.get('baseAsset') or
                        symbol_info.get('base_currency') or
                        symbol_info.get('base') or
                        symbol_info.get('baseCurrency')
                    )

                    # Quote currency (what you're trading with)
                    quote_currency = (
                        symbol_info.get('quoteAsset') or
                        symbol_info.get('quote_currency') or
                        symbol_info.get('quote') or
                        symbol_info.get('quoteCurrency')
                    )

                    # Status (trading availability)
                    status_raw = (
                        symbol_info.get('status') or
                        symbol_info.get('state') or
                        symbol_info.get('trading') or
                        symbol_info.get('active')
                    )

                    # Normalize status to our standard values
                    if status_raw in ['TRADING', 'trading', 'online', 'enabled', True]:
                        status = 'online'
                    elif status_raw in ['HALT', 'halted', 'offline', 'disabled', False]:
                        status = 'offline'
                    elif status_raw in ['BREAK', 'delisted', 'expired']:
                        status = 'delisted'
                    else:
                        status = 'offline'  # Default if unknown

                    # Trading limits/precision (if available)
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Try to extract from various exchange formats
                    if 'filters' in symbol_info:
                        for filter_item in symbol_info.get('filters', []):
                            filter_type = filter_item.get('filterType')
                            if filter_type == 'LOT_SIZE':
                                min_order_size = float(filter_item.get('minQty', 0))
                                max_order_size = float(filter_item.get('maxQty', 0))
                            elif filter_type == 'PRICE_FILTER':
                                price_increment = float(filter_item.get('tickSize', 0))

                    # Alternative field names
                    if min_order_size is None:
                        min_order_size = float(symbol_info.get('base_min_size', 0)) if symbol_info.get('base_min_size') else None
                    if max_order_size is None:
                        max_order_size = float(symbol_info.get('base_max_size', 0)) if symbol_info.get('base_max_size') else None
                    if price_increment is None:
                        price_increment = float(symbol_info.get('quote_increment', 0)) if symbol_info.get('quote_increment') else None

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": symbol_info  # Store full raw data
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse product {symbol_info.get('symbol', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in API response")

            logger.info(f"Discovered {len(products)} products")

            # Optional: Filter to only online products if needed
            # online_products = [p for p in products if p['status'] == 'online']
            # logger.info(f"Online products: {len(online_products)}")

            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for MEXC: {e}")

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
