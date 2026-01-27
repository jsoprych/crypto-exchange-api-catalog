# src/utils/http_client.py
"""
HTTP client utilities for API requests.
"""

import requests
from typing import Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import HTTP_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """
    HTTP client with retry logic and error handling.
    """

    def __init__(
        self,
        timeout: int = HTTP_CONFIG["timeout"],
        max_retries: int = HTTP_CONFIG["max_retries"],
        backoff_factor: float = HTTP_CONFIG["backoff_factor"]
    ):
        """
        Initialize HTTP client with retry configuration.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential backoff
        """
        self.timeout = timeout
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "User-Agent": HTTP_CONFIG["user_agent"]
        })

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform GET request with error handling.

        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: On request failure
        """
        try:
            logger.debug(f"GET request to {url}")
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise

    def close(self):
        """Close the session."""
        self.session.close()
