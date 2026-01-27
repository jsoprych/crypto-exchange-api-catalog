# Vendor API Specification Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: PEP8](https://img.shields.io/badge/code%20style-PEP8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Maintained: Yes](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/jsoprych/coinbase_catalog_to_json)

A robust, extensible system for discovering and cataloging cryptocurrency exchange APIs. Generates machine-readable JSON specifications for use in data ingestion applications.

## Purpose

This tool produces a comprehensive JSON catalog/specification from vendor APIs (starting with Coinbase), enabling applications to:
- **Configure data subscriptions** (tick feeds, bar feeds, order books, etc.)
- **Understand available endpoints** and their parameters
- **Map vendor-specific fields** to internal abstractions
- **Track API changes** over time through audit trails

The JSON specification is designed for **code generation** and will be used by future data stream ingestion applications.

## Features

### Multi-Vendor Support
- **Extensible adapter pattern** - Easy to add new exchanges
- **Coinbase Exchange** - Fully implemented (Phase 1: public endpoints)
- **Future vendors** - Binance, Kraken, etc. ready to implement

### SQLite-Backed Storage
- **Queryable database** - Powerful SQL analysis of API specifications
- **Complete audit trail** - Track every discovery run
- **Change detection** - Automatically identify API changes
- **Versioning** - Historical tracking of API evolution

### Flexible JSON Export
- **Python/Go compatibility** - Configurable naming conventions (`snake_case` or `camelCase`)
- **Multiple output formats** - Per-vendor or unified multi-vendor specs
- **Schema validation** - Ensures consistent output structure

### Comprehensive Discovery
- **REST endpoints** - All HTTP methods, parameters, response schemas
- **WebSocket channels** - Subscribe/unsubscribe formats, message types
- **Products/symbols** - Trading pairs with metadata
- **Feed relationships** - Links products to available data feeds

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/jsoprych/coinbase_catalog_to_json.git
cd coinbase_catalog_to_json

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python3 main.py init
```

## Quick Start

```bash
# 1. Discover Coinbase API
python main.py discover --vendor coinbase

# 2. Export to JSON (Python format with snake_case)
python main.py export --vendor coinbase --format snake_case

# 3. Export to JSON (Go format with camelCase)
python main.py export --vendor coinbase --format camelCase --output output/coinbase_go.json

# 4. List all vendors
python main.py list-vendors

# 5. Query the database
python main.py query "SELECT * FROM products WHERE base_currency = 'BTC'"
```

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────┐
│   Vendor Adapters (Extensible)         │
│   - CoinbaseAdapter                     │
│   - FutureVendorAdapter                 │
└──────────────┬──────────────────────────┘
               │ (vendor-specific data)
               ▼
┌─────────────────────────────────────────┐
│   SQLite Database (Source of Truth)     │
│   - Vendors, Endpoints, Channels        │
│   - Products, Audit Trail               │
└──────────────┬──────────────────────────┘
               │ (query & export)
               ▼
┌─────────────────────────────────────────┐
│   JSON Export (Code Generation Input)   │
│   - Python/Go format options            │
│   - Per-vendor or unified specs         │
└─────────────────────────────────────────┘
```

### Discovery Process

1. **REST Endpoint Discovery** - Identify all available HTTP endpoints
2. **WebSocket Channel Discovery** - Map all subscription channels
3. **Product Discovery** - Fetch trading pairs from live API
4. **Feed Linking** - Connect products to their available feeds

## Project Structure

```
coinbase_catalog_to_json/
├── config/
│   └── settings.py              # Configuration management
├── src/
│   ├── adapters/
│   │   ├── base_adapter.py      # Abstract vendor interface
│   │   └── coinbase_adapter.py  # Coinbase implementation
│   ├── database/
│   │   ├── db_manager.py        # Database connection
│   │   └── repository.py        # Data access layer
│   ├── discovery/
│   │   └── spec_generator.py    # Discovery orchestration
│   ├── export/
│   │   └── json_exporter.py     # JSON export functionality
│   └── utils/
│       ├── logger.py            # Logging utilities
│       ├── http_client.py       # HTTP client with retry
│       └── naming.py            # snake_case ↔ camelCase
├── sql/
│   ├── schema.sql               # Database schema (DDL)
│   ├── queries/                 # Pre-built SQL queries
│   │   ├── 01_vendor_analysis.sql
│   │   ├── 02_endpoint_discovery.sql
│   │   └── 04_product_catalog.sql
│   └── views/
│       └── common_views.sql     # Useful database views
├── data/
│   └── specifications.db        # SQLite database
├── output/                      # JSON exports
├── main.py                      # CLI entry point
├── requirements.txt
└── README.md
```

## Usage

### Command Reference

#### Initialize Database
```bash
python main.py init
```

Creates the database schema with all tables, indexes, and views.

#### Discover Vendor API
```bash
python main.py discover --vendor coinbase
```

Runs the complete discovery process:
- Fetches products from live API
- Maps REST endpoints
- Maps WebSocket channels
- Links products to feeds
- Stores everything in SQLite

**Output:**
```
Discovering Coinbase Exchange API...

✓ Discovery complete:
  - Products: 247
  - REST endpoints: 10
  - WebSocket channels: 5
  - Duration: 2.34s
  - Run ID: 1
```

#### Export Specification
```bash
# Python format (snake_case)
python main.py export --vendor coinbase --format snake_case

# Go format (camelCase)
python main.py export --vendor coinbase --format camelCase

# Custom output path
python main.py export --vendor coinbase --output my_spec.json
```

**Output JSON Structure:**
```json
{
  "spec_metadata": {
    "vendor": "coinbase",
    "display_name": "Coinbase Exchange",
    "spec_version": "1.0",
    "generated_at": "2026-01-26T18:00:00Z",
    "naming_convention": "snake_case",
    "base_url": "https://api.exchange.coinbase.com",
    "websocket_url": "wss://ws-feed.exchange.coinbase.com"
  },
  "rest_api": {
    "base_url": "https://api.exchange.coinbase.com",
    "endpoints": [
      {
        "path": "/products",
        "method": "GET",
        "authentication_required": false,
        "description": "Get a list of available currency pairs for trading",
        "query_parameters": {},
        "response_schema": {"type": "array"},
        "rate_limit_tier": "public"
      }
      // ... more endpoints
    ]
  },
  "websocket_api": {
    "url": "wss://ws-feed.exchange.coinbase.com",
    "channels": [
      {
        "channel_name": "ticker",
        "authentication_required": false,
        "description": "Real-time price updates for a product",
        "subscribe_format": {
          "type": "subscribe",
          "product_ids": ["BTC-USD"],
          "channels": ["ticker"]
        },
        "message_types": ["ticker", "subscriptions"]
      }
      // ... more channels
    ]
  },
  "products": [
    {
      "symbol": "BTC-USD",
      "base_currency": "BTC",
      "quote_currency": "USD",
      "status": "online",
      "available_rest_feeds": [
        {
          "type": "ticker",
          "endpoint": "/products/{product_id}/ticker",
          "method": "GET"
        },
        {
          "type": "candles",
          "endpoint": "/products/{product_id}/candles",
          "method": "GET",
          "intervals": [60, 300, 900, 3600, 21600, 86400]
        }
      ],
      "available_ws_channels": ["ticker", "level2", "matches", "heartbeat"]
    }
    // ... more products
  ]
}
```

#### Query Database
```bash
# List all products
python main.py query "SELECT symbol, base_currency, quote_currency FROM products"

# Find BTC pairs
python main.py query "SELECT * FROM products WHERE base_currency = 'BTC'"

# Show discovery run history
python main.py query "SELECT * FROM discovery_runs ORDER BY run_timestamp DESC"
```

### SQL Query Library

The `sql/queries/` directory contains pre-built queries for common analysis tasks:

#### Vendor Analysis
```bash
sqlite3 data/specifications.db < sql/queries/01_vendor_analysis.sql
```

- List all vendors with API coverage
- Most recently updated vendors
- Vendor health check

#### Endpoint Discovery
```bash
sqlite3 data/specifications.db < sql/queries/02_endpoint_discovery.sql
```

- All REST endpoints for a vendor
- Public vs authenticated endpoints
- Recently added/deprecated endpoints

#### Product Catalog
```bash
sqlite3 data/specifications.db < sql/queries/04_product_catalog.sql
```

- All active products
- Products available on multiple vendors
- Products with specific feeds (candles, ticker, etc.)

### Using Views

The database includes pre-built views for easier querying:

```sql
-- Active API surface across all vendors
SELECT * FROM v_active_api_surface;

-- Product feed availability
SELECT * FROM v_product_feed_availability WHERE symbol = 'BTC-USD';

-- Latest discovery runs
SELECT * FROM v_latest_discovery_runs;

-- Recent API changes
SELECT * FROM v_recent_api_changes;
```

## Configuration

Edit `config/settings.py` to customize:

### Output Format
```python
OUTPUT_CONFIG = {
    "naming_convention": "snake_case",  # or "camelCase"
    "include_vendor_metadata": True,
    "schema_version": "1.0",
    "pretty_print": True,
    "indent": 2
}
```

### Vendor Configuration
```python
VENDORS = {
    "coinbase": {
        "enabled": True,
        "base_url": "https://api.exchange.coinbase.com",
        "websocket_url": "wss://ws-feed.exchange.coinbase.com",
        # ... more config
    }
}
```

## Adding a New Vendor

1. **Create adapter** in `src/adapters/new_vendor_adapter.py`:

```python
from src.adapters.base_adapter import BaseVendorAdapter

class NewVendorAdapter(BaseVendorAdapter):
    def discover_rest_endpoints(self):
        # Implement endpoint discovery
        pass
    
    def discover_websocket_channels(self):
        # Implement channel discovery
        pass
    
    def discover_products(self):
        # Implement product discovery
        pass
```

2. **Add configuration** to `config/settings.py`:

```python
VENDORS["new_vendor"] = {
    "enabled": True,
    "display_name": "New Vendor Exchange",
    "base_url": "https://api.newvendor.com",
    # ... more config
}
```

3. **Update spec_generator.py** to recognize the new adapter:

```python
def _create_adapter(self, vendor_name, vendor_config):
    if vendor_name == 'coinbase':
        return CoinbaseAdapter(vendor_config)
    elif vendor_name == 'new_vendor':
        return NewVendorAdapter(vendor_config)
```

4. **Run discovery**:

```bash
python main.py discover --vendor new_vendor
python main.py export --vendor new_vendor
```

## Design Principles

### Modular Design
- Functions <50 lines (enforced through design)
- Clear separation of concerns
- Reusable components

### Documentation
- Every function has a docstring
- First line of each file: comment with filename
- Meaningful inline comments

### Error Handling
- Fail-fast on critical errors
- Graceful degradation for optional data
- Comprehensive logging

### Extensibility
- New vendors: Inherit from `BaseVendorAdapter`
- New feed types: Configuration-driven
- New intervals: No hardcoding
- Custom transformations: Plugin system ready

## Future Enhancements

### Phase 2: Authenticated Endpoints
- Add support for private endpoints (account, orders, fills)
- Implement authentication configuration
- Add private WebSocket channels

### Additional Vendors
- Binance
- Kraken
- Bitfinex
- And more...

### WebSocket Testing
- Live WebSocket connection testing
- Message format validation
- Real-time data capture

### Documentation Parsing
- Scrape official API documentation
- Parse OpenAPI/Swagger specs
- Cross-validate docs vs live API

## Database Schema

The SQLite database contains 11 tables:

- **vendors** - Vendor registry
- **discovery_runs** - Audit trail of discovery runs
- **rest_endpoints** - REST API endpoints
- **websocket_channels** - WebSocket channels
- **products** - Trading pairs/symbols
- **product_rest_feeds** - Product → REST feed links
- **product_ws_channels** - Product → WebSocket channel links
- **api_changes** - Change tracking
- **spec_versions** - Specification version history

See `sql/schema.sql` for complete DDL.

## Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `api_spec_generator.log` (DEBUG level)

Log format:
```
2026-01-26 18:00:00 [INFO] src.discovery.spec_generator: Starting API specification generation for coinbase
```

## License

[Specify your license]

## Contributing

[Specify contribution guidelines]

## Support

For issues or questions, please [file an issue](https://github.com/yourusername/yourrepo/issues).
