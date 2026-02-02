# src/adapters/okx_adapter.py
"""
OKX exchange adapter.

This adapter implements discovery for OKX cryptocurrency exchange.
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


class OkxAdapter(BaseVendorAdapter):
    """
    OKX exchange adapter.

    This adapter discovers REST endpoints, WebSocket channels, and products
    from the OKX cryptocurrency exchange.

    Configuration (add to config/settings.py):
    "okx": {
        "enabled": True,
        "display_name": "OKX Exchange",
        "base_url": "https://www.okx.com",
        "websocket_url": "wss://ws.okx.com:8443",
        "documentation_url": "https://www.okx.com/docs/en/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "instruments": "/api/v5/public/instruments",
            "time": "/api/v5/public/time",
            "tickers": "/api/v5/market/tickers"
        },
        "rate_limits": {
            "public": 20  # Requests per second (approximate)
        }
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover OKX REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering OKX REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/api/v5/public/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get OKX server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "ts": {"type": "string", "description": "ISO format timestamp"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v5/public/status",
                "method": "GET",
                "authentication_required": False,
                "description": "Get system status",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(system_endpoints)

        # OKX instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/v5/public/instruments",
                "method": "GET",
                "authentication_required": False,
                "description": "Get OKX instrument information including trading pairs and specifications",
                "query_parameters": {
                    "instType": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument type (SPOT, MARGIN, SWAP, FUTURES, OPTION)",
                        "enum": ["SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION"]
                    },
                    "instId": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument ID (e.g., BTC-USDT)"
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
                "path": "/api/v5/market/tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker information for all trading pairs",
                "query_parameters": {
                    "instType": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument type (SPOT, MARGIN, SWAP, FUTURES, OPTION)",
                        "enum": ["SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION"]
                    },
                    "instId": {
                        "type": "string",
                        "required": False,
                        "description": "Instrument ID (e.g., BTC-USDT)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v5/market/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get single ticker information",
                "query_parameters": {
                    "instId": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument ID (e.g., BTC-USDT)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "instId": {"type": "string"},
                        "last": {"type": "string"},
                        "lastSz": {"type": "string"},
                        "askPx": {"type": "string"},
                        "askSz": {"type": "string"},
                        "bidPx": {"type": "string"},
                        "bidSz": {"type": "string"},
                        "open24h": {"type": "string"},
                        "high24h": {"type": "string"},
                        "low24h": {"type": "string"},
                        "volCcy24h": {"type": "string"},
                        "vol24h": {"type": "string"},
                        "ts": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v5/market/books",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book depth",
                "query_parameters": {
                    "instId": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument ID (e.g., BTC-USDT)"
                    },
                    "sz": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of depth levels (1-400)",
                        "default": 100
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
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
                        },
                        "ts": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v5/market/candles",
                "method": "GET",
                "authentication_required": False,
                "description": "Get candlestick data",
                "query_parameters": {
                    "instId": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument ID (e.g., BTC-USDT)"
                    },
                    "bar": {
                        "type": "string",
                        "required": False,
                        "description": "Timeframe (1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W, 1M)",
                        "default": "1m"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of candles to return (1-100)",
                        "default": 100
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
                "path": "/api/v5/market/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades",
                "query_parameters": {
                    "instId": {
                        "type": "string",
                        "required": True,
                        "description": "Instrument ID (e.g., BTC-USDT)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades to return (1-500)",
                        "default": 100
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "instId": {"type": "string"},
                            "tradeId": {"type": "string"},
                            "px": {"type": "string"},
                            "sz": {"type": "string"},
                            "side": {"type": "string"},
                            "ts": {"type": "string"}
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
        Discover OKX WebSocket channels and message formats.

        Implementation Strategy:
        1. Map all public WebSocket channels from documentation
        2. Include subscribe/unsubscribe message formats
        3. Document message types and schemas
        4. Note authentication requirements

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering OKX WebSocket channels")

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
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": "<instrument>"}]  # Replace <instrument> with actual pair
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{"channel": "tickers", "instId": "<instrument>"}]
            },
            "message_types": ["tickers", "snapshot"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "arg": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "instId": {"type": "string"}
                        }
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "instId": {"type": "string"},
                                "last": {"type": "string"},
                                "lastSz": {"type": "string"},
                                "askPx": {"type": "string"},
                                "askSz": {"type": "string"},
                                "bidPx": {"type": "string"},
                                "bidSz": {"type": "string"},
                                "open24h": {"type": "string"},
                                "high24h": {"type": "string"},
                                "low24h": {"type": "string"},
                                "volCcy24h": {"type": "string"},
                                "vol24h": {"type": "string"},
                                "ts": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "tickers:{instrument}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
            }
        })

        # Order book channel
        channels.append({
            "channel_name": "books",
            "authentication_required": False,
            "description": "Real-time order book updates (level 2)",
            "subscribe_format": {
                "op": "subscribe",
                "args": [{"channel": "books", "instId": "<instrument>"}]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{"channel": "books", "instId": "<instrument>"}]
            },
            "message_types": ["books", "snapshot"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "arg": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "instId": {"type": "string"}
                        }
                    },
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
                                },
                                "ts": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "books:{instrument}",
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
                "op": "subscribe",
                "args": [{"channel": "candle1m", "instId": "<instrument>"}]  # Can use candle1m, candle5m, etc.
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{"channel": "candle1m", "instId": "<instrument>"}]
            },
            "message_types": ["candle", "snapshot"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "arg": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "instId": {"type": "string"}
                        }
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 8,
                            "maxItems": 8,
                            "description": "[ts, o, h, l, c, vol, volCcy, volCcyQuote]"
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "candle{timeframe}:{instrument}",
                "supported_timeframes": ["1m", "5m", "15m", "30m", "1H", "4H", "1D", "1W", "1M"],
                "update_frequency": "timeframe-dependent"
            }
        })

        # Trades channel
        channels.append({
            "channel_name": "trades",
            "authentication_required": False,
            "description": "Real-time trade updates",
            "subscribe_format": {
                "op": "subscribe",
                "args": [{"channel": "trades", "instId": "<instrument>"}]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{"channel": "trades", "instId": "<instrument>"}]
            },
            "message_types": ["trades", "snapshot"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "arg": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "instId": {"type": "string"}
                        }
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "instId": {"type": "string"},
                                "tradeId": {"type": "string"},
                                "px": {"type": "string"},
                                "sz": {"type": "string"},
                                "side": {"type": "string"},
                                "ts": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "trades:{instrument}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time"
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
            "description": "Account balance and position updates",
            "subscribe_format": {
                "op": "subscribe",
                "args": [{"channel": "account"}]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{"channel": "account"}]
            },
            "message_types": ["account", "snapshot"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "channel_pattern": "account",
                "requires_api_key": True
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels
    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover OKX trading products/symbols from live API.

        Uses OKX V5 API: /api/v5/public/instruments with instType=SPOT
        Documentation: https://www.okx.com/docs-v5/en/#rest-api-public-data-get-instruments

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering OKX products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM OKX V5 API
            # ========================================================================

            # OKX V5 instruments endpoint for spot trading
            products_url = f"{self.base_url}/api/v5/public/instruments"

            # Parameters for spot trading products
            params = {
                "instType": "SPOT"
            }

            logger.debug(f"Fetching OKX products from: {products_url} with params: {params}")

            # Make the API request
            response = self.http_client.get(products_url, params=params)

            # ========================================================================
            # 2. PARSE OKX RESPONSE FORMAT
            # ========================================================================

            # OKX V5 response format: {"code": "0", "msg": "", "data": [...]}
            if response.get("code") != "0":
                error_msg = response.get("msg", "Unknown error")
                logger.error(f"OKX API error: {error_msg} (code: {response.get('code')})")
                raise Exception(f"OKX API error: {error_msg}")

            symbols_data = response.get("data", [])

            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                logger.debug(f"Full response: {response}")
                raise Exception(f"Unexpected response format from OKX")

            # ========================================================================
            # 3. PROCESS EACH INSTRUMENT/PRODUCT
            # ========================================================================

            products = []
            for symbol_info in symbols_data:
                try:
                    # Extract instrument information from OKX response
                    symbol = symbol_info.get("instId", "")  # e.g., "BTC-USDT"
                    base_currency = symbol_info.get("baseCcy", "")
                    quote_currency = symbol_info.get("quoteCcy", "")

                    # Status mapping for OKX
                    state = symbol_info.get("state", "")
                    if state == "live":
                        status = "online"
                    elif state in ["suspend", "preopen"]:
                        status = "offline"
                    elif state == "expired":
                        status = "delisted"
                    else:
                        status = "offline"  # Default if unknown

                    # Trading limits and precision from OKX response
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Minimum order size (lot size)
                    lot_sz = symbol_info.get("lotSz")
                    if lot_sz:
                        min_order_size = float(lot_sz)

                    # Maximum order size (max order quantity)
                    max_lmt_sz = symbol_info.get("maxLmtSz")
                    if max_lmt_sz and max_lmt_sz != "9999999999999999":  # Skip placeholder value
                        try:
                            max_order_size = float(max_lmt_sz)
                        except ValueError:
                            pass

                    # Price increment (tick size)
                    tick_sz = symbol_info.get("tickSz")
                    if tick_sz:
                        price_increment = float(tick_sz)

                    # Additional precision information
                    min_sz = symbol_info.get("minSz")
                    max_mkt_sz = symbol_info.get("maxMktSz")
                    max_mkt_amt = symbol_info.get("maxMktAmt")

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
                            "instType": symbol_info.get("instType"),
                            "category": symbol_info.get("category"),
                            "state": state,
                            "minSz": min_sz,
                            "maxMktSz": max_mkt_sz,
                            "maxMktAmt": max_mkt_amt,
                            "lotSz": lot_sz,
                            "tickSz": tick_sz,
                            "listTime": symbol_info.get("listTime"),
                            "expTime": symbol_info.get("expTime")
                        }
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse OKX product {symbol_info.get('instId', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from OKX API response")
                raise Exception("No products found in OKX API response")

            # Count online vs offline products
            online_products = [p for p in products if p['status'] == 'online']
            logger.info(f"Discovered {len(products)} total products ({len(online_products)} online)")

            return products

        except Exception as e:
            logger.error(f"Failed to discover OKX products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for OKX: {e}")

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
