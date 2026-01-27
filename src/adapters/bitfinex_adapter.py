# src/adapters/bitfinex_adapter.py
"""
Bitfinex Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from Bitfinex API.
"""

from typing import Dict, List, Any

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BitfinexAdapter(BaseVendorAdapter):
    """
    Adapter for Bitfinex Exchange API discovery.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Bitfinex REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering Bitfinex REST endpoints")

        endpoints = []

        # Market data endpoints (public) - v2 API
        market_endpoints = [
            {
                "path": "/v2/platform/status",
                "method": "GET",
                "authentication_required": False,
                "description": "Get current platform status",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/conf/pub:map:currency:sym",
                "method": "GET",
                "authentication_required": False,
                "description": "Get currency symbol mapping",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get tickers for multiple trading pairs",
                "query_parameters": {
                    "symbols": "comma-separated list of symbols (required)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/ticker/{symbol}",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker for a specific symbol",
                "path_parameters": {
                    "symbol": "trading symbol (e.g., tBTCUSD)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/trades/{symbol}/hist",
                "method": "GET",
                "authentication_required": False,
                "description": "Get trade history",
                "path_parameters": {
                    "symbol": "trading symbol"
                },
                "query_parameters": {
                    "limit": "number of records (max 10000, default 120)",
                    "start": "millisecond start time",
                    "end": "millisecond end time",
                    "sort": "1 = ascending, -1 = descending"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/book/{symbol}/{precision}",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book",
                "path_parameters": {
                    "symbol": "trading symbol",
                    "precision": "P0, P1, P2, P3, P4, R0"
                },
                "query_parameters": {
                    "len": "number of price points (25, 100)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/candles/trade:{timeframe}:{symbol}/hist",
                "method": "GET",
                "authentication_required": False,
                "description": "Get candle chart data",
                "path_parameters": {
                    "timeframe": "1m, 5m, 15m, 30m, 1h, 3h, 6h, 12h, 1D, 7D, 14D, 1M",
                    "symbol": "trading symbol"
                },
                "query_parameters": {
                    "limit": "number of candles (max 10000, default 120)",
                    "start": "millisecond start time",
                    "end": "millisecond end time",
                    "sort": "1 = ascending, -1 = descending"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/candles/trade:{timeframe}:{symbol}/last",
                "method": "GET",
                "authentication_required": False,
                "description": "Get last candle",
                "path_parameters": {
                    "timeframe": "candle timeframe",
                    "symbol": "trading symbol"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/v2/stats1/{key}:{size}:{symbol}:{side}/{section}",
                "method": "GET",
                "authentication_required": False,
                "description": "Get various statistics",
                "path_parameters": {
                    "key": "stats key (e.g., pos.size, funding.size)",
                    "size": "timeframe (1m, 5m, 15m, 30m, 1h, etc.)",
                    "symbol": "trading symbol",
                    "side": "long or short",
                    "section": "last or hist"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Bitfinex WebSocket channels.

        Returns:
            List of channel dictionaries
        """
        logger.info("Discovering Bitfinex WebSocket channels")

        channels = [
            {
                "channel_name": "ticker",
                "authentication_required": False,
                "description": "Ticker updates",
                "subscribe_format": {
                    "event": "subscribe",
                    "channel": "ticker",
                    "symbol": "tBTCUSD"
                },
                "unsubscribe_format": {
                    "event": "unsubscribe",
                    "chanId": 0
                },
                "message_types": ["ticker"],
                "message_schema": {
                    "CHANNEL_ID": "integer",
                    "BID": "float",
                    "BID_SIZE": "float",
                    "ASK": "float",
                    "ASK_SIZE": "float",
                    "DAILY_CHANGE": "float",
                    "DAILY_CHANGE_RELATIVE": "float",
                    "LAST_PRICE": "float",
                    "VOLUME": "float",
                    "HIGH": "float",
                    "LOW": "float"
                }
            },
            {
                "channel_name": "trades",
                "authentication_required": False,
                "description": "Real-time trades",
                "subscribe_format": {
                    "event": "subscribe",
                    "channel": "trades",
                    "symbol": "tBTCUSD"
                },
                "message_types": ["trade", "te", "tu"],
                "message_schema": {
                    "ID": "integer",
                    "MTS": "millisecond timestamp",
                    "AMOUNT": "float (positive = buy, negative = sell)",
                    "PRICE": "float"
                }
            },
            {
                "channel_name": "book",
                "authentication_required": False,
                "description": "Order book feed",
                "subscribe_format": {
                    "event": "subscribe",
                    "channel": "book",
                    "symbol": "tBTCUSD",
                    "prec": "P0",
                    "len": "25"
                },
                "message_types": ["book"],
                "message_schema": {
                    "PRICE": "float",
                    "COUNT": "integer (number of orders)",
                    "AMOUNT": "float (positive = bid, negative = ask)"
                }
            },
            {
                "channel_name": "candles",
                "authentication_required": False,
                "description": "Candle chart updates",
                "subscribe_format": {
                    "event": "subscribe",
                    "channel": "candles",
                    "key": "trade:1m:tBTCUSD"
                },
                "message_types": ["candles"],
                "message_schema": {
                    "MTS": "millisecond timestamp",
                    "OPEN": "float",
                    "CLOSE": "float",
                    "HIGH": "float",
                    "LOW": "float",
                    "VOLUME": "float"
                }
            },
            {
                "channel_name": "status",
                "authentication_required": False,
                "description": "Platform status updates",
                "subscribe_format": {
                    "event": "subscribe",
                    "channel": "status",
                    "key": "liq:global"
                },
                "message_types": ["status"],
                "message_schema": {
                    "KEY": "string",
                    "VALUE": "varies by status type"
                }
            }
        ]

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Bitfinex trading products by fetching tickers endpoint.

        Returns:
            List of product dictionaries
        """
        logger.info("Discovering Bitfinex products from live API")

        try:
            # Fetch all trading pair symbols from Bitfinex conf endpoint
            url = f"{self.base_url}/v2/conf/pub:list:pair:exchange"
            response = self.http_client.get(url)

            if not isinstance(response, list) or len(response) == 0:
                raise Exception(f"Unexpected response format from Bitfinex")

            # Response format: [[symbol1, symbol2, ...]]
            # Extract the first (and only) element which contains the list
            symbols = response[0] if isinstance(response[0], list) else response

            products = []
            for symbol in symbols:
                # Bitfinex uses two formats:
                # 1. Colon-separated: "AAVE:USD", "BTC:EURQ"
                # 2. Concatenated: "BTCUSD", "ETHUSD"
                base_currency = None
                quote_currency = None

                if ':' in symbol:
                    # Format: "BASE:QUOTE"
                    parts = symbol.split(':')
                    base_currency = parts[0]
                    quote_currency = parts[1] if len(parts) > 1 else ""
                else:
                    # Try common quote currencies
                    for quote in ['USDT', 'USD', 'EURQ', 'USDQ', 'USDR', 'EURR', 'XAUT', 'EUR', 'GBP', 'JPY', 'TRY', 'BTC', 'ETH', 'UST']:
                        if symbol.endswith(quote):
                            quote_currency = quote
                            base_currency = symbol[:-len(quote)]
                            break

                    # If we couldn't parse, try to split at 3-4 characters
                    if not base_currency:
                        if len(symbol) >= 6:
                            base_currency = symbol[:len(symbol)//2]
                            quote_currency = symbol[len(symbol)//2:]
                        else:
                            base_currency = symbol
                            quote_currency = ""

                # Normalize the symbol for API calls (remove colon)
                normalized_symbol = symbol.replace(':', '')

                product = {
                    "symbol": symbol,
                    "base_currency": base_currency,
                    "quote_currency": quote_currency,
                    "status": "online",
                    "vendor_metadata": {
                        "pair": symbol,
                        "api_symbol": f"t{normalized_symbol}"  # Bitfinex uses 't' prefix
                    }
                }

                products.append(product)

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise

    def get_candle_timeframes(self) -> List[str]:
        """
        Get available candle timeframes for Bitfinex.

        Returns:
            List of timeframe strings
        """
        return ["1m", "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1D", "7D", "14D", "1M"]
