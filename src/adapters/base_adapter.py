# src/adapters/base_adapter.py
"""
Base adapter interface for vendor API discovery.
All vendor-specific adapters must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from src.utils.http_client import HTTPClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseVendorAdapter(ABC):
    """
    Abstract base class for vendor API adapters.
    Each vendor implements this interface to provide API discovery.
    """

    def __init__(self, config: Dict[str, Any], http_client: Optional[HTTPClient] = None):
        """
        Initialize vendor adapter.

        Args:
            config: Vendor configuration dictionary
            http_client: HTTP client instance (optional, creates new if None)
        """
        self.config = config
        self.http_client = http_client or HTTPClient()
        self.vendor_name = config.get('vendor_name', 'unknown')
        self.base_url = config['base_url']
        self.websocket_url = config.get('websocket_url')

    @abstractmethod
    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover all REST API endpoints.

        Returns:
            List of endpoint dictionaries with keys:
            - path: str
            - method: str
            - authentication_required: bool
            - description: str (optional)
            - path_parameters: dict (optional)
            - query_parameters: dict (optional)
            - response_schema: dict (optional)
            - vendor_metadata: dict (optional)
        """
        pass

    @abstractmethod
    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover all WebSocket channels.

        Returns:
            List of channel dictionaries with keys:
            - channel_name: str
            - authentication_required: bool
            - description: str (optional)
            - subscribe_format: dict (optional)
            - unsubscribe_format: dict (optional)
            - message_types: list (optional)
            - message_schema: dict (optional)
            - vendor_metadata: dict (optional)
        """
        pass

    @abstractmethod
    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover all trading products/symbols.

        Returns:
            List of product dictionaries with keys:
            - symbol: str
            - base_currency: str
            - quote_currency: str
            - status: str (online, offline, delisted)
            - min_order_size: float (optional)
            - max_order_size: float (optional)
            - price_increment: float (optional)
            - vendor_metadata: dict (optional)
        """
        pass

    def validate_endpoint(self, endpoint: Dict[str, Any]) -> bool:
        """
        Validate that an endpoint is accessible (optional override).

        Args:
            endpoint: Endpoint dictionary

        Returns:
            True if endpoint is accessible, False otherwise
        """
        try:
            url = self.base_url + endpoint['path']
            self.http_client.get(url)
            return True
        except Exception as e:
            logger.warning(f"Endpoint validation failed for {endpoint['path']}: {e}")
            return False

    def test_websocket_channel(self, channel: Dict[str, Any]) -> bool:
        """
        Test WebSocket channel connectivity (optional override).

        Args:
            channel: Channel dictionary

        Returns:
            True if channel is accessible, False otherwise
        """
        # Default implementation - can be overridden by specific adapters
        logger.debug(f"WebSocket test not implemented for {channel['channel_name']}")
        return True

    def close(self):
        """Clean up resources."""
        if self.http_client:
            self.http_client.close()
