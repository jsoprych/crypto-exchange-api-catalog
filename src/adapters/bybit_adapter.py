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


class BybitAdapter(BaseVendorAdapter):
    """
    Template adapter for Bybit Exchange API.

    Adapter for Bybit Exchange API discovery.

    Configuration Example (already in config/settings.py):
    "bybit": {
        "enabled": True,
        "display_name": "Bybit",
        "base_url": "https://api.bybit.com",
        "websocket_url": "wss://stream.bybit.com/v5/public/spot",
        "documentation_url": "https://bybit-exchange.github.io/docs/v5/intro",
        ...
    }

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
        Discover Bybit REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Bybit REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/v5/market/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get Bybit server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timeSecond": {"type": "string", "description": "Server time in seconds"},
                        "timeNano": {"type": "string", "description": "Server time in nanoseconds"}
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(system_endpoints)

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/v5/market/instruments-info",
                "method": "GET",
                "authentication_required": False,
                "description": "Get instrument information including trading rules and symbol information",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": True,
                        "description": "Product type (spot, linear, inverse, option)",
                        "enum": ["spot", "linear", "inverse", "option"]
                    },
                    "symbol": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument name (e.g., BTCUSDT). If not provided, returns all symbols"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(product_endpoints)

        # Market data endpoints
        market_data_endpoints = [
            {
                "path": "/v5/market/tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get 24hr ticker information for all symbols or specific symbol",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": True,
                        "description": "Product type (spot, linear, inverse, option)",
                        "enum": ["spot", "linear", "inverse", "option"]
                    },
                    "symbol": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument name (e.g., BTCUSDT). If not provided, returns all symbols"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "lastPrice": {"type": "string"},
                        "highPrice24h": {"type": "string"},
                        "lowPrice24h": {"type": "string"},
                        "volume24h": {"type": "string"},
                        "turnover24h": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v5/market/orderbook",
                "method": "GET",
                "authentication_required": False,
                "description": "Get orderbook depth",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": True,
                        "description": "Product type (spot, linear, inverse, option)",
                        "enum": ["spot", "linear", "inverse", "option"]
                    },
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument name"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of depth levels (1, 50, 200, 500)",
                        "default": 50
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "s": {"type": "string", "description": "Symbol"},
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
                        },
                        "ts": {"type": "integer", "description": "Timestamp"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v5/market/kline",
                "method": "GET",
                "authentication_required": False,
                "description": "Get kline/candlestick data",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": True,
                        "description": "Product type (spot, linear, inverse, option)",
                        "enum": ["spot", "linear", "inverse", "option"]
                    },
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument name"
                    },
                    "interval": {
                        "type": "string",
                        "required": True,
                        "description": "Kline interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of klines to return (1-1000)",
                        "default": 200
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 6,
                        "maxItems": 6
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v5/market/recent-trade",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades list",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": True,
                        "description": "Product type (spot, linear, inverse, option)",
                        "enum": ["spot", "linear", "inverse", "option"]
                    },
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument name"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades to return (1-1000)",
                        "default": 50
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "execId": {"type": "string"},
                            "symbol": {"type": "string"},
                            "price": {"type": "string"},
                            "size": {"type": "string"},
                            "side": {"type": "string"},
                            "time": {"type": "string"}
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
        Discover Bybit WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Bybit WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public) - Bybit V5 WebSocket API
        # ============================================================================

        # Ticker channel - Bybit V5
        channels.append({
            "channel_name": "tickers",
            "authentication_required": False,
            "description": "Real-time ticker updates for trading pairs",
            "subscribe_format": {
                "op": "subscribe",
                "args": ["tickers.BTCUSDT"]  # Example, actual symbol will be replaced
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": ["tickers.BTCUSDT"]
            },
            "message_types": ["snapshot", "delta"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subscription topic"},
                    "type": {"type": "string", "description": "Message type (snapshot/delta)"},
                    "ts": {"type": "integer", "description": "Timestamp in milliseconds"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading pair"},
                            "lastPrice": {"type": "string", "description": "Last traded price"},
                            "highPrice24h": {"type": "string", "description": "24h high price"},
                            "lowPrice24h": {"type": "string", "description": "24h low price"},
                            "volume24h": {"type": "string", "description": "24h trading volume"},
                            "turnover24h": {"type": "string", "description": "24h turnover"},
                            "price24hPcnt": {"type": "string", "description": "24h price change percentage"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "tickers.{}",  # {} will be replaced with symbol
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "category": "spot",  # Also supports linear, inverse, option
                "version": "v5"
            }
        })

        # Order book channel - Bybit V5 (Level 1)
        channels.append({
            "channel_name": "orderbook",
            "authentication_required": False,
            "description": "Real-time order book updates (level 1)",
            "subscribe_format": {
                "op": "subscribe",
                "args": ["orderbook.1.BTCUSDT"]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": ["orderbook.1.BTCUSDT"]
            },
            "message_types": ["snapshot", "delta"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subscription topic"},
                    "type": {"type": "string", "description": "Message type (snapshot/delta)"},
                    "ts": {"type": "integer", "description": "Timestamp in milliseconds"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "s": {"type": "string", "description": "Symbol"},
                            "b": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                "description": "Bids [price, quantity]"
                            },
                            "a": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                "description": "Asks [price, quantity]"
                            },
                            "u": {"type": "integer", "description": "Orderbook update ID"},
                            "seq": {"type": "integer", "description": "Sequence number"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "orderbook.{}.{}",  # level.symbol
                "levels": [1, 50, 200, 500],  # Supported depth levels
                "update_type": "delta",
                "category": "spot",
                "version": "v5"
            }
        })

        # Trade channel - Bybit V5
        channels.append({
            "channel_name": "publicTrade",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "op": "subscribe",
                "args": ["publicTrade.BTCUSDT"]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": ["publicTrade.BTCUSDT"]
            },
            "message_types": ["snapshot", "delta"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subscription topic"},
                    "type": {"type": "string", "description": "Message type (snapshot)"},
                    "ts": {"type": "integer", "description": "Timestamp in milliseconds"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "i": {"type": "string", "description": "Trade ID"},
                                "T": {"type": "integer", "description": "Trade timestamp"},
                                "p": {"type": "string", "description": "Trade price"},
                                "v": {"type": "string", "description": "Trade volume"},
                                "S": {"type": "string", "description": "Side (Buy/Sell)"},
                                "s": {"type": "string", "description": "Symbol"},
                                "BT": {"type": "boolean", "description": "Block trade flag"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "publicTrade.{}",
                "trade_type": "individual",
                "include_maker_info": False,
                "category": "spot",
                "version": "v5"
            }
        })

        # Kline/candlestick channel - Bybit V5
        channels.append({
            "channel_name": "kline",
            "authentication_required": False,
            "description": "Real-time candlestick updates",
            "subscribe_format": {
                "op": "subscribe",
                "args": ["kline.1.BTCUSDT"]  # 1 minute interval
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": ["kline.1.BTCUSDT"]
            },
            "message_types": ["snapshot", "delta"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subscription topic"},
                    "type": {"type": "string", "description": "Message type (snapshot/delta)"},
                    "ts": {"type": "integer", "description": "Timestamp in milliseconds"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 6,
                            "maxItems": 6,
                            "description": "[start_time, open_price, high_price, low_price, close_price, volume]"
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "kline.{}.{}",  # interval.symbol
                "supported_intervals": ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"],
                "update_frequency": "interval-based",
                "category": "spot",
                "version": "v5"
            }
        })

        # ============================================================================
        # 2. HEARTBEAT/CONNECTION MANAGEMENT - Bybit V5
        # ============================================================================

        channels.append({
            "channel_name": "heartbeat",
            "authentication_required": False,
            "description": "Connection heartbeat/ping-pong messages",
            "subscribe_format": {
                "op": "subscribe",
                "args": []
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": []
            },
            "message_types": ["ping", "pong"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "description": "Operation (ping/pong)"},
                    "req_id": {"type": "string", "description": "Request ID"},
                    "args": {"type": "array", "items": {"type": "string"}}
                }
            },
            "vendor_metadata": {
                "keepalive_interval": 20000,  # Bybit recommends ping every 20 seconds
                "auto_reconnect": True,
                "version": "v5"
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        """
        channels.append({
            "channel_name": "position",
            "authentication_required": True,
            "description": "Position updates",
            "subscribe_format": {
                "op": "auth",
                "args": ["api_key", "expires", "signature"]
            },
            "message_types": ["snapshot", "delta"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "requires_signature": True,
                "update_types": ["position"],
                "category": "private",
                "version": "v5"
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Bybit trading products/symbols from live API.

        Uses Bybit V5 API: /v5/market/instruments-info with category=spot
        Documentation: https://bybit-exchange.github.io/docs/v5/market/instrument

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Bybit products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM BYBIT V5 API
            # ========================================================================

            # Bybit V5 instruments info endpoint for spot trading
            products_url = f"{self.base_url}/v5/market/instruments-info"

            # Parameters for spot trading products
            params = {
                "category": "spot"
            }

            logger.debug(f"Fetching Bybit products from: {products_url} with params: {params}")

            # Make the API request
            response = self.http_client.get(products_url, params=params)

            # ========================================================================
            # 2. PARSE BYBIT RESPONSE FORMAT
            # ========================================================================

            # Bybit V5 response format: {"retCode": 0, "retMsg": "OK", "result": {...}, ...}
            if response.get("retCode") != 0:
                error_msg = response.get("retMsg", "Unknown error")
                logger.error(f"Bybit API error: {error_msg} (code: {response.get('retCode')})")
                raise Exception(f"Bybit API error: {error_msg}")

            result = response.get("result", {})
            symbols_data = result.get("list", [])

            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                logger.debug(f"Full response: {response}")
                raise Exception(f"Unexpected response format from Bybit")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            products = []
            for symbol_info in symbols_data:
                try:
                    # Extract symbol information from Bybit response
                    symbol = symbol_info.get("symbol", "")
                    base_currency = symbol_info.get("baseCoin", "")
                    quote_currency = symbol_info.get("quoteCoin", "")

                    # Status mapping for Bybit
                    status_raw = symbol_info.get("status", "")
                    if status_raw == "Trading":
                        status = "online"
                    elif status_raw in ["Settling", "Closed"]:
                        status = "offline"
                    elif status_raw == "PreLaunch":
                        status = "offline"  # Not yet trading
                    else:
                        status = "offline"

                    # Trading limits and precision from Bybit response
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Lot size filter (min/max order size)
                    lot_size_filter = symbol_info.get("lotSizeFilter", {})
                    if lot_size_filter:
                        min_order_qty = lot_size_filter.get("minOrderQty")
                        max_order_qty = lot_size_filter.get("maxOrderQty")
                        if min_order_qty:
                            min_order_size = float(min_order_qty)
                        if max_order_qty:
                            max_order_size = float(max_order_qty)

                    # Price filter (tick size)
                    price_filter = symbol_info.get("priceFilter", {})
                    if price_filter:
                        tick_size = price_filter.get("tickSize")
                        if tick_size:
                            price_increment = float(tick_size)

                    # Additional precision information
                    base_precision = symbol_info.get("basePrecision", 8)
                    quote_precision = symbol_info.get("quotePrecision", 8)

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
                            "base_precision": base_precision,
                            "quote_precision": quote_precision,
                            "category": "spot",
                            "launch_time": symbol_info.get("launchTime"),
                            "delivery_time": symbol_info.get("deliveryTime")
                        }
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse Bybit product {symbol_info.get('symbol', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from Bybit API response")
                raise Exception("No products found in Bybit API response")

            # Count online vs offline products
            online_products = [p for p in products if p['status'] == 'online']
            logger.info(f"Discovered {len(products)} total products ({len(online_products)} online)")

            return products

        except Exception as e:
            logger.error(f"Failed to discover Bybit products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Bybit: {e}")

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
