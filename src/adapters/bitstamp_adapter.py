# src/adapters/bitstamp_adapter.py
"""
Bitstamp Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from Bitstamp API.
"""

from typing import Dict, List, Any, Optional

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BitstampAdapter(BaseVendorAdapter):
    """
    Adapter for Bitstamp Exchange API discovery.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Bitstamp REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering Bitstamp REST endpoints")

        endpoints = []

        # Market data endpoints (public)
        market_endpoints = [
            {
                "path": "/currencies/",
                "method": "GET",
                "authentication_required": False,
                "description": "Get list of all currencies with basic data",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/ticker/",
                "method": "GET",
                "authentication_required": False,
                "description": "Return ticker data for all markets",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/ticker/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Return ticker data for the requested currency pair",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "last": {"type": "string"},
                        "high": {"type": "string"},
                        "low": {"type": "string"},
                        "vwap": {"type": "string"},
                        "volume": {"type": "string"},
                        "bid": {"type": "string"},
                        "ask": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "open": {"type": "string"},
                        "open_24": {"type": "string"},
                        "percent_change_24": {"type": "string"},
                        "side": {"type": "string"},
                        "market_type": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/ticker_hour/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Return hourly ticker data for the requested currency pair",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "last": {"type": "string"},
                        "high": {"type": "string"},
                        "low": {"type": "string"},
                        "vwap": {"type": "string"},
                        "volume": {"type": "string"},
                        "bid": {"type": "string"},
                        "ask": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "open": {"type": "string"},
                        "side": {"type": "string"},
                        "market_type": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/order_book/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book data with grouping options",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {
                    "group": {
                        "type": "integer",
                        "required": False,
                        "description": "Group orders at same price (0: no grouping, 1: grouping, 2: with order IDs)",
                        "default": 1,
                        "enum": [0, 1, 2]
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"},
                        "microtimestamp": {"type": "string"},
                        "bids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 2
                            }
                        },
                        "asks": {
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
                "path": "/transactions/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Return transaction data from a given time frame",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {
                    "time": {
                        "type": "string",
                        "required": False,
                        "description": "Time interval (minute, hour, day)",
                        "default": "hour",
                        "enum": ["minute", "hour", "day"]
                    }
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "tid": {"type": "string"},
                            "price": {"type": "string"},
                            "amount": {"type": "string"},
                            "type": {"type": "string"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/markets/",
                "method": "GET",
                "authentication_required": False,
                "description": "View that returns list of all available markets",
                "query_parameters": {},
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/ohlc/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "OHLC (Open High Low Close) data",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {
                    "step": {
                        "type": "integer",
                        "required": True,
                        "description": "Timeframe in seconds",
                        "enum": [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200]
                    },
                    "limit": {
                        "type": "integer",
                        "required": True,
                        "description": "Limit OHLC results (1-1000)",
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "start": {
                        "type": "integer",
                        "required": False,
                        "description": "Unix timestamp from when OHLC data will be started"
                    },
                    "end": {
                        "type": "integer",
                        "required": False,
                        "description": "Unix timestamp to when OHLC data will be shown"
                    },
                    "exclude_current_candle": {
                        "type": "boolean",
                        "required": False,
                        "description": "If set, results won't include current (open) candle",
                        "default": False
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "properties": {
                                "pair": {"type": "string"},
                                "market": {"type": "string"},
                                "ohlc": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "timestamp": {"type": "string"},
                                            "open": {"type": "string"},
                                            "high": {"type": "string"},
                                            "low": {"type": "string"},
                                            "close": {"type": "string"},
                                            "volume": {"type": "string"}
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
                "path": "/eur_usd/",
                "method": "GET",
                "authentication_required": False,
                "description": "Return EUR/USD conversion rate",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "buy": {"type": "string"},
                        "sell": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/time/",
                "method": "GET",
                "authentication_required": False,
                "description": "Get server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            # Derivatives endpoints (for perpetual contracts)
            {
                "path": "/funding_rate/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Returns current funding rate data for derivatives markets",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "funding_rate": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "market": {"type": "string"},
                        "next_funding_time": {"type": "string"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/funding_rate_history/{market_symbol}/",
                "method": "GET",
                "authentication_required": False,
                "description": "Returns historic funding rate data for derivatives markets",
                "path_parameters": {"market_symbol": "string"},
                "query_parameters": {
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Max number of results"
                    },
                    "since_timestamp": {
                        "type": "integer",
                        "required": False,
                        "description": "Show only funding rates from unix timestamp (max 30 days old)"
                    },
                    "until_timestamp": {
                        "type": "integer",
                        "required": False,
                        "description": "Show only funding rates to unix timestamp (max 30 days old)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "market": {"type": "string"},
                        "funding_rate_history": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "funding_rate": {"type": "string"},
                                    "timestamp": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            # Travel Rule endpoints
            {
                "path": "/travel_rule/vasps/",
                "method": "GET",
                "authentication_required": False,
                "description": "A list of Virtual Asset Service Providers needed to comply with the Travel Rule",
                "query_parameters": {
                    "per_page": {
                        "type": "integer",
                        "required": False,
                        "description": "Results per page"
                    },
                    "page": {
                        "type": "integer",
                        "required": False,
                        "description": "Page number"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array"},
                        "pagination": {"type": "object"}
                    }
                },
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Bitstamp WebSocket channels.

        Returns:
            List of channel dictionaries
        """
        logger.info("Discovering Bitstamp WebSocket channels")

        channels = [
            {
                "channel_name": "live_trades",
                "authentication_required": False,
                "description": "Real-time trade execution data",
                "subscribe_format": {
                    "event": "bts:subscribe",
                    "data": {
                        "channel": "live_trades_{pair}"
                    }
                },
                "unsubscribe_format": {
                    "event": "bts:unsubscribe",
                    "data": {
                        "channel": "live_trades_{pair}"
                    }
                },
                "message_types": ["trade", "subscription_succeeded"],
                "message_schema": {
                    "event": "string",
                    "channel": "string",
                    "data": {
                        "id": "integer",
                        "timestamp": "string",
                        "amount": "string",
                        "price": "string",
                        "type": "integer",
                        "buy_order_id": "integer",
                        "sell_order_id": "integer"
                    }
                }
            },
            {
                "channel_name": "order_book",
                "authentication_required": False,
                "description": "Real-time order book snapshots",
                "subscribe_format": {
                    "event": "bts:subscribe",
                    "data": {
                        "channel": "order_book_{pair}"
                    }
                },
                "unsubscribe_format": {
                    "event": "bts:unsubscribe",
                    "data": {
                        "channel": "order_book_{pair}"
                    }
                },
                "message_types": ["data", "subscription_succeeded"],
                "message_schema": {
                    "event": "string",
                    "channel": "string",
                    "data": {
                        "timestamp": "string",
                        "microtimestamp": "string",
                        "bids": "array of [price, amount]",
                        "asks": "array of [price, amount]"
                    }
                }
            },
            {
                "channel_name": "diff_order_book",
                "authentication_required": False,
                "description": "Real-time order book difference updates",
                "subscribe_format": {
                    "event": "bts:subscribe",
                    "data": {
                        "channel": "diff_order_book_{pair}"
                    }
                },
                "unsubscribe_format": {
                    "event": "bts:unsubscribe",
                    "data": {
                        "channel": "diff_order_book_{pair}"
                    }
                },
                "message_types": ["data", "subscription_succeeded"],
                "message_schema": {
                    "event": "string",
                    "channel": "string",
                    "data": {
                        "timestamp": "string",
                        "microtimestamp": "string",
                        "bids": "array of [price, amount]",
                        "asks": "array of [price, amount]"
                    }
                }
            },
            {
                "channel_name": "live_orders",
                "authentication_required": True,
                "description": "Real-time user order updates (requires authentication)",
                "subscribe_format": {
                    "event": "bts:subscribe",
                    "data": {
                        "channel": "private-my_orders"
                    }
                },
                "unsubscribe_format": {
                    "event": "bts:unsubscribe",
                    "data": {
                        "channel": "private-my_orders"
                    }
                },
                "message_types": ["order_created", "order_changed", "order_deleted", "subscription_succeeded"],
                "message_schema": {
                    "event": "string",
                    "channel": "string",
                    "data": {
                        "id": "integer",
                        "datetime": "string",
                        "type": "integer",
                        "price": "string",
                        "amount": "string",
                        "currency_pair": "string"
                    }
                }
            },
            {
                "channel_name": "ticker",
                "authentication_required": False,
                "description": "Real-time ticker updates",
                "subscribe_format": {
                    "event": "bts:subscribe",
                    "data": {
                        "channel": "live_ticker_{pair}"
                    }
                },
                "unsubscribe_format": {
                    "event": "bts:unsubscribe",
                    "data": {
                        "channel": "live_ticker_{pair}"
                    }
                },
                "message_types": ["ticker", "subscription_succeeded"],
                "message_schema": {
                    "event": "string",
                    "channel": "string",
                    "data": {
                        "timestamp": "string",
                        "bid": "string",
                        "ask": "string",
                        "last": "string",
                        "low": "string",
                        "high": "string",
                        "volume": "string",
                        "vwap": "string",
                        "open": "string"
                    }
                }
            }
        ]

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Bitstamp trading products by fetching from /markets endpoint.

        Returns:
            List of product dictionaries
        """
        logger.info("Discovering Bitstamp products from live API")

        try:
            # Fetch markets from Bitstamp API
            url = f"{self.base_url}/markets/"
            response = self.http_client.get(url)

            products = []
            for item in response:
                # Parse product information
                product = {
                    "symbol": item.get("market_symbol", ""),
                    "name": item.get("name", ""),
                    "base_currency": item.get("base_currency", ""),
                    "quote_currency": item.get("counter_currency", ""),
                    "base_decimals": item.get("base_decimals", 8),
                    "quote_decimals": item.get("counter_decimals", 2),
                    "trading_enabled": item.get("trading", "Enabled") == "Enabled",
                    "market_type": item.get("market_type", "SPOT"),
                    "minimum_order_value": item.get("minimum_order_value", "0.0"),
                    "maximum_order_value": item.get("maximum_order_value", "0.0"),
                    "minimum_order_amount": item.get("minimum_order_amount", "0.0"),
                    "maximum_order_amount": item.get("maximum_order_amount", "0.0"),
                    "instant_and_market_orders": item.get("instant_and_market_orders", "Enabled") == "Enabled",
                    "description": item.get("description", "")
                }

                # Determine available feeds based on market type
                available_rest_feeds = []
                available_ws_channels = []

                # All markets have ticker and order book feeds
                available_rest_feeds.append({
                    "type": "ticker",
                    "endpoint": "/ticker/{market_symbol}/"
                })
                available_rest_feeds.append({
                    "type": "order_book",
                    "endpoint": "/order_book/{market_symbol}/"
                })
                available_rest_feeds.append({
                    "type": "transactions",
                    "endpoint": "/transactions/{market_symbol}/"
                })
                available_rest_feeds.append({
                    "type": "ohlc",
                    "endpoint": "/ohlc/{market_symbol}/",
                    "intervals": [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200]
                })

                # Add funding rate feeds for derivatives markets
                if product["market_type"] in ["PERPETUAL", "FUTURES"]:
                    available_rest_feeds.append({
                        "type": "funding_rate",
                        "endpoint": "/funding_rate/{market_symbol}/"
                    })
                    available_rest_feeds.append({
                        "type": "funding_rate_history",
                        "endpoint": "/funding_rate_history/{market_symbol}/"
                    })

                # WebSocket channels
                available_ws_channels.extend([
                    "live_trades",
                    "order_book",
                    "diff_order_book",
                    "ticker"
                ])

                # Add feed information to product
                product["available_rest_feeds"] = available_rest_feeds
                product["available_ws_channels"] = available_ws_channels

                products.append(product)

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover Bitstamp products: {e}")
            raise

    def get_candle_intervals(self) -> List[int]:
        """
        Get available candle intervals for OHLC data.

        Returns:
            List of interval seconds
        """
        return [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200]

    def validate_endpoint(self, endpoint: Dict[str, Any]) -> bool:
        """
        Validate an endpoint configuration.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            True if endpoint is valid
        """
        required_fields = ["path", "method", "authentication_required", "description"]
        for field in required_fields:
            if field not in endpoint:
                logger.warning(f"Endpoint missing required field: {field}")
                return False
        return True

    def test_websocket_channel(self, channel_name: str, pair: str = "btcusd") -> bool:
        """
        Test WebSocket channel connectivity (placeholder for actual test).

        Args:
            channel_name: Channel name to test
            pair: Trading pair for channel

        Returns:
            True if channel test successful
        """
        logger.info(f"Testing WebSocket channel: {channel_name} for pair: {pair}")
        # This is a placeholder - actual WebSocket testing would connect and verify
        return True
