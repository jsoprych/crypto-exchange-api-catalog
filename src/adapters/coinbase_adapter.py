# src/adapters/coinbase_adapter.py
"""
Coinbase Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from Coinbase API.
"""

from typing import Dict, List, Any

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CoinbaseAdapter(BaseVendorAdapter):
    """
    Adapter for Coinbase Exchange API discovery.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Coinbase REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering Coinbase REST endpoints")

        endpoints = []

        # Market data endpoints (public)
        market_endpoints = [
            {
                "path": "/products",
                "method": "GET",
                "authentication_required": False,
                "description": "Get a list of available currency pairs for trading",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}",
                "method": "GET",
                "authentication_required": False,
                "description": "Get information on a single product",
                "path_parameters": {"product_id": "string"},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}/book",
                "method": "GET",
                "authentication_required": False,
                "description": "Get a list of open orders for a product",
                "path_parameters": {"product_id": "string"},
                "query_parameters": {"level": "integer (1, 2, or 3)"},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get snapshot information about the last trade (tick)",
                "path_parameters": {"product_id": "string"},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Get latest trades for a product",
                "path_parameters": {"product_id": "string"},
                "query_parameters": {"limit": "integer", "before": "integer", "after": "integer"},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}/candles",
                "method": "GET",
                "authentication_required": False,
                "description": "Get historic rates for a product (candles/OHLCV)",
                "path_parameters": {"product_id": "string"},
                "query_parameters": {
                    "start": "ISO 8601 datetime",
                    "end": "ISO 8601 datetime",
                    "granularity": "integer (60, 300, 900, 3600, 21600, 86400)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/products/{product_id}/stats",
                "method": "GET",
                "authentication_required": False,
                "description": "Get 24 hr stats for a product",
                "path_parameters": {"product_id": "string"},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/currencies",
                "method": "GET",
                "authentication_required": False,
                "description": "Get list of known currencies",
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/currencies/{currency_id}",
                "method": "GET",
                "authentication_required": False,
                "description": "Get information on a single currency",
                "path_parameters": {"currency_id": "string"},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get the API server time",
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Coinbase WebSocket channels.

        Returns:
            List of channel dictionaries
        """
        logger.info("Discovering Coinbase WebSocket channels")

        channels = [
            {
                "channel_name": "ticker",
                "authentication_required": False,
                "description": "Real-time price updates for a product",
                "subscribe_format": {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["ticker"]
                },
                "unsubscribe_format": {
                    "type": "unsubscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["ticker"]
                },
                "message_types": ["ticker", "subscriptions"],
                "message_schema": {
                    "type": "ticker",
                    "sequence": "integer",
                    "product_id": "string",
                    "price": "string",
                    "open_24h": "string",
                    "volume_24h": "string",
                    "low_24h": "string",
                    "high_24h": "string",
                    "volume_30d": "string",
                    "best_bid": "string",
                    "best_ask": "string",
                    "side": "string",
                    "time": "datetime",
                    "trade_id": "integer",
                    "last_size": "string"
                }
            },
            {
                "channel_name": "level2",
                "authentication_required": False,
                "description": "Order book snapshots and updates",
                "subscribe_format": {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["level2"]
                },
                "unsubscribe_format": {
                    "type": "unsubscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["level2"]
                },
                "message_types": ["snapshot", "l2update", "subscriptions"],
                "message_schema": {
                    "snapshot": {
                        "type": "snapshot",
                        "product_id": "string",
                        "bids": "array of [price, size]",
                        "asks": "array of [price, size]"
                    },
                    "l2update": {
                        "type": "l2update",
                        "product_id": "string",
                        "changes": "array of [side, price, size]",
                        "time": "datetime"
                    }
                }
            },
            {
                "channel_name": "matches",
                "authentication_required": False,
                "description": "Real-time match/trade messages",
                "subscribe_format": {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["matches"]
                },
                "unsubscribe_format": {
                    "type": "unsubscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["matches"]
                },
                "message_types": ["last_match", "match", "subscriptions"],
                "message_schema": {
                    "type": "match",
                    "trade_id": "integer",
                    "sequence": "integer",
                    "maker_order_id": "string",
                    "taker_order_id": "string",
                    "time": "datetime",
                    "product_id": "string",
                    "size": "string",
                    "price": "string",
                    "side": "string"
                }
            },
            {
                "channel_name": "heartbeat",
                "authentication_required": False,
                "description": "Heartbeat messages to keep connection alive",
                "subscribe_format": {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["heartbeat"]
                },
                "unsubscribe_format": {
                    "type": "unsubscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["heartbeat"]
                },
                "message_types": ["heartbeat", "subscriptions"],
                "message_schema": {
                    "type": "heartbeat",
                    "sequence": "integer",
                    "last_trade_id": "integer",
                    "product_id": "string",
                    "time": "datetime"
                }
            },
            {
                "channel_name": "status",
                "authentication_required": False,
                "description": "Product status messages (online, offline, etc.)",
                "subscribe_format": {
                    "type": "subscribe",
                    "channels": ["status"]
                },
                "unsubscribe_format": {
                    "type": "unsubscribe",
                    "channels": ["status"]
                },
                "message_types": ["status", "subscriptions"],
                "message_schema": {
                    "type": "status",
                    "products": "array of product status objects",
                    "currencies": "array of currency status objects"
                }
            }
        ]

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Coinbase trading products by fetching from /products endpoint.

        Returns:
            List of product dictionaries
        """
        logger.info("Discovering Coinbase products from live API")

        try:
            # Fetch products from Coinbase API
            url = f"{self.base_url}/products"
            response = self.http_client.get(url)

            products = []
            for item in response:
                # Parse product information
                product = {
                    "symbol": item.get("id"),
                    "base_currency": item.get("base_currency"),
                    "quote_currency": item.get("quote_currency"),
                    "status": "online" if item.get("status") == "online" else "offline",
                    "min_order_size": float(item.get("base_min_size", 0)),
                    "max_order_size": float(item.get("base_max_size", 0)) if item.get("base_max_size") else None,
                    "price_increment": float(item.get("quote_increment", 0)),
                    "vendor_metadata": item  # Store full response
                }
                products.append(product)

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise

    def get_candle_intervals(self) -> List[int]:
        """
        Get available candle intervals for Coinbase.

        Returns:
            List of granularity values in seconds
        """
        # Coinbase supported granularities
        return [60, 300, 900, 3600, 21600, 86400]
