# src/adapters/kucoin_adapter.py
"""
KuCoin exchange adapter.

This adapter implements discovery for KuCoin cryptocurrency exchange.
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


class KucoinAdapter(BaseVendorAdapter):
    """
    KuCoin exchange adapter.

    This adapter discovers REST endpoints, WebSocket channels, and products
    from the KuCoin cryptocurrency exchange.

    Configuration (add to config/settings.py):
    "kucoin": {
        "enabled": True,
        "display_name": "KuCoin Exchange",
        "base_url": "https://api.kucoin.com",
        "websocket_url": "wss://ws-api.kucoin.com/endpoint",
        "documentation_url": "https://docs.kucoin.com/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "symbols": "/api/v1/symbols",
            "time": "/api/v1/timestamp",
            "tickers": "/api/v1/market/allTickers"
        },
        "rate_limits": {
            "public": 20  # Requests per second (approximate)
        }
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover KuCoin REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering KuCoin REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/api/v1/timestamp",
                "method": "GET",
                "authentication_required": False,
                "description": "Get KuCoin server time (milliseconds)",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {"type": "integer", "description": "Server timestamp in milliseconds"}
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(system_endpoints)

        # KuCoin instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/v1/symbols",
                "method": "GET",
                "authentication_required": False,
                "description": "Get KuCoin trading pairs and specifications",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "name": {"type": "string"},
                                    "baseCurrency": {"type": "string"},
                                    "quoteCurrency": {"type": "string"},
                                    "feeCurrency": {"type": "string"},
                                    "market": {"type": "string"},
                                    "baseMinSize": {"type": "string"},
                                    "quoteMinSize": {"type": "string"},
                                    "baseMaxSize": {"type": "string"},
                                    "quoteMaxSize": {"type": "string"},
                                    "baseIncrement": {"type": "string"},
                                    "quoteIncrement": {"type": "string"},
                                    "priceIncrement": {"type": "string"},
                                    "priceLimitRate": {"type": "string"},
                                    "isMarginEnabled": {"type": "boolean"},
                                    "enableTrading": {"type": "boolean"}
                                }
                            }
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
                "path": "/api/v1/market/allTickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker information for all trading pairs",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "integer", "description": "Current timestamp"},
                                "ticker": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string"},
                                            "symbolName": {"type": "string"},
                                            "buy": {"type": "string"},
                                            "sell": {"type": "string"},
                                            "changeRate": {"type": "string"},
                                            "changePrice": {"type": "string"},
                                            "high": {"type": "string"},
                                            "low": {"type": "string"},
                                            "vol": {"type": "string"},
                                            "volValue": {"type": "string"},
                                            "last": {"type": "string"},
                                            "averagePrice": {"type": "string"},
                                            "takerFeeRate": {"type": "string"},
                                            "makerFeeRate": {"type": "string"},
                                            "takerCoefficient": {"type": "string"},
                                            "makerCoefficient": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v1/market/orderbook/level2_20",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book depth (top 20 levels)",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol (e.g., BTC-USDT)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "integer", "description": "Timestamp"},
                                "sequence": {"type": "string", "description": "Sequence number"},
                                "bids": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 2,
                                        "maxItems": 2,
                                        "description": "[price, size]"
                                    }
                                },
                                "asks": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 2,
                                        "maxItems": 2,
                                        "description": "[price, size]"
                                    }
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v1/market/candles",
                "method": "GET",
                "authentication_required": False,
                "description": "Get candlestick data",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol (e.g., BTC-USDT)"
                    },
                    "type": {
                        "type": "string",
                        "required": True,
                        "description": "Candle timeframe (1min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week)",
                        "enum": ["1min", "5min", "15min", "30min", "1hour", "2hour", "4hour", "6hour", "8hour", "12hour", "1day", "1week"]
                    },
                    "startAt": {
                        "type": "integer",
                        "required": False,
                        "description": "Start time (seconds)"
                    },
                    "endAt": {
                        "type": "integer",
                        "required": False,
                        "description": "End time (seconds)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 6,
                                "maxItems": 6,
                                "description": "[timestamp, open, high, low, close, volume]"
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v1/market/histories",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol (e.g., BTC-USDT)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "API response code"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sequence": {"type": "string", "description": "Sequence number"},
                                    "tradeId": {"type": "string", "description": "Trade ID"},
                                    "price": {"type": "string", "description": "Trade price"},
                                    "size": {"type": "string", "description": "Trade size"},
                                    "side": {"type": "string", "description": "buy or sell"},
                                    "time": {"type": "string", "description": "Timestamp in nanoseconds"}
                                }
                            }
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
                "path": "/api/v1/accounts",
                "method": "GET",
                "authentication_required": True,
                "description": "Account information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
        ]
        endpoints.extend(authenticated_endpoints)
        """

        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # KuCoin doesn't provide endpoint discovery endpoint
        # Using static endpoints based on documentation

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover KuCoin WebSocket channels and message formats.

        KuCoin WebSocket API uses topics like /market/ticker, /market/level2, etc.
        Documentation: https://docs.kucoin.com/#websocket-feed

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering KuCoin WebSocket channels")

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
                "topic": "/market/ticker:{symbol}",  # Replace {symbol} with actual pair
                "response": True
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "topic": "/market/ticker:{symbol}",
                "response": True
            },
            "message_types": ["ticker"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type"},
                    "topic": {"type": "string", "description": "Topic name"},
                    "subject": {"type": "string", "description": "Message subject"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "sequence": {"type": "string", "description": "Sequence number"},
                            "price": {"type": "string", "description": "Last trade price"},
                            "size": {"type": "string", "description": "Last trade size"},
                            "bestAsk": {"type": "string", "description": "Best ask price"},
                            "bestAskSize": {"type": "string", "description": "Best ask size"},
                            "bestBid": {"type": "string", "description": "Best bid price"},
                            "bestBidSize": {"type": "string", "description": "Best bid size"},
                            "time": {"type": "integer", "description": "Timestamp in nanoseconds"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "/market/ticker:{symbol}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Level 2 Order Book channel
        channels.append({
            "channel_name": "level2",
            "authentication_required": False,
            "description": "Real-time order book updates (level 2)",
            "subscribe_format": {
                "type": "subscribe",
                "topic": "/market/level2:{symbol}",  # Replace {symbol} with actual pair
                "response": True
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "topic": "/market/level2:{symbol}",
                "response": True
            },
            "message_types": ["snapshot", "update"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (snapshot or update)"},
                    "topic": {"type": "string", "description": "Topic name"},
                    "subject": {"type": "string", "description": "Message subject"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "sequence": {"type": "integer", "description": "Sequence number"},
                            "changes": {
                                "type": "object",
                                "properties": {
                                    "asks": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 2,
                                            "maxItems": 2,
                                            "description": "[price, size]"
                                        }
                                    },
                                    "bids": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 2,
                                            "maxItems": 2,
                                            "description": "[price, size]"
                                        }
                                    }
                                }
                            },
                            "time": {"type": "integer", "description": "Timestamp in milliseconds"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "/market/level2:{symbol}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Trade/match channel
        channels.append({
            "channel_name": "match",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "type": "subscribe",
                "topic": "/market/match:{symbol}",  # Replace {symbol} with actual pair
                "response": True
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "topic": "/market/match:{symbol}",
                "response": True
            },
            "message_types": ["match"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type"},
                    "topic": {"type": "string", "description": "Topic name"},
                    "subject": {"type": "string", "description": "Message subject"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "sequence": {"type": "string", "description": "Sequence number"},
                            "tradeId": {"type": "string", "description": "Trade ID"},
                            "price": {"type": "string", "description": "Trade price"},
                            "size": {"type": "string", "description": "Trade size"},
                            "side": {"type": "string", "description": "buy or sell"},
                            "time": {"type": "string", "description": "Timestamp in nanoseconds"}
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "/market/match:{symbol}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Candlestick channel
        channels.append({
            "channel_name": "candle",
            "authentication_required": False,
            "description": "Real-time candlestick updates",
            "subscribe_format": {
                "type": "subscribe",
                "topic": "/market/candles:{symbol}_{type}",  # e.g., /market/candles:BTC-USDT_1min
                "response": True
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "topic": "/market/candles:{symbol}_{type}",
                "response": True
            },
            "message_types": ["candle"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type"},
                    "topic": {"type": "string", "description": "Topic name"},
                    "subject": {"type": "string", "description": "Message subject"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 6,
                            "maxItems": 6,
                            "description": "[timestamp, open, close, high, low, volume, amount]"
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "/market/candles:{symbol}_{type}",
                "supported_timeframes": ["1min", "5min", "15min", "30min", "1hour", "2hour", "4hour", "6hour", "8hour", "12hour", "1day", "1week"],
                "update_frequency": "timeframe-dependent"
            }
        })

        # ============================================================================
        # 2. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        # Account channel example (commented out for Phase 1)
        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account balance updates",
            "subscribe_format": {
                "type": "subscribe",
                "topic": "/account/balance",
                "privateChannel": True,
                "response": True
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "topic": "/account/balance",
                "privateChannel": True,
                "response": True
            },
            "message_types": ["account.balance"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "channel_pattern": "/account/balance",
                "requires_api_key": True
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels
    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover KuCoin trading products/symbols from live API.

        Uses KuCoin API: /api/v1/symbols
        Documentation: https://docs.kucoin.com/#get-symbols-list

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering KuCoin products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM KuCoin API
            # ========================================================================

            # KuCoin symbols endpoint for all trading pairs
            products_url = f"{self.base_url}/api/v1/symbols"

            logger.debug(f"Fetching KuCoin products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE KuCoin RESPONSE FORMAT
            # ========================================================================

            # KuCoin response format: {"code": "200000", "data": [...]}
            if response.get("code") != "200000":
                error_msg = response.get("msg", "Unknown error")
                logger.error(f"KuCoin API error: {error_msg} (code: {response.get('code')})")
                raise Exception(f"KuCoin API error: {error_msg}")

            symbols_data = response.get("data", [])

            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                logger.debug(f"Full response: {response}")
                raise Exception(f"Unexpected response format from KuCoin")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            products = []
            for symbol_info in symbols_data:
                try:
                    # Extract symbol information from KuCoin response
                    symbol = symbol_info.get("symbol", "")  # e.g., "BTC-USDT"
                    base_currency = symbol_info.get("baseCurrency", "")
                    quote_currency = symbol_info.get("quoteCurrency", "")

                    # Status mapping for KuCoin
                    enable_trading = symbol_info.get("enableTrading", False)
                    if enable_trading:
                        status = "online"
                    else:
                        status = "offline"

                    # Trading limits and precision from KuCoin response
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Minimum order size
                    base_min_size = symbol_info.get("baseMinSize")
                    if base_min_size:
                        min_order_size = float(base_min_size)

                    # Maximum order size
                    base_max_size = symbol_info.get("baseMaxSize")
                    if base_max_size:
                        try:
                            max_order_size = float(base_max_size)
                        except ValueError:
                            pass

                    # Price increment (tick size)
                    price_increment_str = symbol_info.get("priceIncrement")
                    if price_increment_str:
                        price_increment = float(price_increment_str)

                    # Additional precision information
                    base_increment = symbol_info.get("baseIncrement")
                    quote_increment = symbol_info.get("quoteIncrement")
                    quote_min_size = symbol_info.get("quoteMinSize")
                    quote_max_size = symbol_info.get("quoteMaxSize")

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
                            "name": symbol_info.get("name"),
                            "feeCurrency": symbol_info.get("feeCurrency"),
                            "market": symbol_info.get("market"),
                            "baseMinSize": base_min_size,
                            "baseMaxSize": base_max_size,
                            "baseIncrement": base_increment,
                            "quoteMinSize": quote_min_size,
                            "quoteMaxSize": quote_max_size,
                            "quoteIncrement": quote_increment,
                            "priceIncrement": price_increment_str,
                            "priceLimitRate": symbol_info.get("priceLimitRate"),
                            "isMarginEnabled": symbol_info.get("isMarginEnabled"),
                            "enableTrading": enable_trading
                        }
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse KuCoin product {symbol_info.get('symbol', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from KuCoin API response")
                raise Exception("No products found in KuCoin API response")

            # Count online vs offline products
            online_products = [p for p in products if p['status'] == 'online']
            logger.info(f"Discovered {len(products)} total products ({len(online_products)} online)")

            return products

        except Exception as e:
            logger.error(f"Failed to discover KuCoin products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for KuCoin: {e}")

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
