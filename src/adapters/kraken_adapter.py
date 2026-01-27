# src/adapters/kraken_adapter.py
"""
Kraken Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from Kraken API.
"""

from typing import Dict, List, Any

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KrakenAdapter(BaseVendorAdapter):
    """
    Adapter for Kraken Exchange API discovery.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Kraken REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering Kraken REST endpoints")

        endpoints = []

        # Market data endpoints (public)
        market_endpoints = [
            {
                "path": "/0/public/Time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get server time",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/SystemStatus",
                "method": "GET",
                "authentication_required": False,
                "description": "Get system status",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/Assets",
                "method": "GET",
                "authentication_required": False,
                "description": "Get asset info",
                "query_parameters": {
                    "asset": "comma delimited list of assets (optional)",
                    "aclass": "asset class (optional, default: currency)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/AssetPairs",
                "method": "GET",
                "authentication_required": False,
                "description": "Get tradable asset pairs",
                "query_parameters": {
                    "pair": "comma delimited list of pairs (optional)",
                    "info": "info to retrieve (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/Ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker information",
                "query_parameters": {
                    "pair": "comma delimited list of pairs (required)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/OHLC",
                "method": "GET",
                "authentication_required": False,
                "description": "Get OHLC (candlestick) data",
                "query_parameters": {
                    "pair": "asset pair (required)",
                    "interval": "time frame interval (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)",
                    "since": "return data since given id (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/Depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book",
                "query_parameters": {
                    "pair": "asset pair (required)",
                    "count": "maximum number of asks/bids (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/Trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades",
                "query_parameters": {
                    "pair": "asset pair (required)",
                    "since": "return trade data since given id (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/0/public/Spread",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent spread data",
                "query_parameters": {
                    "pair": "asset pair (required)",
                    "since": "return spread data since given id (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Kraken WebSocket channels.

        Returns:
            List of channel dictionaries
        """
        logger.info("Discovering Kraken WebSocket channels")

        channels = [
            {
                "channel_name": "ticker",
                "authentication_required": False,
                "description": "Ticker information on currency pair",
                "subscribe_format": {
                    "event": "subscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "ticker"
                    }
                },
                "unsubscribe_format": {
                    "event": "unsubscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "ticker"
                    }
                },
                "message_types": ["ticker"],
                "message_schema": {
                    "channelID": "integer",
                    "channelName": "ticker",
                    "pair": "string",
                    "a": "ask [price, whole lot volume, lot volume]",
                    "b": "bid [price, whole lot volume, lot volume]",
                    "c": "close [price, lot volume]",
                    "v": "volume [today, last 24 hours]",
                    "p": "volume weighted average price [today, last 24 hours]",
                    "t": "number of trades [today, last 24 hours]",
                    "l": "low [today, last 24 hours]",
                    "h": "high [today, last 24 hours]",
                    "o": "open [today, last 24 hours]"
                }
            },
            {
                "channel_name": "ohlc",
                "authentication_required": False,
                "description": "OHLC (candlestick) data",
                "subscribe_format": {
                    "event": "subscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "ohlc",
                        "interval": 1
                    }
                },
                "message_types": ["ohlc"],
                "message_schema": {
                    "channelID": "integer",
                    "time": "timestamp",
                    "etime": "end timestamp",
                    "open": "open price",
                    "high": "high price",
                    "low": "low price",
                    "close": "close price",
                    "vwap": "volume weighted average price",
                    "volume": "volume",
                    "count": "number of trades"
                }
            },
            {
                "channel_name": "trade",
                "authentication_required": False,
                "description": "Trade feed",
                "subscribe_format": {
                    "event": "subscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "trade"
                    }
                },
                "message_types": ["trade"],
                "message_schema": {
                    "channelID": "integer",
                    "price": "string",
                    "volume": "string",
                    "time": "timestamp",
                    "side": "buy or sell",
                    "orderType": "market or limit",
                    "misc": "miscellaneous"
                }
            },
            {
                "channel_name": "spread",
                "authentication_required": False,
                "description": "Spread data",
                "subscribe_format": {
                    "event": "subscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "spread"
                    }
                },
                "message_types": ["spread"],
                "message_schema": {
                    "channelID": "integer",
                    "bid": "best bid price",
                    "ask": "best ask price",
                    "timestamp": "timestamp",
                    "bidVolume": "bid volume",
                    "askVolume": "ask volume"
                }
            },
            {
                "channel_name": "book",
                "authentication_required": False,
                "description": "Order book (10, 25, 100, 500, 1000 depth levels)",
                "subscribe_format": {
                    "event": "subscribe",
                    "pair": ["XBT/USD"],
                    "subscription": {
                        "name": "book",
                        "depth": 10
                    }
                },
                "message_types": ["book-10", "book-25", "book-100", "book-500", "book-1000"],
                "message_schema": {
                    "channelID": "integer",
                    "asks": "array of [price, volume, timestamp]",
                    "bids": "array of [price, volume, timestamp]"
                }
            }
        ]

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Kraken trading products by fetching from /0/public/AssetPairs endpoint.

        Returns:
            List of product dictionaries
        """
        logger.info("Discovering Kraken products from live API")

        try:
            # Fetch asset pairs from Kraken API
            url = f"{self.base_url}/0/public/AssetPairs"
            response = self.http_client.get(url)

            if 'error' in response and response['error']:
                raise Exception(f"Kraken API error: {response['error']}")

            products = []
            for pair_name, pair_info in response.get('result', {}).items():
                # Skip dark pool pairs and non-standard pairs
                if pair_info.get('status') != 'online':
                    continue
                if '.d' in pair_name:  # Skip dark pool
                    continue

                # Parse product information
                product = {
                    "symbol": pair_name,
                    "base_currency": pair_info.get("base"),
                    "quote_currency": pair_info.get("quote"),
                    "status": "online" if pair_info.get("status") == "online" else "offline",
                    "vendor_metadata": pair_info  # Store full response
                }

                # Extract order size limits if available
                if 'ordermin' in pair_info:
                    product['min_order_size'] = float(pair_info.get('ordermin', 0))

                # Price increment (tick size)
                if 'pair_decimals' in pair_info:
                    product['price_increment'] = 10 ** -int(pair_info.get('pair_decimals', 0))

                products.append(product)

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise

    def get_ohlc_intervals(self) -> List[int]:
        """
        Get available OHLC (candlestick) intervals for Kraken in minutes.

        Returns:
            List of interval values in minutes
        """
        return [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
