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
        "display_name": "Binance US",
        "base_url": "https://api.binance.us",
        "websocket_url": "wss://stream.binance.us:9443",
        "documentation_url": "https://docs.binance.us/",
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
    },
    "bybit": {
        "enabled": True,
        "display_name": "Bybit",
        "base_url": "https://api.bybit.com",
        "websocket_url": "wss://stream.bybit.com/v5/public/spot",
        "documentation_url": "https://bybit-exchange.github.io/docs/v5/intro",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "tickers": "/v5/market/tickers",
            "orderbook": "/v5/market/orderbook",
            "klines": "/v5/market/kline",
            "time": "/v5/market/time"
        },
        "rate_limits": {
            "public": 50  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
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
            "public": 20  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False,  # Phase 1: public only
        }
    },
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
            "public": 20  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "gateio": {
        "enabled": True,
        "display_name": "Gate.io Exchange",
        "base_url": "https://api.gateio.ws",
        "websocket_url": "wss://ws.gateio.io/v3",
        "documentation_url": "https://www.gate.io/docs/developers/apiv4/en/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "currency_pairs": "/api/v4/spot/currency_pairs",
            "time": "/api/v4/spot/time",
            "tickers": "/api/v4/spot/tickers"
        },
        "rate_limits": {
            "public": 20  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "huobi": {
        "enabled": True,
        "display_name": "Huobi Exchange",
        "base_url": "https://api.huobi.pro",
        "websocket_url": "wss://api.huobi.pro/ws",
        "documentation_url": "https://huobiapi.github.io/docs/spot/v1/en/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "symbols": "/v1/common/symbols",
            "time": "/v1/common/timestamp",
            "tickers": "/market/tickers"
        },
        "rate_limits": {
            "public": 10  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "mexc": {
        "enabled": True,
        "display_name": "MEXC Exchange",
        "base_url": "https://api.mexc.com",
        "websocket_url": "wss://wbs.mexc.com/ws",
        "documentation_url": "https://mexcdevelop.github.io/apidocs/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "exchange_info": "/api/v3/exchangeInfo",
            "time": "/api/v3/time",
            "tickers": "/api/v3/ticker/24hr"
        },
        "rate_limits": {
            "public": 20,  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False,  # Phase 1: public only
        }
    },
    "bitstamp": {
        "enabled": True,
        "display_name": "Bitstamp",
        "base_url": "https://www.bitstamp.net/api/v2",
        "websocket_url": "wss://ws.bitstamp.net",
        "documentation_url": "https://www.bitstamp.net/api/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "trading_pairs": "/trading-pairs-info/",
            "ticker": "/ticker/{currency_pair}/",
            "order_book": "/order_book/{currency_pair}/",
            "time": "/time/"
        },
        "rate_limits": {
            "public": 10,  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False,  # Phase 1: public only
        }
    },
    "bitget": {
        "enabled": True,
        "display_name": "Bitget Exchange",
        "base_url": "https://api.bitget.com",
        "websocket_url": "wss://ws.bitget.com/spot/v1/stream",
        "documentation_url": "https://bitgetlimited.github.io/apidoc/en/spot/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/api/spot/v1/public/products",
            "time": "/api/spot/v1/public/time",
            "tickers": "/api/spot/v1/market/tickers",
            "depth": "/api/spot/v1/market/depth",
            "fills": "/api/spot/v1/market/fills",
            "candles": "/api/spot/v1/market/candles"
        },
        "rate_limits": {
            "public": 20,  # requests per second (approximate)
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False,  # Phase 1: public only
        }
    },
    "bitmart": {
        "enabled": True,
        "display_name": "Bitmart Exchange",
        "base_url": "https://api-cloud.bitmart.com",
        "websocket_url": "wss://ws-manager-compress.bitmart.com",
        "documentation_url": "https://developer-pro.bitmart.com/en/spot",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/spot/v1/symbols",
            "time": "/system/time",
            "tickers": "/spot/v1/ticker"
        },
        "rate_limits": {
            "public": 20,  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False,  # Phase 1: public only
        }
    },
    "crypto_com": {
        "enabled": True,
        "display_name": "Crypto.com Exchange",
        "base_url": "https://api.crypto.com/exchange/v1",
        "websocket_url": "wss://stream.crypto.com/exchange/v1/market",
        "documentation_url": "https://exchange-docs.crypto.com/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/public/get-instruments",
            "tickers": "/public/get-tickers",
            "order_book": "/public/get-book",
            "trades": "/public/get-trades",
            "candlestick": "/public/get-candlestick"
        },
        "rate_limits": {
            "public": 100  # Based on documentation: 100 requests per second for public market data
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "gemini": {
        "enabled": True,
        "display_name": "Gemini Exchange",
        "base_url": "https://api.gemini.com/v1",
        "websocket_url": "wss://api.gemini.com/v1/marketdata",
        "documentation_url": "https://docs.gemini.com/rest-api/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/symbols",
            "pricefeed": "/pricefeed",  # Current prices for all pairs
            "pubticker": "/pubticker/{symbol}",  # Ticker for specific symbol
            "book": "/book/{symbol}",  # Order book for specific symbol
            "trades": "/trades/{symbol}",  # Recent trades for specific symbol
            "symbol_details": "/symbols/details/{symbol}"  # Symbol details
        },
        "rate_limits": {
            "public": 20  # Based on documentation: 20 requests per minute
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "poloniex": {
        "enabled": True,
        "display_name": "Poloniex Exchange",
        "base_url": "https://api.poloniex.com",
        "websocket_url": "wss://ws.poloniex.com/ws",
        "documentation_url": "https://docs.poloniex.com",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/markets",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "deribit": {
        "enabled": True,
        "display_name": "Deribit Exchange",
        "base_url": "https://www.deribit.com/api/v2",
        "websocket_url": "wss://www.deribit.com/ws/api/v2",
        "documentation_url": "https://docs.deribit.com",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/public/get_instruments",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "phemex": {
        "enabled": True,
        "display_name": "Phemex Exchange",
        "base_url": "https://api.phemex.com",
        "websocket_url": "wss://ws.phemex.com",
        "documentation_url": "https://github.com/phemex/phemex-api-docs",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/public/products",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "lbank": {
        "enabled": True,
        "display_name": "Lbank Exchange",
        "base_url": "https://api.lbank.info",
        "websocket_url": "wss://api.lbank.info/ws",
        "documentation_url": "https://www.lbank.info/en-US/docs/index.html",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/v2/currencyPairs.do",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "whitebit": {
        "enabled": True,
        "display_name": "Whitebit Exchange",
        "base_url": "https://whitebit.com",
        "websocket_url": "wss://whitebit.com/ws",
        "documentation_url": "https://whitebit.com/api/v4/doc",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/api/v4/public/markets",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "upbit": {
        "enabled": True,
        "display_name": "Upbit Exchange",
        "base_url": "https://api.upbit.com",
        "websocket_url": "wss://api.upbit.com/websocket/v1",
        "documentation_url": "https://docs.upbit.com/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/v1/market/all",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "bithumb": {
        "enabled": True,
        "display_name": "Bithumb Exchange",
        "base_url": "https://api.bithumb.com",
        "websocket_url": "wss://ws-api.bithumb.com/websocket/v1",
        "documentation_url": "https://apidocs.bithumb.com/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/v1/market/all",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "korbit": {
        "enabled": True,
        "display_name": "Korbit Exchange",
        "base_url": "https://api.korbit.co.kr",
        "websocket_url": "wss://ws.korbit.co.kr",
        "documentation_url": "https://apidocs.korbit.co.kr/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/v1/constants",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
    "zaif": {
        "enabled": True,
        "display_name": "Zaif Exchange",
        "base_url": "https://api.zaif.jp",
        "websocket_url": "wss://api.zaif.jp",
        "documentation_url": "https://zaif-api-document.readthedocs.io/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/api/1/ticker",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        },
        "rate_limits": {
            "public": 20  # UPDATE: Set actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }
    },
}

# Discovery process configuration
DISCOVERY_CONFIG = {
    "validate_live_api": True,
    "test_websocket_connections": True,
    "capture_response_schemas": True,
    "max_products_sample": None,  # None = all products, or set a number for testing
}
