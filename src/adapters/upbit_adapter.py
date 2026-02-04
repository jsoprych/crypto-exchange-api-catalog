# src/adapters/upbit_adapter.py
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


class UpbitAdapter(BaseVendorAdapter):
    """
    Template adapter for Upbit Exchange API.

    Replace all occurrences of:
    - 'UpbitAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Upbit' with actual exchange name (e.g., 'Bybit')
    - 'https://api.upbit.com' with actual REST API base URL
    - 'wss://api.upbit.com/websocket/v1' with actual WebSocket URL
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
        Discover Upbit REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Upbit REST endpoints")

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
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "market": {"type": "string"},
                            "trade_date": {"type": "string"},
                            "trade_time": {"type": "string"},
                            "trade_date_kst": {"type": "string"},
                            "trade_time_kst": {"type": "string"},
                            "trade_timestamp": {"type": "integer"},
                            "opening_price": {"type": "number"},
                            "high_price": {"type": "number"},
                            "low_price": {"type": "number"},
                            "trade_price": {"type": "number"},
                            "prev_closing_price": {"type": "number"},
                            "change": {"type": "string"},
                            "change_price": {"type": "number"},
                            "change_rate": {"type": "number"},
                            "signed_change_price": {"type": "number"},
                            "signed_change_rate": {"type": "number"},
                            "trade_volume": {"type": "number"},
                            "acc_trade_price": {"type": "number"},
                            "acc_trade_price_24h": {"type": "number"},
                            "acc_trade_volume": {"type": "number"},
                            "acc_trade_volume_24h": {"type": "number"},
                            "highest_52_week_price": {"type": "number"},
                            "highest_52_week_date": {"type": "string"},
                            "lowest_52_week_price": {"type": "number"},
                            "lowest_52_week_date": {"type": "string"},
                            "timestamp": {"type": "integer"}
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
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "market": {"type": "string"},
                            "timestamp": {"type": "integer"},
                            "total_ask_size": {"type": "number"},
                            "total_bid_size": {"type": "number"},
                            "orderbook_units": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "bid_price": {"type": "number"},
                                        "bid_size": {"type": "number"},
                                        "ask_price": {"type": "number"},
                                        "ask_size": {"type": "number"}
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
                "description": "Recent trades",
                "query_parameters": {
                    "market": {
                        "type": "string",
                        "required": True,
                        "description": "Market symbol (e.g., KRW-BTC)"
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades to return (1-200)",
                        "default": 200
                    },
                    "cursor": {
                        "type": "string",
                        "required": False,
                        "description": "Cursor for pagination"
                    },
                    "daysAgo": {
                        "type": "integer",
                        "required": False,
                        "description": "Days ago to fetch trades from (1-7)",
                        "default": 1
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "market": {"type": "string"},
                            "trade_date_utc": {"type": "string"},
                            "trade_time_utc": {"type": "string"},
                            "timestamp": {"type": "integer"},
                            "trade_price": {"type": "number"},
                            "trade_volume": {"type": "number"},
                            "prev_closing_price": {"type": "number"},
                            "change_price": {"type": "number"},
                            "ask_bid": {"type": "string"},
                            "sequential_id": {"type": "integer"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v1/candles/{timeframe}",
                "method": "GET",
                "authentication_required": False,
                "description": "Candlestick/OHLC data",
                "path_parameters": {
                    "timeframe": {
                        "type": "string",
                        "required": True,
                        "description": "Candle timeframe (minutes/1, minutes/3, minutes/5, minutes/10, minutes/15, minutes/30, minutes/60, minutes/240, days, weeks, months)"
                    }
                },
                "query_parameters": {
                    "market": {
                        "type": "string",
                        "required": True,
                        "description": "Market symbol"
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of candles to return (1-200)",
                        "default": 200
                    },
                    "to": {
                        "type": "string",
                        "required": False,
                        "description": "End time in ISO 8601 format"
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "market": {"type": "string"},
                            "candle_date_time_utc": {"type": "string"},
                            "candle_date_time_kst": {"type": "string"},
                            "opening_price": {"type": "number"},
                            "high_price": {"type": "number"},
                            "low_price": {"type": "number"},
                            "trade_price": {"type": "number"},
                            "timestamp": {"type": "integer"},
                            "candle_acc_trade_price": {"type": "number"},
                            "candle_acc_trade_volume": {"type": "number"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(market_data_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Upbit WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Upbit WebSocket channels")

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
        Discover Upbit trading products/symbols from live API.

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
        logger.info("Discovering Upbit products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # Upbit endpoint: /v1/market/all
            products_url = f"{self.base_url}/v1/market/all"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON UPBIT FORMAT
            # ========================================================================

            products = []

            # Upbit response format: array of market objects
            if not isinstance(response, list):
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Upbit, expected array")

            symbols_data = response

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for market_info in symbols_data:
                try:
                    # Extract fields from Upbit market object
                    market_symbol = market_info.get('market')

                    # Validate required field
                    if not market_symbol:
                        logger.warning(f"Skipping market with missing 'market' field: {market_info}")
                        continue

                    # Parse base and quote currency from market symbol (format: "KRW-BTC" or "BTC-ETH")
                    # Upbit uses format: "QUOTE-BASE" for KRW pairs, "BASE-QUOTE" for crypto pairs
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

                    # Upbit doesn't provide status in this endpoint, assume online
                    status = 'online'

                    # Trading limits/precision - Upbit doesn't provide in this endpoint
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": market_info  # Store full raw data
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

            # Optional: Filter to only online products if needed
            # online_products = [p for p in products if p['status'] == 'online']
            # logger.info(f"Online products: {len(online_products)}")

            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Upbit: {e}")

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
