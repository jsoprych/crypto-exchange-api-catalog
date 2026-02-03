# src/adapters/crypto_com_adapter.py
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


class Crypto_comAdapter(BaseVendorAdapter):
    """
    Template adapter for Crypto_com Exchange API.

    Replace all occurrences of:
    - 'Crypto_comAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Crypto_com' with actual exchange name (e.g., 'Bybit')
    - 'https://api.crypto.com/exchange/v1' with actual REST API base URL
    - 'wss://stream.crypto.com/exchange/v1/market' with actual WebSocket URL
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
        Discover Crypto.com Exchange REST API endpoints.

        Based on official documentation: https://exchange-docs.crypto.com/

        Implementation Strategy:
        1. Include all public market data endpoints
        2. Document authentication requirements
        3. Include query parameters and response schemas
        4. Note rate limits from documentation

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Crypto.com Exchange REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/public/get-instruments",
                "method": "GET",
                "authentication_required": False,
                "description": "Get information on all supported instruments (e.g., BTCUSD-PERP)",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "e.g., BTCUSD-PERP"},
                                    "inst_type": {"type": "string", "description": "e.g., PERPETUAL_SWAP"},
                                    "display_name": {"type": "string", "description": "e.g., BTCUSD Perpetual"},
                                    "base_ccy": {"type": "string", "description": "Base currency, e.g., BTC"},
                                    "quote_ccy": {"type": "string", "description": "Quote currency, e.g., USD"},
                                    "quote_decimals": {"type": "number", "description": "Minimum decimal place for price field"},
                                    "quantity_decimals": {"type": "number", "description": "Minimum decimal place for qty field"},
                                    "price_tick_size": {"type": "string", "description": "Minimum price tick size"},
                                    "qty_tick_size": {"type": "string", "description": "Minimum trading quantity / tick size"},
                                    "max_leverage": {"type": "string", "description": "Max leverage of the product"},
                                    "tradable": {"type": "boolean", "description": "True or false"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-announcements",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch all announcements in Crypto.com Exchange",
                "query_parameters": {
                    "category": {
                        "type": "string",
                        "required": False,
                        "description": "Filter by category: list, delist, event, product, system"
                    },
                    "product_type": {
                        "type": "string",
                        "required": False,
                        "description": "Filter by product type. e.g., Spot, Derivative, OTC, Staking, TradingArena etc"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
        ]
        endpoints.extend(product_endpoints)

        # Market data endpoints
        market_data_endpoints = [
            {
                "path": "/public/get-tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get public tickers for all or a particular instrument",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": False,
                        "description": "e.g., BTCUSD-PERP (optional, if omitted returns all)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "h": {"type": "string", "description": "Price of the 24h highest trade"},
                                    "l": {"type": "string", "description": "Price of the 24h lowest trade, null if there weren't any trades"},
                                    "a": {"type": "string", "description": "The price of the latest trade, null if there weren't any trades"},
                                    "i": {"type": "string", "description": "Instrument name"},
                                    "v": {"type": "string", "description": "The total 24h traded volume"},
                                    "vv": {"type": "string", "description": "The total 24h traded volume value (in USD)"},
                                    "oi": {"type": "string", "description": "Open interest"},
                                    "c": {"type": "string", "description": "24-hour price change, null if there weren't any trades"},
                                    "b": {"type": "string", "description": "The current best bid price, null if there aren't any bids"},
                                    "k": {"type": "string", "description": "The current best ask price, null if there aren't any asks"},
                                    "t": {"type": "number", "description": "The published timestamp in ms"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-book",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch the public order book for a particular instrument and depth",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "e.g., BTCUSD-PERP"
                    },
                    "depth": {
                        "type": "string",
                        "required": True,
                        "description": "Number of bids and asks to return (up to 50)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "instrument_name": {"type": "string"},
                        "depth": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "asks": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 3,
                                            "maxItems": 3,
                                            "description": "[0] = Price, [1] = Quantity, [2] = Number of Orders"
                                        }
                                    },
                                    "bids": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 3,
                                            "maxItems": 3,
                                            "description": "[0] = Price, [1] = Quantity, [2] = Number of Orders"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch public trades for a particular instrument",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "e.g., BTCUSD-PERP"
                    },
                    "count": {
                        "type": "number",
                        "required": False,
                        "description": "Maximum number of trades to retrieve. Default: 25, Max: 150"
                    },
                    "start_ts": {
                        "type": "number_or_string",
                        "required": False,
                        "description": "Start time in Unix time format (inclusive). Default: end_time - 1 day"
                    },
                    "end_ts": {
                        "type": "number_or_string",
                        "required": False,
                        "description": "End time in Unix time format (exclusive). Default: current system timestamp"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "d": {"type": "string", "description": "Trade ID"},
                                    "t": {"type": "number", "description": "Trade timestamp in milliseconds"},
                                    "tn": {"type": "string", "description": "Trade timestamp in nanoseconds"},
                                    "q": {"type": "string", "description": "Trade quantity"},
                                    "p": {"type": "string", "description": "Trade price"},
                                    "s": {"type": "string", "description": "Side (BUY or SELL)"},
                                    "i": {"type": "string", "description": "Instrument name"},
                                    "m": {"type": "string", "description": "Trade match ID"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-candlestick",
                "method": "GET",
                "authentication_required": False,
                "description": "Retrieve candlesticks (k-line data history) over a given period for an instrument",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "e.g., BTCUSD-PERP"
                    },
                    "timeframe": {
                        "type": "string",
                        "required": False,
                        "description": "The period value: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1D, 7D, 14D, 1M. Default: M1",
                        "default": "M1"
                    },
                    "count": {
                        "type": "number",
                        "required": False,
                        "description": "Default is 25",
                        "default": 25
                    },
                    "start_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is 1 day ago (Unix timestamp)"
                    },
                    "end_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is current time (Unix timestamp)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "instrument_name": {"type": "string"},
                        "interval": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "t": {"type": "long", "description": "Start time of candlestick (Unix timestamp)"},
                                    "o": {"type": "number", "description": "Open"},
                                    "h": {"type": "number", "description": "High"},
                                    "l": {"type": "number", "description": "Low"},
                                    "c": {"type": "number", "description": "Close"},
                                    "v": {"type": "number", "description": "Volume"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-valuations",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch certain valuation type data for a particular instrument",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "e.g., BTCUSD-INDEX"
                    },
                    "valuation_type": {
                        "type": "string",
                        "required": True,
                        "description": "index_price, mark_price, funding_hist, funding_rate, estimated_funding_rate"
                    },
                    "count": {
                        "type": "number",
                        "required": False,
                        "description": "Default is 25",
                        "default": 25
                    },
                    "start_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is 30 days ago for funding_hist, 1 day ago for others"
                    },
                    "end_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is current time (Unix timestamp)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "instrument_name": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "v": {"type": "string", "description": "Value"},
                                    "t": {"type": "long", "description": "Timestamp"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
        ]
        endpoints.extend(market_data_endpoints)

        # ============================================================================
        # 2. SYSTEM ENDPOINTS
        # ============================================================================

        system_endpoints = [
            {
                "path": "/public/get-expired-settlement-price",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch settlement price of expired instruments",
                "query_parameters": {
                    "instrument_type": {
                        "type": "string",
                        "required": True,
                        "description": "FUTURE"
                    },
                    "page": {
                        "type": "number",
                        "required": False,
                        "description": "Default is 1"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
            {
                "path": "/public/get-insurance",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch balance of Insurance Fund for a particular currency",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "e.g., USD"
                    },
                    "count": {
                        "type": "number",
                        "required": False,
                        "description": "Default is 25"
                    },
                    "start_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is 1 day ago (Unix timestamp)"
                    },
                    "end_ts": {
                        "type": "number",
                        "required": False,
                        "description": "Default timestamp is current time (Unix timestamp)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public",
                "rate_limit_notes": "100 requests per second (public market data)"
            },
        ]
        endpoints.extend(system_endpoints)

        # ============================================================================
        # 3. STAKING ENDPOINTS (Public)
        # ============================================================================

        staking_endpoints = [
            {
                "path": "/public/staking/get-conversion-rate",
                "method": "GET",
                "authentication_required": False,
                "description": "Get conversion rate between staked token and liquid staking token",
                "query_parameters": {
                    "instrument_name": {
                        "type": "string",
                        "required": True,
                        "description": "CDCETH (liquid staking token instrument name)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "instrument_name": {"type": "string", "description": "CDCETH"},
                        "conversion_rate": {"type": "string", "description": "conversion rate between staked token (ETH.staked) and liquid staking token (CDCETH)"}
                    }
                },
                "rate_limit_tier": "staking",
                "rate_limit_notes": "50 requests per second (staking endpoints)"
            },
        ]
        endpoints.extend(staking_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Crypto_com WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Crypto_com WebSocket channels")

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
        Discover Crypto_com trading products/symbols from live API.

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
        logger.info("Discovering Crypto_com products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM EXCHANGE API
            # ========================================================================

            # Crypto.com Exchange uses /public/get-instruments endpoint
            products_url = f"{self.base_url}/public/get-instruments"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON CRYPTO.COM FORMAT
            # ========================================================================

            products = []

            # Crypto.com response format: {"id": 1, "method": "...", "code": 0, "result": {"data": [...]}}
            if 'result' in response and 'data' in response['result']:
                symbols_data = response['result']['data']
            elif 'data' in response:
                symbols_data = response['data']
            else:
                # Default to trying to use the response directly
                symbols_data = response

            # Ensure we have an iterable
            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                raise Exception(f"Unexpected response format from Crypto_com")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for symbol_info in symbols_data:
                try:
                    # Extract fields from Crypto.com format
                    symbol = symbol_info.get('symbol')
                    base_currency = symbol_info.get('base_ccy')
                    quote_currency = symbol_info.get('quote_ccy')

                    # Status: use 'tradable' field (boolean)
                    tradable = symbol_info.get('tradable', False)
                    status = 'online' if tradable else 'offline'

                    # Trading limits/precision
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Extract price tick size and quantity tick size
                    price_tick_size = symbol_info.get('price_tick_size')
                    qty_tick_size = symbol_info.get('qty_tick_size')

                    if price_tick_size:
                        try:
                            price_increment = float(price_tick_size)
                        except (ValueError, TypeError):
                            price_increment = None

                    if qty_tick_size:
                        try:
                            min_order_size = float(qty_tick_size)
                        except (ValueError, TypeError):
                            min_order_size = None

                    # Decimals for precision
                    quantity_decimals = symbol_info.get('quantity_decimals')
                    quote_decimals = symbol_info.get('quote_decimals')

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

            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Crypto_com: {e}")

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
