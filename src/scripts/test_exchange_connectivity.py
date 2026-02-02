#!/usr/bin/env python3
"""
Exchange Connectivity Test Script

Tests connectivity to cryptocurrency exchange APIs from the current location.
Detects geographic restrictions, API availability, and network issues.

Usage:
  python test_exchange_connectivity.py                     # Test all exchanges
  python test_exchange_connectivity.py coinbase binance    # Test specific exchanges
  python test_exchange_connectivity.py --verbose          # Detailed output
  python test_exchange_connectivity.py --report           # Generate HTML report
  python test_exchange_connectivity.py --ws-test          # Include WebSocket tests
"""

import argparse
import asyncio
import json
import sys
import time
import aiohttp
import websockets
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import concurrent.futures

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import VENDORS


class ExchangeConnectivityTester:
    """
    Tests connectivity to cryptocurrency exchange APIs.
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize tester with timeout settings.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.results = {}
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_http_endpoint(self, exchange_name: str, url: str) -> Dict[str, Any]:
        """
        Test HTTP endpoint connectivity.

        Args:
            exchange_name: Name of the exchange
            url: URL to test

        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        result = {
            'exchange': exchange_name,
            'url': url,
            'success': False,
            'response_time_ms': None,
            'status_code': None,
            'error': None,
            'response_headers': {},
            'geo_blocked': False,
            'cloudfront_block': False,
            'test_time': datetime.utcnow().isoformat() + 'Z'
        }

        try:
            async with self.session.get(url, allow_redirects=False) as response:
                elapsed_ms = (time.time() - start_time) * 1000

                result.update({
                    'success': True,
                    'status_code': response.status,
                    'response_time_ms': round(elapsed_ms, 2),
                    'response_headers': dict(response.headers)
                })

                # Check for geographic restrictions
                if response.status == 403:
                    response_text = await response.text()
                    if 'CloudFront' in response_text:
                        result['cloudfront_block'] = True
                        result['geo_blocked'] = True
                    elif 'Forbidden' in response_text or 'restricted' in response_text.lower():
                        result['geo_blocked'] = True

                elif response.status == 301 or response.status == 302:
                    # Redirect might indicate geographic restriction
                    location = response.headers.get('Location', '')
                    if 'restricted' in location.lower() or 'forbidden' in location.lower():
                        result['geo_blocked'] = True

        except aiohttp.ClientError as e:
            result['error'] = str(e)

            # Detect common geographic restriction patterns
            error_str = str(e).lower()
            if 'forbidden' in error_str or '403' in error_str:
                result['geo_blocked'] = True
            if 'cloudfront' in error_str:
                result['cloudfront_block'] = True

        except asyncio.TimeoutError:
            result['error'] = f"Timeout after {self.timeout} seconds"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"

        return result

    async def test_websocket_endpoint(self, exchange_name: str, url: str) -> Dict[str, Any]:
        """
        Test WebSocket endpoint connectivity.

        Args:
            exchange_name: Name of the exchange
            url: WebSocket URL to test

        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        result = {
            'exchange': exchange_name,
            'url': url,
            'success': False,
            'connection_time_ms': None,
            'error': None,
            'test_time': datetime.utcnow().isoformat() + 'Z',
            'protocol': 'websocket'
        }

        try:
            # Try to establish WebSocket connection with short timeout
            async with websockets.connect(url, timeout=5) as ws:
                elapsed_ms = (time.time() - start_time) * 1000
                result.update({
                    'success': True,
                    'connection_time_ms': round(elapsed_ms, 2)
                })

                # Try to send a ping to verify connection is alive
                pong = await asyncio.wait_for(ws.ping(), timeout=2)
                if pong:
                    result['ping_success'] = True

        except asyncio.TimeoutError:
            result['error'] = "WebSocket connection timeout"
        except websockets.exceptions.InvalidStatusCode as e:
            result['error'] = f"Invalid status code: {e.status_code}"
            if e.status_code == 403:
                result['geo_blocked'] = True
        except Exception as e:
            result['error'] = f"WebSocket error: {str(e)}"

        return result

    async def test_exchange(self, exchange_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test all connectivity for a single exchange.

        Args:
            exchange_name: Name of the exchange
            config: Exchange configuration from settings

        Returns:
            Comprehensive test results for the exchange
        """
        print(f"Testing {exchange_name}...")

        exchange_results = {
            'exchange': exchange_name,
            'display_name': config.get('display_name', exchange_name),
            'base_url': config.get('base_url'),
            'websocket_url': config.get('websocket_url'),
            'tests': [],
            'overall_status': 'unknown',
            'recommendations': [],
            'accessibility': 'unknown'
        }

        # Test REST API endpoints
        if config.get('base_url'):
            # Test basic connectivity endpoints first
            test_endpoints = []

            # Add time endpoint if documented
            if 'endpoints' in config and 'time' in config['endpoints']:
                test_endpoints.append(config['endpoints']['time'])
            else:
                # Try common time endpoints
                common_time_endpoints = [
                    '/api/v3/time',  # Binance, OKX, MEXC
                    '/api/v1/timestamp',  # KuCoin
                    '/v1/common/timestamp',  # Huobi
                    '/api/v4/spot/time',  # Gate.io
                    '/v5/market/time',  # Bybit V5
                    '/time',  # Coinbase
                    '/0/public/Time',  # Kraken
                    '/v2/platform/status',  # Bitfinex
                ]

                # Use the first endpoint that seems appropriate
                test_endpoints.extend(common_time_endpoints)

            # Test each endpoint
            for endpoint in test_endpoints[:3]:  # Limit to 3 endpoints
                full_url = config['base_url'] + endpoint
                http_result = await self.test_http_endpoint(exchange_name, full_url)
                exchange_results['tests'].append(http_result)

                # If any test succeeds, mark exchange as accessible
                if http_result.get('success'):
                    exchange_results['overall_status'] = 'accessible'
                    exchange_results['accessibility'] = 'full'
                    break
                elif http_result.get('geo_blocked'):
                    exchange_results['overall_status'] = 'restricted'
                    exchange_results['accessibility'] = 'geo_blocked'
                    break

        # Test WebSocket if configured and requested
        if config.get('websocket_url'):
            ws_result = await self.test_websocket_endpoint(
                exchange_name,
                config['websocket_url']
            )
            exchange_results['tests'].append(ws_result)

            # Update accessibility based on WebSocket results
            if ws_result.get('success'):
                if exchange_results['accessibility'] == 'unknown':
                    exchange_results['accessibility'] = 'websocket_only'
                elif exchange_results['accessibility'] == 'full':
                    exchange_results['accessibility'] = 'full'
            elif ws_result.get('geo_blocked'):
                exchange_results['accessibility'] = 'restricted'

        # Generate recommendations
        self._generate_recommendations(exchange_results)

        # Store results
        self.results[exchange_name] = exchange_results
        return exchange_results

    def _generate_recommendations(self, exchange_results: Dict[str, Any]):
        """
        Generate recommendations based on test results.

        Args:
            exchange_results: Test results for an exchange
        """
        recommendations = []

        if exchange_results['accessibility'] == 'full':
            recommendations.append("✅ Exchange fully accessible from this location")

        elif exchange_results['accessibility'] == 'websocket_only':
            recommendations.append("⚠️  Only WebSocket accessible, REST API may be restricted")
            recommendations.append("Consider using WebSocket for real-time data")

        elif exchange_results['accessibility'] == 'geo_blocked':
            recommendations.append("❌ Geographic restrictions detected")
            recommendations.append("Try using VPN or proxy service")
            recommendations.append("Check if exchange offers US-specific service (e.g., Binance.US)")

        elif exchange_results['accessibility'] == 'restricted':
            recommendations.append("⚠️  Partial restrictions detected")
            recommendations.append("Some endpoints may be blocked")
            recommendations.append("Check exchange documentation for regional access rules")

        elif exchange_results['overall_status'] == 'unknown':
            recommendations.append("❓ Connectivity status unknown")
            recommendations.append("Check network connectivity and firewall settings")
            recommendations.append("Verify exchange is operational")

        # Check for CloudFront blocking
        for test in exchange_results['tests']:
            if test.get('cloudfront_block'):
                recommendations.append("🌐 CloudFront distribution blocking detected")
                recommendations.append("This exchange actively blocks certain regions")
                recommendations.append("VPN required for access")
                break

        # Check response times
        response_times = []
        for test in exchange_results['tests']:
            if test.get('response_time_ms'):
                response_times.append(test['response_time_ms'])

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time > 1000:
                recommendations.append(f"🐌 Slow response time: {avg_time:.0f}ms average")
                recommendations.append("Consider using closer server locations")
            elif avg_time < 100:
                recommendations.append(f"⚡ Excellent response time: {avg_time:.0f}ms average")

        exchange_results['recommendations'] = recommendations

    async def run_tests(self, exchange_names: List[str], test_websocket: bool = False) -> Dict[str, Any]:
        """
        Run connectivity tests for specified exchanges.

        Args:
            exchange_names: List of exchange names to test
            test_websocket: Whether to test WebSocket connections

        Returns:
            Dictionary with all test results
        """
        print(f"\n{'='*80}")
        print(f"EXCHANGE CONNECTIVITY TEST - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*80}\n")

        # Filter exchanges to test
        exchanges_to_test = {}
        for name in exchange_names:
            if name in VENDORS:
                exchanges_to_test[name] = VENDORS[name]
            else:
                print(f"⚠️  Exchange '{name}' not configured, skipping")

        if not exchanges_to_test:
            print("❌ No exchanges to test")
            return {}

        print(f"Testing {len(exchanges_to_test)} exchanges...\n")

        # Run tests concurrently
        tasks = []
        for exchange_name, config in exchanges_to_test.items():
            # Only test WebSocket if explicitly requested
            if not test_websocket:
                config = config.copy()
                config.pop('websocket_url', None)

            task = self.test_exchange(exchange_name, config)
            tasks.append(task)

        await asyncio.gather(*tasks)

        return self.results

    def print_summary(self):
        """Print formatted test summary."""
        if not self.results:
            print("No test results available")
            return

        print(f"\n{'='*80}")
        print("CONNECTIVITY TEST SUMMARY")
        print(f"{'='*80}\n")

        # Summary table
        print(f"{'Exchange':<15} {'Status':<15} {'Accessibility':<20} {'Recommendation'}")
        print(f"{'-'*15} {'-'*15} {'-'*20} {'-'*30}")

        accessible_count = 0
        restricted_count = 0
        unknown_count = 0

        for exchange_name, results in sorted(self.results.items()):
            status = results['overall_status']
            accessibility = results['accessibility']

            # Count statistics
            if accessibility in ['full', 'websocket_only']:
                accessible_count += 1
                status_symbol = "✅"
            elif accessibility in ['geo_blocked', 'restricted']:
                restricted_count += 1
                status_symbol = "❌"
            else:
                unknown_count += 1
                status_symbol = "❓"

            # Get first recommendation for summary
            recommendation = results['recommendations'][0] if results['recommendations'] else "No data"
            if len(recommendation) > 30:
                recommendation = recommendation[:27] + "..."

            print(f"{exchange_name:<15} {status_symbol + ' ' + status:<15} {accessibility:<20} {recommendation}")

        print(f"\n{'='*80}")
        print("STATISTICS")
        print(f"{'='*80}")
        print(f"Total exchanges tested: {len(self.results)}")
        print(f"✅ Fully accessible: {accessible_count}")
        print(f"❌ Restricted/blocked: {restricted_count}")
        print(f"❓ Unknown/unreachable: {unknown_count}")

        # Identify exchanges with geographic restrictions
        geo_blocked = []
        cloudfront_blocked = []

        for exchange_name, results in self.results.items():
            for test in results['tests']:
                if test.get('geo_blocked'):
                    geo_blocked.append(exchange_name)
                    break
                if test.get('cloudfront_block'):
                    cloudfront_blocked.append(exchange_name)
                    break

        if geo_blocked:
            print(f"\n{'='*80}")
            print("GEOGRAPHIC RESTRICTIONS DETECTED")
            print(f"{'='*80}")
            for exchange in geo_blocked:
                print(f"❌ {exchange}: Geographic restrictions active")
                if exchange in cloudfront_blocked:
                    print(f"   🔒 CloudFront distribution blocking detected")

        # Detailed results for each exchange
        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")

        for exchange_name, results in sorted(self.results.items()):
            print(f"\n{exchange_name.upper()} ({results['display_name']})")
            print(f"Overall Status: {results['overall_status']}")
            print(f"Accessibility: {results['accessibility']}")

            if results['tests']:
                print(f"\nTest Results:")
                for test in results['tests']:
                    if test.get('success'):
                        print(f"  ✅ {test['url']} - {test['status_code']} ({test['response_time_ms']}ms)")
                    else:
                        print(f"  ❌ {test['url']} - Error: {test.get('error', 'Unknown')}")

            if results['recommendations']:
                print(f"\nRecommendations:")
                for rec in results['recommendations']:
                    print(f"  {rec}")

    def generate_report(self, output_file: str = "connectivity_report.html"):
        """
        Generate HTML report of connectivity test results.

        Args:
            output_file: Output HTML file path
        """
        from string import Template

        # HTML template
        html_template = Template('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Exchange Connectivity Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                h2 { color: #666; margin-top: 30px; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                .exchange { margin: 20px 0; padding: 15px; border-left: 4px solid #ddd; }
                .accessible { border-left-color: #4CAF50; }
                .restricted { border-left-color: #f44336; }
                .unknown { border-left-color: #ff9800; }
                .test-result { margin: 5px 0; padding: 5px; }
                .success { color: #4CAF50; }
                .error { color: #f44336; }
                .recommendation { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 3px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .stat { font-size: 1.2em; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>Exchange Connectivity Test Report</h1>
            <p>Generated: $generated_time</p>

            <div class="summary">
                <h2>Summary</h2>
                <div class="stat">Total exchanges tested: $total_count</div>
                <div class="stat" style="color: #4CAF50;">✅ Accessible: $accessible_count</div>
                <div class="stat" style="color: #f44336;">❌ Restricted: $restricted_count</div>
                <div class="stat" style="color: #ff9800;">❓ Unknown: $unknown_count</div>
            </div>

            <h2>Exchange Details</h2>
            $exchange_details
        </body>
        </html>
        ''')

        # Count statistics
        accessible_count = 0
        restricted_count = 0
        unknown_count = 0

        for results in self.results.values():
            if results['accessibility'] in ['full', 'websocket_only']:
                accessible_count += 1
            elif results['accessibility'] in ['geo_blocked', 'restricted']:
                restricted_count += 1
            else:
                unknown_count += 1

        # Generate exchange details HTML
        exchange_details_html = ""
        for exchange_name, results in sorted(self.results.items()):
            # Determine CSS class based on accessibility
            if results['accessibility'] in ['full', 'websocket_only']:
                css_class = "accessible"
            elif results['accessibility'] in ['geo_blocked', 'restricted']:
                css_class = "restricted"
            else:
                css_class = "unknown"

            # Test results HTML
            test_results_html = ""
            for test in results['tests']:
                if test.get('success'):
                    test_results_html += f'''
                    <div class="test-result success">
                        ✅ {test['url']} - HTTP {test.get('status_code', 'N/A')}
                        ({test.get('response_time_ms', 'N/A')}ms)
                    </div>
                    '''
                else:
                    test_results_html += f'''
                    <div class="test-result error">
                        ❌ {test['url']} - Error: {test.get('error', 'Unknown')}
                    </div>
                    '''

            # Recommendations HTML
            recommendations_html = ""
            for rec in results['recommendations']:
                recommendations_html += f'<div>{rec}</div>'

            exchange_details_html += f'''
            <div class="exchange {css_class}">
                <h3>{exchange_name} ({results['display_name']})</h3>
                <p><strong>Status:</strong> {results['overall_status']}</p>
                <p><strong>Accessibility:</strong> {results['accessibility']}</p>

                <h4>Test Results:</h4>
                {test_results_html}

                <h4>Recommendations:</h4>
                <div class="recommendation">
                    {recommendations_html}
                </div>
            </div>
            '''

        # Fill template
        html_content = html_template.substitute(
            generated_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            total_count=len(self.results),
            accessible_count=accessible_count,
            restricted_count=restricted_count,
            unknown_count=unknown_count,
            exchange_details=exchange_details_html
        )

        # Write to file
        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"\n✅ HTML report generated: {output_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test connectivity to cryptocurrency exchange APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all exchanges
  python test_exchange_connectivity.py

  # Test specific exchanges
  python test_exchange_connectivity.py coinbase binance kraken

  # Test with verbose output and WebSocket tests
  python test_exchange_connectivity.py --verbose --ws-test

  # Generate HTML report
  python test_exchange_connectivity.py --report

  # Test exchanges excluding those known to be blocked
  python test_exchange_connectivity.py --exclude bybit

  # List available exchanges
  python test_exchange_connectivity.py --list
        """
    )

    parser.add_argument(
        'exchanges',
        nargs='*',
        default=['all'],
        help='Exchange names to test (default: all)'
    )

    parser.add_argument(
        '--exclude',
        nargs='+',
        default=[],
        help='Exclude specific exchanges from testing'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available exchanges and exit'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed test results'
    )

    parser.add_argument(
        '--ws-test',
        action='store_true',
        help='Include WebSocket connectivity tests'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate HTML report (connectivity_report.html)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='connectivity_report.html',
        help='Output file for HTML report (default: connectivity_report.html)'
    )

    args = parser.parse_args()

    # List available exchanges if requested
    if args.list:
        print(f"\nAvailable exchanges ({len(VENDORS)}):")
        for name, config in VENDORS.items():
            status = "enabled" if config.get('enabled', False) else "disabled"
            print(f"  • {name:15} - {config.get('display_name', 'N/A'):25} [{status}]")
        return

    # Determine which exchanges to test
    if 'all' in args.exchanges or not args.exchanges:
        exchanges_to_test = list(VENDORS.keys())
    else:
        exchanges_to_test = args.exchanges

    # Filter out excluded exchanges
    exchanges_to_test = [e for e in exchanges_to_test if e not in args.exclude]

    # Filter for enabled exchanges only
    exchanges_to_test = [e for e in exchanges_to_test
                        if e in VENDORS and VENDORS[e].get('enabled', False)]

    if not exchanges_to_test:
        print("❌ No exchanges to test")
        return

    # Run connectivity tests
    async with ExchangeConnectivityTester(timeout=args.timeout) as tester:
        results = await tester.run_tests(
            exchanges_to_test,
            test_websocket=args.ws_test
        )

        # Print summary
        tester.print_summary()

        # Generate HTML report if requested
        if args.report:
            tester.generate_report(args.output)

        # Print verbose details if requested
        if args.verbose:
            print(f"\n{'='*80}")
            print("VERBOSE DETAILS")
            print(f"{'='*80}")
            for exchange_name, exchange_results in results.items():
                print(f"\n{exchange_name.upper()}:")
                print(json.dumps(exchange_results, indent=2, default=str))


if __name__ == '__main__':
    # Run async main
    asyncio.run(main())
