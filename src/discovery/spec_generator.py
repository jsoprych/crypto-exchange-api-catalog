# src/discovery/spec_generator.py
"""
API specification generator orchestrates the discovery process.

This module coordinates the end-to-end discovery of vendor API specifications,
including REST endpoints, WebSocket channels, and trading products.
"""

import time
from typing import Dict, List, Any, Optional

from src.adapters.base_adapter import BaseVendorAdapter
from src.adapters.coinbase_adapter import CoinbaseAdapter
from src.adapters.binance_adapter import BinanceAdapter
from src.adapters.kraken_adapter import KrakenAdapter
from src.adapters.bitfinex_adapter import BitfinexAdapter
from src.adapters.bybit_adapter import BybitAdapter
from src.adapters.okx_adapter import OkxAdapter
from src.adapters.kucoin_adapter import KucoinAdapter
from src.adapters.gateio_adapter import GateioAdapter
from src.adapters.huobi_adapter import HuobiAdapter
from src.adapters.mexc_adapter import MexcAdapter
from src.adapters.bitstamp_adapter import BitstampAdapter
from src.adapters.bitget_adapter import BitgetAdapter
from src.adapters.bitmart_adapter import BitmartAdapter
from src.adapters.crypto_com_adapter import Crypto_comAdapter
from src.adapters.gemini_adapter import GeminiAdapter
from src.adapters.poloniex_adapter import PoloniexAdapter
from src.adapters.deribit_adapter import DeribitAdapter
from src.adapters.phemex_adapter import PhemexAdapter
from src.database.repository import SpecificationRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpecificationGenerator:
    """
    Orchestrates the API specification discovery process.
    """

    def __init__(self, repository: SpecificationRepository):
        """
        Initialize specification generator.

        Args:
            repository: Database repository instance
        """
        self.repository = repository

    def generate_specification(
        self,
        vendor_name: str,
        vendor_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete API specification for a vendor.

        Args:
            vendor_name: Vendor name
            vendor_config: Vendor configuration

        Returns:
            Dictionary with discovery statistics and results
        """
        logger.info(f"Starting API specification generation for {vendor_name}")
        start_time = time.time()

        # Add vendor_name to config
        vendor_config['vendor_name'] = vendor_name

        # Get or create vendor in database
        vendor_id = self.repository.get_or_create_vendor(vendor_config)

        # Start discovery run
        run_id = self.repository.start_discovery_run(
            vendor_id,
            discovery_method='live_api_probing'
        )

        try:
            # Create vendor adapter
            adapter = self._create_adapter(vendor_name, vendor_config)

            # Phase 1: Discover REST endpoints
            logger.info("Phase 1: Discovering REST endpoints")
            endpoints = adapter.discover_rest_endpoints()
            endpoint_ids = self._save_endpoints(vendor_id, endpoints, run_id)

            # Phase 2: Discover WebSocket channels
            logger.info("Phase 2: Discovering WebSocket channels")
            channels = adapter.discover_websocket_channels()
            channel_ids = self._save_channels(vendor_id, channels, run_id)

            # Phase 3: Discover products
            logger.info("Phase 3: Discovering products")
            products = adapter.discover_products()
            product_ids = self._save_products(vendor_id, products, run_id)

            # Phase 4: Link products to feeds
            logger.info("Phase 4: Linking products to endpoints and channels")
            self._link_product_feeds(
                vendor_name,
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )

            # Calculate statistics
            duration = time.time() - start_time
            stats = {
                'endpoints_discovered': len(endpoints),
                'websocket_channels_discovered': len(channels),
                'products_discovered': len(products)
            }

            # Mark discovery run as complete
            self.repository.complete_discovery_run(
                run_id,
                duration,
                stats,
                success=True
            )

            logger.info(
                f"Specification generation complete: "
                f"{stats['products_discovered']} products, "
                f"{stats['endpoints_discovered']} endpoints, "
                f"{stats['websocket_channels_discovered']} channels "
                f"in {duration:.2f}s"
            )

            return {
                'success': True,
                'run_id': run_id,
                'vendor_id': vendor_id,
                'duration': duration,
                **stats
            }

        except Exception as e:
            # Mark discovery run as failed
            duration = time.time() - start_time
            self.repository.complete_discovery_run(
                run_id,
                duration,
                {'endpoints_discovered': 0, 'websocket_channels_discovered': 0, 'products_discovered': 0},
                success=False,
                error_message=str(e)
            )

            logger.error(f"Specification generation failed: {e}")
            raise

    def _create_adapter(
        self,
        vendor_name: str,
        vendor_config: Dict[str, Any]
    ) -> BaseVendorAdapter:
        """
        Create appropriate adapter for vendor.

        Args:
            vendor_name: Vendor name
            vendor_config: Vendor configuration

        Returns:
            Vendor adapter instance
        """
        if vendor_name == 'coinbase':
            return CoinbaseAdapter(vendor_config)
        elif vendor_name == 'binance':
            return BinanceAdapter(vendor_config)
        elif vendor_name == 'kraken':
            return KrakenAdapter(vendor_config)
        elif vendor_name == 'bitfinex':
            return BitfinexAdapter(vendor_config)
        elif vendor_name == 'bybit':
            return BybitAdapter(vendor_config)
        elif vendor_name == 'okx':
            return OkxAdapter(vendor_config)
        elif vendor_name == 'kucoin':
            return KucoinAdapter(vendor_config)
        elif vendor_name == 'gateio':
            return GateioAdapter(vendor_config)
        elif vendor_name == 'huobi':
            return HuobiAdapter(vendor_config)
        elif vendor_name == 'mexc':
            return MexcAdapter(vendor_config)
        elif vendor_name == 'bitstamp':
            return BitstampAdapter(vendor_config)
        elif vendor_name == 'bitget':
            return BitgetAdapter(vendor_config)
        elif vendor_name == 'bitmart':
            return BitmartAdapter(vendor_config)
        elif vendor_name == 'crypto_com':
            return Crypto_comAdapter(vendor_config)
        elif vendor_name == 'gemini':
            return GeminiAdapter(vendor_config)
        elif vendor_name == 'poloniex':
            return PoloniexAdapter(vendor_config)
        elif vendor_name == 'deribit':
            return DeribitAdapter(vendor_config)
                elif vendor_name == 'phemex':
            return PhemexAdapter(vendor_config)
        else:
            raise ValueError(f"Unknown vendor: {vendor_name}")

    def _save_endpoints(
        self,
        vendor_id: int,
        endpoints: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save REST endpoints to database.

        Args:
            vendor_id: Vendor ID
            endpoints: List of endpoint dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping endpoint paths to endpoint IDs
        """
        endpoint_ids = {}

        for endpoint in endpoints:
            endpoint_id = self.repository.save_rest_endpoint(
                vendor_id,
                endpoint,
                run_id
            )
            key = f"{endpoint['method']} {endpoint['path']}"
            endpoint_ids[key] = endpoint_id

            logger.debug(f"Saved endpoint: {key}")

        return endpoint_ids

    def _save_channels(
        self,
        vendor_id: int,
        channels: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save WebSocket channels to database.

        Args:
            vendor_id: Vendor ID
            channels: List of channel dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping channel names to channel IDs
        """
        channel_ids = {}

        for channel in channels:
            channel_id = self.repository.save_websocket_channel(
                vendor_id,
                channel,
                run_id
            )
            channel_ids[channel['channel_name']] = channel_id

            logger.debug(f"Saved channel: {channel['channel_name']}")

        return channel_ids

    def _save_products(
        self,
        vendor_id: int,
        products: list,
        run_id: int
    ) -> Dict[str, int]:
        """
        Save products to database.

        Args:
            vendor_id: Vendor ID
            products: List of product dictionaries
            run_id: Discovery run ID

        Returns:
            Dictionary mapping symbols to product IDs
        """
        product_ids = {}

        for product in products:
            product_id = self.repository.save_product(
                vendor_id,
                product,
                run_id
            )
            product_ids[product['symbol']] = product_id

            logger.debug(f"Saved product: {product['symbol']}")

        return product_ids

    def _link_product_feeds(
        self,
        vendor_name: str,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link products to their available endpoints and channels.

        Args:
            vendor_name: Vendor name
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: Vendor adapter instance
        """
        # Vendor-specific linking logic
        if vendor_name == 'coinbase':
            self._link_coinbase_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'binance':
            self._link_binance_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'kraken':
            self._link_kraken_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'bitfinex':
            self._link_bitfinex_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'okx':
            self._link_okx_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'kucoin':
            self._link_kucoin_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'gateio':
            self._link_gateio_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'huobi':
            self._link_huobi_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'bitget':
            self._link_bitget_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )
        elif vendor_name == 'bitmart':
            self._link_bitmart_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )

    def _link_coinbase_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: CoinbaseAdapter
    ):
        """
        Link Coinbase products to their feeds.

        Args:
            product_ids: Product IDs by symbol
            endpoint_ids: Endpoint IDs by key
            channel_ids: Channel IDs by name
            adapter: Coinbase adapter instance
        """
        # Get candle intervals
        candle_intervals = adapter.get_candle_intervals()

        # Link each product to available feeds
        for symbol, product_id in product_ids.items():
            # REST feeds
            # Ticker
            ticker_key = "GET /products/{product_id}/ticker"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Candles
            candles_key = "GET /products/{product_id}/candles"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles',
                    intervals=candle_intervals
                )

            # Trades
            trades_key = "GET /products/{product_id}/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Order book
            book_key = "GET /products/{product_id}/book"
            if book_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[book_key],
                    'orderbook'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                if channel_name != 'status':  # Status channel doesn't use product_ids
                    self.repository.link_product_to_ws_channel(
                        product_id,
                        channel_id
                    )

        logger.info(f"Linked {len(product_ids)} products to feeds")

    def _link_binance_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BinanceAdapter
    ):
        """
        Link Binance products to their feeds.

        Args:
            product_ids: Product IDs by symbol
            endpoint_ids: Endpoint IDs by key
            channel_ids: Channel IDs by name
            adapter: Binance adapter instance
        """
        # Get kline intervals
        kline_intervals = adapter.get_kline_intervals()

        # Link each product to available feeds
        for symbol, product_id in product_ids.items():
            # REST feeds
            # Ticker (24hr)
            ticker_key = "GET /api/v3/ticker/24hr"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Klines (candlesticks)
            klines_key = "GET /api/v3/klines"
            if klines_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[klines_key],
                    'candles',
                    intervals=kline_intervals
                )

            # Trades
            trades_key = "GET /api/v3/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Order book (depth)
            depth_key = "GET /api/v3/depth"
            if depth_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[depth_key],
                    'orderbook'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} Binance products to feeds")

    def _link_kraken_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: KrakenAdapter
    ):
        """
        Link Kraken products to their feeds.

        Args:
            product_ids: Product IDs by symbol
            endpoint_ids: Endpoint IDs by key
            channel_ids: Channel IDs by name
            adapter: Kraken adapter instance
        """
        # Get OHLC intervals
        ohlc_intervals = adapter.get_ohlc_intervals()

        # Link each product to available feeds
        for symbol, product_id in product_ids.items():
            # REST feeds
            # Ticker
            ticker_key = "GET /0/public/Ticker"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # OHLC (candlesticks)
            ohlc_key = "GET /0/public/OHLC"
            if ohlc_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ohlc_key],
                    'candles',
                    intervals=ohlc_intervals
                )

            # Trades
            trades_key = "GET /0/public/Trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Order book (Depth)
            depth_key = "GET /0/public/Depth"
            if depth_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[depth_key],
                    'orderbook'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} Kraken products to feeds")

    def _link_bitfinex_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BitfinexAdapter
    ):
        """
        Link Bitfinex products to their feeds.

        Args:
            product_ids: Product IDs by symbol
            endpoint_ids: Endpoint IDs by key
            channel_ids: Channel IDs by name
            adapter: Bitfinex adapter instance
        """
        # Get candle timeframes
        candle_timeframes = adapter.get_candle_timeframes()

        # Link each product to available feeds
        for symbol, product_id in product_ids.items():
            # REST feeds
            # Ticker
            ticker_key = "GET /v2/ticker/{symbol}"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Candles
            candles_key = "GET /v2/candles/trade:{timeframe}:{symbol}/hist"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles',
                    intervals=candle_timeframes
                )

            # Trades
            trades_key = "GET /v2/trades/{symbol}/hist"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Order book
            book_key = "GET /v2/book/{symbol}/{precision}"
            if book_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[book_key],
                    'orderbook'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} Bitfinex products to feeds")

    def _link_okx_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link OKX products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: OkxAdapter instance
        """
        logger.info("Linking OKX products to feeds")

        # Get candle intervals from adapter
        candle_timeframes = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints
            # Ticker endpoint
            ticker_key = "GET /api/v5/market/ticker"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Order book endpoint
            books_key = "GET /api/v5/market/books"
            if books_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[books_key],
                    'orderbook'
                )

            # Candlestick endpoint
            candles_key = "GET /api/v5/market/candles"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles'
                )

            # Trades endpoint
            trades_key = "GET /api/v5/market/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} OKX products to feeds")

    def _link_kucoin_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link KuCoin products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: KucoinAdapter instance
        """
        logger.info("Linking KuCoin products to feeds")

        # Get candle intervals from adapter
        candle_timeframes = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints
            # Ticker endpoint (all tickers)
            ticker_key = "GET /api/v1/market/allTickers"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Order book endpoint
            orderbook_key = "GET /api/v1/market/orderbook/level2_20"
            if orderbook_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[orderbook_key],
                    'orderbook'
                )

            # Candlestick endpoint
            candles_key = "GET /api/v1/market/candles"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles'
                )

            # Trades endpoint
            trades_key = "GET /api/v1/market/histories"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} KuCoin products to feeds")

    def _link_gateio_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Gate.io products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: GateioAdapter instance
        """
        logger.info("Linking Gate.io products to feeds")

        # Get candle intervals from adapter
        candle_timeframes = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints
            # Ticker endpoint
            ticker_key = "GET /api/v4/spot/tickers"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Order book endpoint
            orderbook_key = "GET /api/v4/spot/order_book"
            if orderbook_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[orderbook_key],
                    'orderbook'
                )

            # Candlestick endpoint
            candles_key = "GET /api/v4/spot/candlesticks"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles'
                )

            # Trades endpoint
            trades_key = "GET /api/v4/spot/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} Gate.io products to feeds")

    def _link_huobi_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Huobi products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: HuobiAdapter instance
        """
        logger.info("Linking Huobi products to feeds")

        # Get candle intervals from adapter
        candle_timeframes = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints
            # Ticker endpoint (market/tickers)
            ticker_key = "GET /market/tickers"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Order book endpoint
            orderbook_key = "GET /market/depth"
            if orderbook_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[orderbook_key],
                    'orderbook'
                )

            # Candlestick endpoint
            candles_key = "GET /market/history/kline"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles'
                )

            # Trades endpoint
            trades_key = "GET /market/history/trade"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )

        logger.info(f"Linked {len(product_ids)} Huobi products to feeds")

    def _link_bitget_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Bitget products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: BitgetAdapter instance
        """
        logger.info("Linking Bitget products to feeds")

        # Get candle intervals from adapter
        candle_intervals = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints
            # Ticker endpoint (all tickers)
            ticker_key = "GET /api/spot/v1/market/tickers"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Single ticker endpoint (specific symbol)
            single_ticker_key = "GET /api/spot/v1/market/ticker"
            if single_ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[single_ticker_key],
                    'ticker'
                )

            # Order book depth endpoint
            depth_key = "GET /api/spot/v1/market/depth"
            if depth_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[depth_key],
                    'orderbook'
                )

            # Merged depth endpoint
            merge_depth_key = "GET /api/spot/v1/market/merge-depth"
            if merge_depth_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[merge_depth_key],
                    'orderbook'
                )

            # Candlestick endpoint
            candles_key = "GET /api/spot/v1/market/candles"
            if candles_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[candles_key],
                    'candles',
                    intervals=candle_intervals
                )

            # Trades endpoint (fills)
            fills_key = "GET /api/spot/v1/market/fills"
            if fills_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[fills_key],
                    'trades'
                )

            # Trade history endpoint
            fills_history_key = "GET /api/spot/v1/market/fills-history"
            if fills_history_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[fills_history_key],
                    'trades'
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )
    def _link_bitmart_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Bitmart products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: BitmartAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Bitmart products to feeds")

        # Get candle intervals from adapter
        candle_intervals = adapter.get_candle_intervals()

        for symbol, product_id in product_ids.items():
            # REST endpoints

            # Ticker endpoint (all tickers)
            ticker_key = "GET /spot/v1/ticker"
            if ticker_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_key],
                    'ticker'
                )

            # Single ticker detail endpoint
            ticker_detail_key = "GET /spot/v1/ticker/detail"
            if ticker_detail_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[ticker_detail_key],
                    'ticker'
                )

            # Order book endpoint
            orderbook_key = "GET /spot/v1/symbols/book"
            if orderbook_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[orderbook_key],
                    'orderbook'
                )

            # Order book depth v3 endpoint
            orderbook_v3_key = "GET /spot/quotation/v3/books"
            if orderbook_v3_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[orderbook_v3_key],
                    'orderbook'
                )

            # Trades endpoint
            trades_key = "GET /spot/v1/symbols/trades"
            if trades_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_key],
                    'trades'
                )

            # Trades v3 endpoint
            trades_v3_key = "GET /spot/quotation/v3/trades"
            if trades_v3_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[trades_v3_key],
                    'trades'
                )

            # K-line endpoint
            kline_key = "GET /spot/v1/symbols/kline"
            if kline_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[kline_key],
                    'candles',
                    intervals=candle_intervals
                )

            # K-line v3 endpoint
            kline_v3_key = "GET /spot/quotation/v3/klines"
            if kline_v3_key in endpoint_ids:
                self.repository.link_product_to_endpoint(
                    product_id,
                    endpoint_ids[kline_v3_key],
                    'candles',
                    intervals=candle_intervals
                )

            # WebSocket channels - all products support all channels
            for channel_name, channel_id in channel_ids.items():
                self.repository.link_product_to_ws_channel(
                    product_id,
                    channel_id
                )
    def _link_crypto_com_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Crypto_com products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: Crypto_comAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Crypto_com products to feeds")

        # TODO: Implement Crypto_com-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass

    def _link_gemini_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Gemini products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: GeminiAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Gemini products to feeds")

        # TODO: Implement Gemini-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass

    def _link_poloniex_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Poloniex products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: PoloniexAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Poloniex products to feeds")
    def _link_deribit_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Deribit products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: DeribitAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Deribit products to feeds")

        # TODO: Implement Deribit-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass

    def _link_phemex_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link Phemex products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: PhemexAdapter instance
        """
        logger.info(f"Linking {len(product_ids)} Phemex products to feeds")

        # TODO: Implement Phemex-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass


        # TODO: Implement Poloniex-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass
