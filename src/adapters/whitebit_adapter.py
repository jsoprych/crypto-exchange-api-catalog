# src/adapters/whitebit_adapter.py
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


class WhitebitAdapter(BaseVendorAdapter):
    """
    Template adapter for Whitebit Exchange API.

    Replace all occurrences of:
    - 'WhitebitAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Whitebit' with actual exchange name (e.g., 'Bybit')
    - 'https://whitebit.com' with actual REST API base URL
    - 'wss://whitebit.com/ws' with actual WebSocket URL
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
        Discover Whitebit REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Whitebit REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/api/v3/ping",
                "method": "GET",
                "authentication_required": False,
                "description": "Test connectivity to the REST API",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "serverTime": {"type": "integer", "description": "Unix timestamp in milliseconds"}
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(system_endpoints)

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/v3/exchangeInfo",
                "method": "GET",
                "authentication_required": False,
                "description": "Get exchange trading rules and symbol information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(product_endpoints)

        # Market data endpoints
        market_data_endpoints = [
            {
                "path": "/api/v3/ticker/24hr",
                "method": "GET",
                "authentication_required": False,
                "description": "24 hour rolling window price change statistics",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": False,
                        "description": "Trading pair symbol (e.g., BTCUSDT). If not provided, returns all symbols"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "priceChange": {"type": "string"},
                        "priceChangePercent": {"type": "string"},
                        "lastPrice": {"type": "string"},
                        "volume": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of depth levels (5, 10, 20, 50, 100, 500, 1000, 5000)",
                        "default": 100
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "lastUpdateId": {"type": "integer"},
                        "bids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 2
                            }
                        },
                        "asks": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 2
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/klines",
                "method": "GET",
                "authentication_required": False,
                "description": "Kline/candlestick data",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "interval": {
                        "type": "string",
                        "required": True,
                        "description": "Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of klines to return (1-1000)",
                        "default": 500
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 12,
                        "maxItems": 12
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trades list",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades to return (1-1000)",
                        "default": 500
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "price": {"type": "string"},
                            "qty": {"type": "string"},
                            "time": {"type": "integer"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(market_data_endpoints)

        # ============================================================================
        # 2. AUTHENTICATED ENDPOINTS (Phase 3 - Optional for initial implementation)
        # ============================================================================

        # Uncomment and implement when adding authenticated endpoint support
        """
        authenticated_endpoints = [
            {
                "path": "/api/v3/account",
                "method": "GET",
                "authentication_required": True,
                "description": "Account information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
            {
                "path": "/api/v3/order",
                "method": "POST",
                "authentication_required": True,
                "description": "Create new order",
                "query_parameters": {
                    "symbol": {"type": "string", "required": True},
                    "side": {"type": "string", "required": True, "enum": ["BUY", "SELL"]},
                    "type": {"type": "string", "required": True, "enum": ["LIMIT", "MARKET"]},
                    "quantity": {"type": "string", "required": True},
                    "price": {"type": "string", "required": False}  # Required for LIMIT orders
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
        ]
        endpoints.extend(authenticated_endpoints)
        """

        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # Some exchanges provide API endpoint listings. Example pattern:
        """
        try:
            # If exchange provides endpoint discovery endpoint
            discovery_url = f"{self.base_url}/api/v3/endpoints"
            response = self.http_client.get(discovery_url)

            for endpoint_info in response.get('endpoints', []):
                endpoint = {
                    "path": endpoint_info['path'],
                    "method": endpoint_info['method'],
                    "authentication_required": endpoint_info.get('auth_required', False),
                    "description": endpoint_info.get('description', ''),
                    "query_parameters": endpoint_info.get('params', {}),
                    "response_schema": endpoint_info.get('response_schema', {}),
                    "rate_limit_tier": endpoint_info.get('rate_limit', 'public')
                }
                endpoints.append(endpoint)

        except Exception as e:
            logger.warning(f"Dynamic endpoint discovery failed: {e}. Using static endpoints.")
        """

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Whitebit WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Whitebit WebSocket channels")

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
        Discover Whitebit trading products/symbols from live API.

        IMPORTANT: This method MUST make live API calls to fetch actual products.
        Do not hardcode products. Fetch from exchange's product endpoint.

        Implementation Steps:
        1. Call the exchange's product/info endpoint (/api/v4/public/markets)
        2. Parse the response to extract symbol information
        3. Map to our standard product format
        4. Handle pagination if needed
        5. Implement error handling and retry logic

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Whitebit products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # WhiteBIT endpoint: /api/v4/public/markets
            products_url = f"{self.base_url}/api/v4/public/markets"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON WHITEBIT FORMAT
            # ========================================================================

            products = []

            # WhiteBIT response format: array of market objects
            if not isinstance(response, list):
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Whitebit, expected array")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for market_info in response:
                try:
                    # Extract fields from WhiteBIT market object
                    symbol = market_info.get('name')
                    base_currency = market_info.get('stock')
                    quote_currency = market_info.get('money')

                    # Validate required fields
                    if not all([symbol, base_currency, quote_currency]):
                        logger.warning(f"Skipping market with missing required fields: {market_info}")
                        continue

                    # Status based on tradesEnabled field
                    trades_enabled = market_info.get('tradesEnabled', False)
                    status = 'online' if trades_enabled else 'offline'

                    # Trading limits/precision
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # minAmount field
                    if 'minAmount' in market_info:
                        try:
                            min_order_size = float(market_info['minAmount'])
                        except (ValueError, TypeError):
                            logger.debug(f"Could not parse minAmount: {market_info.get('minAmount')}")

                    # maxTotal field (optional)
                    if 'maxTotal' in market_info:
                        try:
                            max_order_size = float(market_info['maxTotal'])
                        except (ValueError, TypeError):
                            logger.debug(f"Could not parse maxTotal: {market_info.get('maxTotal')}")

                    # Price increment from moneyPrec (precision)
                    # moneyPrec is the number of decimal places for quote currency
                    if 'moneyPrec' in market_info:
                        try:
                            money_prec = int(market_info['moneyPrec'])
                            price_increment = 10 ** -money_prec
                        except (ValueError, TypeError):
                            logger.debug(f"Could not parse moneyPrec: {market_info.get('moneyPrec')}")

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency.upper() if base_currency else None,
                        "quote_currency": quote_currency.upper() if quote_currency else None,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": market_info  # Store full raw data
                    }

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse market {market_info.get('name', 'unknown')}: {e}")
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
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Whitebit: {e}")

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
