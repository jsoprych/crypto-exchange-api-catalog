# config/settings.py
"""
Configuration settings for the Vendor API Specification generator.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Database configuration
DATABASE_PATH = PROJECT_ROOT / "data" / "specifications.db"

# Output configuration
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_CONFIG = {
    "naming_convention": "snake_case",  # or "camelCase"
    "include_vendor_metadata": True,
    "schema_version": "1.0",
    "pretty_print": True,
    "indent": 2
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": str(PROJECT_ROOT / "api_spec_generator.log"),
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

# HTTP client configuration
HTTP_CONFIG = {
    "timeout": 30,  # seconds
    "max_retries": 3,
    "backoff_factor": 1.0,  # exponential backoff
    "user_agent": "VendorAPISpecGenerator/1.0"
}

# Vendor configurations
VENDORS = {
    "coinbase": {
        "enabled": True,
        "display_name": "Coinbase Exchange",
        "base_url": "https://api.exchange.coinbase.com",
        "websocket_url": "wss://ws-feed.exchange.coinbase.com",
        "documentation_url": "https://docs.cloud.coinbase.com/exchange/reference/",
        "discovery_methods": ["live_api_probing"],  # Phase 1: live only
        "endpoints": {
            "products": "/products",
            "time": "/time",
            "currencies": "/currencies"
        },
        "rate_limits": {
            "public": 10  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "binance": {
        "enabled": True,
        "display_name": "Binance",
        "base_url": "https://api.binance.com",
        "websocket_url": "wss://stream.binance.com:9443",
        "documentation_url": "https://binance-docs.github.io/apidocs/spot/en/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "exchange_info": "/api/v3/exchangeInfo",
            "time": "/api/v3/time",
            "ping": "/api/v3/ping"
        },
        "rate_limits": {
            "public": 20  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "kraken": {
        "enabled": True,
        "display_name": "Kraken",
        "base_url": "https://api.kraken.com",
        "websocket_url": "wss://ws.kraken.com",
        "documentation_url": "https://docs.kraken.com/rest/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "asset_pairs": "/0/public/AssetPairs",
            "time": "/0/public/Time",
            "system_status": "/0/public/SystemStatus"
        },
        "rate_limits": {
            "public": 20  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "bitfinex": {
        "enabled": True,
        "display_name": "Bitfinex",
        "base_url": "https://api-pub.bitfinex.com",
        "websocket_url": "wss://api-pub.bitfinex.com/ws/2",
        "documentation_url": "https://docs.bitfinex.com/docs",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "platform_status": "/v2/platform/status",
            "pair_list": "/v2/conf/pub:list:pair:exchange",
            "tickers": "/v2/tickers"
        },
        "rate_limits": {
            "public": 30  # requests per minute (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    }
}

# Discovery process configuration
DISCOVERY_CONFIG = {
    "validate_live_api": True,
    "test_websocket_connections": True,
    "capture_response_schemas": True,
    "max_products_sample": None,  # None = all products, or set a number for testing
}
