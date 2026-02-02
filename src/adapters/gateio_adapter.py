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


class GateioAdapter(BaseVendorAdapter):
    """
    Template adapter for Gate.io Exchange API.

    Replace all occurrences of:
    - 'TemplateAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Gate.io' with actual exchange name (e.g., 'Bybit')
    - 'https://api.gateio.ws' with actual REST API base URL
    - 'wss://ws.gateio.io/v3' with actual WebSocket URL
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
        Discover Gate.io REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Gate.io REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/api/v4/spot/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get Gate.io server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "server_time": {"type": "integer", "description": "Unix timestamp in milliseconds"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v4/spot/currencies",
                "method": "GET",
                "authentication_required": False,
                "description": "Get all supported currencies",
                "query_parameters": {},
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "currency": {"type": "string"},
                            "name": {"type": "string"},
                            "delisted": {"type": "boolean"},
                            "withdraw_disabled": {"type": "boolean"},
                            "withdraw_delayed": {"type": "boolean"},
                            "deposit_disabled": {"type": "boolean"},
                            "trade_disabled": {"type": "boolean"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(system_endpoints)

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/v4/spot/currency_pairs",
                "method": "GET",
                "authentication_required": False,
                "description": "Get all supported currency pairs",
                "query_parameters": {},
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "base": {"type": "string"},
                            "quote": {"type": "string"},
                            "fee": {"type": "string"},
                            "min_base_amount": {"type": "string"},
                            "min_quote_amount": {"type": "string"},
                            "amount_precision": {"type": "integer"},
                            "precision": {"type": "integer"},
                            "trade_status": {"type": "string"},
                            "sell_start": {"type": "integer"},
                            "buy_start": {"type": "integer"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(product_endpoints)

        # Market data endpoints
        market_data_endpoints = [
            {
                "path": "/api/v4/spot/tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker information for all trading pairs",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": False,
                        "description": "Currency pair (e.g., BTC_USDT). If not provided, returns all pairs"
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "currency_pair": {"type": "string"},
                            "last": {"type": "string"},
                            "lowest_ask": {"type": "string"},
                            "highest_bid": {"type": "string"},
                            "change_percentage": {"type": "string"},
                            "base_volume": {"type": "string"},
                            "quote_volume": {"type": "string"},
                            "high_24h": {"type": "string"},
                            "low_24h": {"type": "string"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v4/spot/order_book",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., BTC_USDT)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of depth levels (1-50)",
                        "default": 10
                    },
                    "with_id": {
                        "type": "boolean",
                        "required": False,
                        "description": "Whether to include order ID",
                        "default": False
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "current": {"type": "integer"},
                        "update": {"type": "integer"},
                        "asks": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 2
                            }
                        },
                        "bids": {
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
                "path": "/api/v4/spot/candlesticks",
                "method": "GET",
                "authentication_required": False,
                "description": "Candlestick data",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., BTC_USDT)"
                    },
                    "interval": {
                        "type": "string",
                        "required": True,
                        "description": "Candle interval (10s, 1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 7d, 30d)",
                        "enum": ["10s", "1m", "5m", "15m", "30m", "1h", "4h", "8h", "1d", "7d", "30d"]
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of candles to return (1-1000)",
                        "default": 100
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 6,
                        "maxItems": 6,
                        "description": "[timestamp, quote_volume, close, high, low, open, base_volume]"
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v4/spot/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trades list",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., BTC_USDT)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades to return (1-1000)",
                        "default": 100
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "create_time": {"type": "string"},
                            "create_time_ms": {"type": "string"},
                            "side": {"type": "string"},
                            "amount": {"type": "string"},
                            "price": {"type": "string"}
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
                "path": "/api/v4/spot/accounts",
                "method": "GET",
                "authentication_required": True,
                "description": "Account information",
                "query_parameters": {
                    "currency": {
                        "type": "string",
                        "required": False,
                        "description": "Currency (e.g., USDT). If not provided, returns all currencies"
                    }
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

        # Gate.io doesn't provide endpoint discovery endpoint
        # Using static endpoints based on documentation

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Gate.io WebSocket channels and message formats.

        Gate.io WebSocket API uses V3 with channel naming like spot.tickers, spot.trades, etc.
        Documentation: https://www.gate.io/docs/developers/apiv4/ws/en/

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Gate.io WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public)
        # ============================================================================

        # Tickers channel
        channels.append({
            "channel_name": "tickers",
            "authentication_required": False,
            "description": "Real-time ticker updates for trading pairs",
            "subscribe_format": {
                "time": 1234567890,  # Current timestamp
                "channel": "spot.tickers",
                "event": "subscribe",
                "payload": ["BTC_USDT"]  # Replace with actual pair
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "spot.tickers",
                "event": "unsubscribe",
                "payload": ["BTC_USDT"]
            },
            "message_types": ["update"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "integer", "description": "Event timestamp"},
                    "time_ms": {"type": "integer", "description": "Event timestamp in milliseconds"},
                    "channel": {"type": "string", "description": "Channel name"},
                    "event": {"type": "string", "description": "Event type"},
                    "result": {
                        "type": "object",
                        "properties": {
                            "currency_pair": {"type": "string"},
                            "last": {"type": "string"},
                            "lowest_ask": {"type": "string"},
                            "highest_bid": {"type": "string"},
                            "change_percentage": {"type": "string"},
                            "base_volume": {"type": "string"},
                            "quote_volume": {"type": "string"},
                            "high_24h": {"type": "string"},
                            "low_24h": {"type": "string"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "spot.tickers",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Order book channel
        channels.append({
            "channel_name": "orderbook",
            "authentication_required": False,
            "description": "Real-time order book updates (level 2)",
            "subscribe_format": {
                "time": 1234567890,
                "channel": "spot.order_book",
                "event": "subscribe",
                "payload": ["BTC_USDT", "10", "100ms"]  # symbol, depth, interval
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "spot.order_book",
                "event": "unsubscribe",
                "payload": ["BTC_USDT", "10", "100ms"]
            },
            "message_types": ["update", "snapshot"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "integer", "description": "Event timestamp"},
                    "time_ms": {"type": "integer", "description": "Event timestamp in milliseconds"},
                    "channel": {"type": "string", "description": "Channel name"},
                    "event": {"type": "string", "description": "Event type"},
                    "result": {
                        "type": "object",
                        "properties": {
                            "t": {"type": "integer", "description": "Update timestamp"},
                            "e": {"type": "string", "description": "Event type"},
                            "s": {"type": "string", "description": "Symbol"},
                            "b": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                }
                            },
                            "a": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                }
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "spot.order_book",
                "supports_multiple_symbols": True,
                "update_frequency": "100ms",
                "depth_options": ["5", "10", "20", "50", "100"]
            }
        })

        # Trades channel
        channels.append({
            "channel_name": "trades",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "time": 1234567890,
                "channel": "spot.trades",
                "event": "subscribe",
                "payload": ["BTC_USDT"]
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "spot.trades",
                "event": "unsubscribe",
                "payload": ["BTC_USDT"]
            },
            "message_types": ["update"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "integer", "description": "Event timestamp"},
                    "time_ms": {"type": "integer", "description": "Event timestamp in milliseconds"},
                    "channel": {"type": "string", "description": "Channel name"},
                    "event": {"type": "string", "description": "Event type"},
                    "result": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Trade ID"},
                            "create_time": {"type": "string", "description": "Create time"},
                            "create_time_ms": {"type": "string", "description": "Create time in milliseconds"},
                            "side": {"type": "string", "description": "buy or sell"},
                            "amount": {"type": "string", "description": "Trade amount"},
                            "price": {"type": "string", "description": "Trade price"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "spot.trades",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Candlestick channel
        channels.append({
            "channel_name": "candlesticks",
            "authentication_required": False,
            "description": "Real-time candlestick updates",
            "subscribe_format": {
                "time": 1234567890,
                "channel": "spot.candlesticks",
                "event": "subscribe",
                "payload": ["1m", "BTC_USDT"]  # interval, symbol
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "spot.candlesticks",
                "event": "unsubscribe",
                "payload": ["1m", "BTC_USDT"]
            },
            "message_types": ["update"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "integer", "description": "Event timestamp"},
                    "time_ms": {"type": "integer", "description": "Event timestamp in milliseconds"},
                    "channel": {"type": "string", "description": "Channel name"},
                    "event": {"type": "string", "description": "Event type"},
                    "result": {
                        "type": "object",
                        "properties": {
                            "t": {"type": "string", "description": "Candle timestamp"},
                            "v": {"type": "string", "description": "Quote volume"},
                            "c": {"type": "string", "description": "Close price"},
                            "h": {"type": "string", "description": "High price"},
                            "l": {"type": "string", "description": "Low price"},
                            "o": {"type": "string", "description": "Open price"},
                            "n": {"type": "string", "description": "Base volume"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "spot.candlesticks",
                "supported_intervals": ["10s", "1m", "5m", "15m", "30m", "1h", "4h", "8h", "1d", "7d", "30d"],
                "update_frequency": "interval-dependent"
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
                "time": 1234567890,
                "channel": "server.ping",
                "event": "ping"
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "server.ping",
                "event": "pong"
            },
            "message_types": ["ping", "pong"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "integer", "description": "Current timestamp"},
                    "channel": {"type": "string", "description": "Channel name"},
                    "event": {"type": "string", "description": "Event type"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "server.ping",
                "keepalive_interval": 30,
                "auto_reconnect": True
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        # Account channel example (commented out for Phase 1)
        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account balance updates",
            "subscribe_format": {
                "time": 1234567890,
                "channel": "spot.balances",
                "event": "subscribe",
                "auth": {
                    "method": "api_key",
                    "KEY": "<api_key>",
                    "SIGN": "<signature>"
                }
            },
            "unsubscribe_format": {
                "time": 1234567890,
                "channel": "spot.balances",
                "event": "unsubscribe"
            },
            "message_types": ["update"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "channel_pattern": "spot.balances",
                "requires_api_key": True
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Gate.io trading products/symbols from live API.

        Uses Gate.io API: /api/v4/spot/currency_pairs
        Documentation: https://www.gate.io/docs/developers/apiv4/en/#list-all-currency-pairs-supported

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Gate.io products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM GATE.IO API
            # ========================================================================

            # Gate.io currency pairs endpoint
            products_url = f"{self.base_url}/api/v4/spot/currency_pairs"

            logger.debug(f"Fetching Gate.io products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE GATE.IO RESPONSE FORMAT
            # ========================================================================

            # Gate.io returns array directly
            if not isinstance(response, list):
                logger.error(f"Unexpected response format: {type(response)}")
                logger.debug(f"Full response: {response}")
                raise Exception(f"Unexpected response format from Gate.io")

            symbols_data = response

            # ========================================================================
            # 3. PROCESS EACH CURRENCY PAIR/PRODUCT
            # ========================================================================

            products = []
            for symbol_info in symbols_data:
                try:
                    # Extract symbol information from Gate.io response
                    symbol = symbol_info.get("id", "")  # e.g., "BTC_USDT"
                    base_currency = symbol_info.get("base", "")
                    quote_currency = symbol_info.get("quote", "")

                    # Status mapping for Gate.io
                    trade_status = symbol_info.get("trade_status", "")
                    if trade_status == "tradable":
                        status = "online"
                    elif trade_status in ["halted", "disabled"]:
                        status = "offline"
                    elif trade_status == "delisted":
                        status = "delisted"
                    else:
                        status = "offline"  # Default if unknown

                    # Trading limits and precision from Gate.io response
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Minimum order size (base amount)
                    min_base_amount = symbol_info.get("min_base_amount")
                    if min_base_amount:
                        min_order_size = float(min_base_amount)

                    # Maximum order size - Gate.io doesn't provide max directly
                    # Could use min_quote_amount for quote side min

                    # Price increment (tick size) - Gate.io provides precision
                    precision = symbol_info.get("precision")
                    if precision is not None:
                        try:
                            price_increment = 10 ** -int(precision)
                        except (ValueError, TypeError):
                            pass

                    # Additional precision information
                    amount_precision = symbol_info.get("amount_precision")
                    min_quote_amount = symbol_info.get("min_quote_amount")
                    fee = symbol_info.get("fee")
                    sell_start = symbol_info.get("sell_start")
                    buy_start = symbol_info.get("buy_start")

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": {
                            "original_data": symbol_info,
                            "id": symbol_info.get("id"),
                            "fee": fee,
                            "min_base_amount": min_base_amount,
                            "min_quote_amount": min_quote_amount,
                            "amount_precision": amount_precision,
                            "precision": precision,
                            "trade_status": trade_status,
                            "sell_start": sell_start,
                            "buy_start": buy_start
                        }
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse Gate.io product {symbol_info.get('id', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from Gate.io API response")
                raise Exception("No products found in Gate.io API response")

            # Count online vs offline products
            online_products = [p for p in products if p['status'] == 'online']
            logger.info(f"Discovered {len(products)} total products ({len(online_products)} online)")

            return products

        except Exception as e:
            logger.error(f"Failed to discover Gate.io products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Gate.io: {e}")
            raise Exception(f"Product discovery failed for Gate.io: {e}")

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
