# src/adapters/bithumb_adapter.py
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


class BithumbAdapter(BaseVendorAdapter):
    """
    Adapter for Bithumb Exchange API.

    Bithumb is a leading South Korean cryptocurrency exchange.
    API Documentation: https://apidocs.bithumb.com/

    Key endpoints:
    - GET /v1/market/all - List all trading markets
    - GET /v1/ticker - Current price and 24h statistics
    - GET /v1/orderbook - Order book depth
    - GET /v1/trades/ticks - Recent trades
    - GET /v1/candles/days - Daily candlestick data
    - WebSocket: wss://ws-api.bithumb.com/websocket/v1

    Market format: "KRW-BTC", "BTC-ETH" (QUOTE-BASE for KRW pairs, BASE-QUOTE for crypto pairs)
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Bithumb REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Bithumb REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/v1/market/all",
                "method": "GET",
                "authentication_required": False,
                "description": "Get list of all trading markets",
                "query_parameters": {
                    "isDetails": {
                        "type": "boolean",
                        "required": False,
                        "description": "If true, returns detailed information including Korean and English names",
                        "default": False
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "market": {"type": "string"},
                            "korean_name": {"type": "string"},
                            "english_name": {"type": "string"}
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
                "path": "/v1/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Current price and 24-hour statistics",
                "query_parameters": {
                    "markets": {
                        "type": "string",
                        "required": True,
                        "description": "Comma-separated list of market symbols (e.g., KRW-BTC,BTC-ETH)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "opening_price": {"type": "number"},
                                    "closing_price": {"type": "number"},
                                    "min_price": {"type": "number"},
                                    "max_price": {"type": "number"},
                                    "average_price": {"type": "number"},
                                    "volume": {"type": "number"},
                                    "volume_power": {"type": "number"},
                                    "sell_order_book": {"type": "number"},
                                    "buy_order_book": {"type": "number"},
                                    "date": {"type": "integer"},
                                    "acc_trade_price": {"type": "number"},
                                    "acc_trade_price_24h": {"type": "number"},
                                    "acc_trade_volume": {"type": "number"},
                                    "acc_trade_volume_24h": {"type": "number"},
                                    "highest_52_week_price": {"type": "integer"},
                                    "highest_52_week_date": {"type": "string"},
                                    "lowest_52_week_price": {"type": "integer"},
                                    "lowest_52_week_date": {"type": "string"},
                                    "timestamp": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v1/orderbook",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth",
                "query_parameters": {
                    "markets": {
                        "type": "string",
                        "required": True,
                        "description": "Comma-separated list of market symbols"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "integer"},
                                    "order_currency": {"type": "string"},
                                    "payment_currency": {"type": "string"},
                                    "bids": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "price": {"type": "string"},
                                                "quantity": {"type": "string"},
                                                "order_type": {"type": "string"}
                                            }
                                        }
                                    },
                                    "asks": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "price": {"type": "string"},
                                                "quantity": {"type": "string"},
                                                "order_type": {"type": "string"}
                                            }
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
                "path": "/v1/trades/ticks",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trade ticks",
                "query_parameters": {
                    "market": {
                        "type": "string",
                        "required": True,
                        "description": "Market symbol (e.g., krw-btc)"
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trade ticks to retrieve",
                        "default": 1
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "integer"},
                                    "price": {"type": "string"},
                                    "units": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v1/candles/days",
                "method": "GET",
                "authentication_required": False,
                "description": "Daily candlestick data",
                "query_parameters": {
                    "market": {
                        "type": "string",
                        "required": False,
                        "description": "Market symbol (optional)"
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of candles to retrieve",
                        "default": 1
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "array"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v1/candles/weeks",
                "method": "GET",
                "authentication_required": False,
                "description": "Weekly candlestick data",
                "query_parameters": {
                    "market": {
                        "type": "string",
                        "required": False,
                        "description": "Market symbol (optional)"
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of candles to retrieve",
                        "default": 1
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "array"}
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(market_data_endpoints)

        # ============================================================================
        # 2. AUTHENTICATED ENDPOINTS (Phase 3 - Optional for initial implementation)
        # ============================================================================

        # Bithumb requires authentication for most account-related endpoints
        # These are placeholder for future implementation
        authenticated_endpoints = [
            {
                "path": "/info/account",
                "method": "POST",
                "authentication_required": True,
                "description": "Account balance information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
            {
                "path": "/info/balance",
                "method": "POST",
                "authentication_required": True,
                "description": "Detailed balance information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
        ]
        endpoints.extend(authenticated_endpoints)

        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # Bithumb doesn't provide endpoint discovery, using static endpoints

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Bithumb WebSocket channels and message formats.

        Bithumb WebSocket API documentation:
        - Connection URL: wss://ws-api.bithumb.com/websocket/v1
        - Subscription format: Array of objects
        - Example: [{"ticket":"test example"},{"type":"ticker","codes":["KRW-BTC"]}]
        - Response format: JSON objects with type field indicating data type

        Implementation Strategy:
        1. Map public WebSocket channels from documentation (ticker, trade)
        2. Include Bithumb-specific subscribe/unsubscribe message formats
        3. Document message types and schemas based on actual API responses
        4. Note authentication requirements (none for public channels)

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Bithumb WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public - No Authentication Required)
        # ============================================================================

        # Ticker channel - Real-time price updates
        channels.append({
            "channel_name": "ticker",
            "authentication_required": False,
            "description": "Real-time ticker updates for trading pairs",
            "subscribe_format": [
                {"ticket": "bithumb_ticker_subscription"},
                {"type": "ticker", "codes": ["<market>"]},  # Replace <market> with actual market code
                {"format": "DEFAULT"}  # Options: DEFAULT, SIMPLE (abbreviated field names)
            ],
            "unsubscribe_format": [
                {"ticket": "bithumb_ticker_unsubscription"},
                {"type": "ticker", "codes": ["<market>"]}
            ],
            "message_types": ["ticker", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (ticker)"},
                    "code": {"type": "string", "description": "Market code (e.g., KRW-BTC)"},
                    "opening_price": {"type": "number", "description": "Opening price for current day"},
                    "high_price": {"type": "number", "description": "Highest price for current day"},
                    "low_price": {"type": "number", "description": "Lowest price for current day"},
                    "trade_price": {"type": "number", "description": "Current trade price"},
                    "prev_closing_price": {"type": "number", "description": "Previous day's closing price"},
                    "change": {"type": "string", "description": "Price change direction (RISE, FALL, EVEN)"},
                    "change_price": {"type": "number", "description": "Absolute price change"},
                    "change_rate": {"type": "number", "description": "Price change rate"},
                    "signed_change_price": {"type": "number", "description": "Signed price change"},
                    "signed_change_rate": {"type": "number", "description": "Signed change rate"},
                    "trade_volume": {"type": "number", "description": "Current trade volume"},
                    "acc_trade_volume": {"type": "number", "description": "Accumulated trade volume"},
                    "acc_trade_volume_24h": {"type": "number", "description": "24h accumulated trade volume"},
                    "acc_trade_price": {"type": "number", "description": "Accumulated trade price"},
                    "acc_trade_price_24h": {"type": "number", "description": "24h accumulated trade price"},
                    "trade_date": {"type": "string", "description": "Trade date (YYYY-MM-DD, KST)"},
                    "trade_time": {"type": "string", "description": "Trade time (HH:mm:ss, KST)"},
                    "trade_timestamp": {"type": "integer", "description": "Trade timestamp in milliseconds"},
                    "ask_bid": {"type": "string", "description": "ASK (sell) or BID (buy)"},
                    "acc_ask_volume": {"type": "number", "description": "Accumulated ask volume"},
                    "acc_bid_volume": {"type": "number", "description": "Accumulated bid volume"},
                    "highest_52_week_price": {"type": "number", "description": "52-week highest price"},
                    "highest_52_week_date": {"type": "string", "description": "Date of 52-week highest price"},
                    "lowest_52_week_price": {"type": "number", "description": "52-week lowest price"},
                    "lowest_52_week_date": {"type": "string", "description": "Date of 52-week lowest price"},
                    "market_state": {"type": "string", "description": "Market state (ACTIVE, etc.)"},
                    "is_trading_suspended": {"type": "boolean", "description": "Trading suspended flag"},
                    "delisting_date": {"type": ["string", "null"], "description": "Delisting date if scheduled"},
                    "market_warning": {"type": "string", "description": "Market warning (NONE, CAUTION)"},
                    "timestamp": {"type": "integer", "description": "Message timestamp in milliseconds"},
                    "stream_type": {"type": "string", "description": "SNAPSHOT or REALTIME"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "ticker",  # Bithumb uses type field, not channel patterns
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "response_formats": ["DEFAULT", "SIMPLE"],
                "simple_format_mapping": {
                    "ty": "type", "cd": "code", "op": "opening_price", "hp": "high_price",
                    "lp": "low_price", "tp": "trade_price", "pcp": "prev_closing_price",
                    "c": "change", "cp": "change_price", "cr": "change_rate",
                    "scr": "signed_change_rate", "tv": "trade_volume", "atv": "acc_trade_volume",
                    "atv24h": "acc_trade_volume_24h", "atp": "acc_trade_price",
                    "atp24h": "acc_trade_price_24h", "tdt": "trade_date", "ttm": "trade_time",
                    "ttms": "trade_timestamp", "ab": "ask_bid", "aav": "acc_ask_volume",
                    "abv": "acc_bid_volume", "h52wp": "highest_52_week_price",
                    "h52wdt": "highest_52_week_date", "l52wp": "lowest_52_week_price",
                    "l52wdt": "lowest_52_week_date", "ms": "market_state", "its": "is_trading_suspended",
                    "dd": "delisting_date", "mw": "market_warning", "tms": "timestamp", "st": "stream_type"
                }
            }
        })

        # Trade channel - Real-time trade execution updates
        channels.append({
            "channel_name": "trade",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": [
                {"ticket": "bithumb_trade_subscription"},
                {"type": "trade", "codes": ["<market>"]},
                {"format": "DEFAULT"}
            ],
            "unsubscribe_format": [
                {"ticket": "bithumb_trade_unsubscription"},
                {"type": "trade", "codes": ["<market>"]}
            ],
            "message_types": ["trade", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (trade)"},
                    "code": {"type": "string", "description": "Market code (e.g., KRW-BTC)"},
                    "trade_price": {"type": "number", "description": "Transaction price"},
                    "trade_volume": {"type": "number", "description": "Transaction volume"},
                    "ask_bid": {"type": "string", "description": "ASK (sell) or BID (buy)"},
                    "prev_closing_price": {"type": "number", "description": "Previous day's closing price"},
                    "change": {"type": "string", "description": "Price change direction (RISE, FALL, EVEN)"},
                    "change_price": {"type": "number", "description": "Absolute price change"},
                    "trade_date": {"type": "string", "description": "Trade date (YYYY-MM-DD, KST)"},
                    "trade_time": {"type": "string", "description": "Trade time (HH:mm:ss, KST)"},
                    "trade_timestamp": {"type": "integer", "description": "Trade timestamp in milliseconds"},
                    "sequential_id": {"type": "integer", "description": "Unique transaction number"},
                    "timestamp": {"type": "integer", "description": "Message timestamp in milliseconds"},
                    "stream_type": {"type": "string", "description": "SNAPSHOT or REALTIME"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "trade",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "trade_types": ["individual"],  # Bithumb provides individual trades
                "include_maker_info": True  # ask_bid field indicates maker side
            }
        })

        # Orderbook channel - Real-time order book updates (if available)
        # Note: Bithumb WebSocket orderbook documentation not found in initial research
        # Placeholder for future implementation
        channels.append({
            "channel_name": "orderbook",
            "authentication_required": False,
            "description": "Real-time order book updates (placeholder - REST only documented)",
            "subscribe_format": [
                {"ticket": "bithumb_orderbook_subscription"},
                {"type": "orderbook", "codes": ["<market>"]},
                {"format": "DEFAULT"}
            ],
            "unsubscribe_format": [
                {"ticket": "bithumb_orderbook_unsubscription"},
                {"type": "orderbook", "codes": ["<market>"]}
            ],
            "message_types": ["orderbook", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (orderbook)"},
                    "code": {"type": "string", "description": "Market code"},
                    "timestamp": {"type": "integer", "description": "Order book timestamp"},
                    "order_currency": {"type": "string", "description": "Currency being traded"},
                    "payment_currency": {"type": "string", "description": "Payment currency"},
                    "bids": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "price": {"type": "string", "description": "Bid price"},
                                "quantity": {"type": "string", "description": "Bid quantity"},
                                "order_type": {"type": "string", "description": "Order type"}
                            }
                        }
                    },
                    "asks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "price": {"type": "string", "description": "Ask price"},
                                "quantity": {"type": "string", "description": "Ask quantity"},
                                "order_type": {"type": "string", "description": "Order type"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "orderbook",
                "documentation_status": "placeholder",  # REST orderbook documented, WebSocket not confirmed
                "update_type": "snapshot",  # Assuming full snapshot updates
                "levels": "full"  # Assuming full depth
            }
        })

        # ============================================================================
        # 2. HEARTBEAT/CONNECTION MANAGEMENT
        # ============================================================================

        channels.append({
            "channel_name": "heartbeat",
            "authentication_required": False,
            "description": "Connection heartbeat/ping-pong messages",
            "subscribe_format": [
                {"ticket": "bithumb_heartbeat"},
                {"type": "ping"}
            ],
            "unsubscribe_format": [
                {"ticket": "bithumb_heartbeat_unsubscribe"},
                {"type": "ping"}
            ],
            "message_types": ["pong", "connection", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (pong)"},
                    "timestamp": {"type": "integer", "description": "Timestamp"}
                }
            },
            "vendor_metadata": {
                "keepalive_interval": 30000,  # milliseconds (typical)
                "auto_reconnect": True,
                "ping_format": {"type": "ping"}  # Simple ping message
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        # Bithumb requires authentication for account-related WebSocket channels
        # Placeholder for future implementation
        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account updates (balance changes, orders, etc.)",
            "subscribe_format": [
                {"ticket": "bithumb_account_auth"},
                {"type": "auth", "api_key": "<api_key>", "signature": "<signature>", "timestamp": "<timestamp>"}
            ],
            "message_types": ["balance", "order", "trade"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "requires_signature": True,
                "update_types": ["balance", "order", "trade"],
                "auth_method": "api_key_signature"
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Bithumb trading products/symbols from live API.

        IMPORTANT: This method MUST make live API calls to fetch actual products.
        Do not hardcode products. Fetch from exchange's product endpoint.

        Implementation Steps:
        1. Call Bithumb's product endpoint /v1/market/all
        2. Parse the response to extract symbol information
        3. Map to our standard product format
        4. Handle pagination if needed
        5. Implement error handling and retry logic

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Bithumb products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # Bithumb endpoint: /v1/market/all
            products_url = f"{self.base_url}/v1/market/all"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON BITHUMB FORMAT
            # ========================================================================

            products = []

            # Bithumb response format: array of market objects
            if not isinstance(response, list):
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Bithumb, expected array")

            symbols_data = response

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for market_info in symbols_data:
                try:
                    # Extract fields from Bithumb market object
                    market_symbol = market_info.get('market')

                    # Validate required field
                    if not market_symbol:
                        logger.warning(f"Skipping market with missing 'market' field: {market_info}")
                        continue

                    # Parse base and quote currency from market symbol (format: "KRW-BTC" or "BTC-ETH")
                    # Bithumb uses format: "QUOTE-BASE" for KRW pairs, "BASE-QUOTE" for crypto pairs
                    parts = market_symbol.split('-')
                    if len(parts) != 2:
                        logger.warning(f"Skipping malformed market symbol {market_symbol}, expected format 'XXX-XXX'")
                        continue

                    # Determine if it's KRW pair (KRW-BTC) or crypto pair (BTC-ETH)
                    # For KRW pairs: quote is KRW, base is the other currency
                    # For crypto pairs: first is base, second is quote
                    if parts[0] == 'KRW':
                        # KRW-BTC format: KRW is quote, BTC is base
                        base_currency = parts[1]
                        quote_currency = parts[0]
                        symbol = f"{base_currency}-{quote_currency}"
                    else:
                        # BTC-ETH format: BTC is base, ETH is quote
                        base_currency = parts[0]
                        quote_currency = parts[1]
                        symbol = market_symbol

                    # Bithumb doesn't provide status in this endpoint, assume online
                    status = 'online'

                    # Trading limits/precision - Bithumb doesn't provide in this endpoint
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Extract Korean and English names if available
                    korean_name = market_info.get('korean_name')
                    english_name = market_info.get('english_name')

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
                            "market_symbol": market_symbol,
                            "korean_name": korean_name,
                            "english_name": english_name,
                            "raw_data": market_info
                        }
                    }

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse market {market_info.get('market', 'unknown')}: {e}")
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
            raise Exception(f"Product discovery failed for Bithumb: {e}")

    # ============================================================================
    # OPTIONAL HELPER METHODS
    # ============================================================================

    def get_candle_intervals(self) -> List[int]:
        """
        Get available candle intervals for this exchange.

        Returns:
            List of granularity values in seconds
        """
        # Bithumb candle endpoints:
        # - /v1/candles/days (daily candles)
        # - /v1/candles/weeks (weekly candles)
        # Note: Bithumb REST API primarily supports daily and weekly candles.
        # WebSocket may support additional intervals but documentation not found.
        return [60, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 604800]

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
