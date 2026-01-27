# Quick Start Guide

Get up and running with the Vendor API Specification Generator in 5 minutes.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 main.py init
```

## Basic Usage

### 1. Discover Coinbase API

```bash
python3 main.py discover --vendor coinbase
```

**Expected output:**
```
Discovering Coinbase Exchange API...

✓ Discovery complete:
  - Products: 776
  - REST endpoints: 10
  - WebSocket channels: 5
  - Duration: 19.93s
  - Run ID: 1
```

### 2. Export to JSON (Python format)

```bash
python3 main.py export --vendor coinbase --format snake_case
```

**Output file:** `output/coinbase/coinbase_api_spec.json`

### 3. Export to JSON (Go format)

```bash
python3 main.py export --vendor coinbase --format camelCase --output coinbase_go.json
```

**Output file:** `coinbase_go.json`

## Query Examples

### Find all BTC trading pairs

```bash
python3 main.py query "SELECT symbol, base_currency, quote_currency FROM products WHERE base_currency = 'BTC'"
```

### Check discovery run history

```bash
python3 main.py query "SELECT * FROM discovery_runs"
```

### Find products with ticker feeds

```bash
python3 main.py query "
SELECT p.symbol, prf.feed_type 
FROM products p 
JOIN product_rest_feeds prf ON p.product_id = prf.product_id 
WHERE prf.feed_type = 'ticker' 
LIMIT 10
"
```

### Using pre-built SQL queries

```bash
# Vendor analysis
sqlite3 data/specifications.db < sql/queries/01_vendor_analysis.sql

# Endpoint discovery
sqlite3 data/specifications.db < sql/queries/02_endpoint_discovery.sql

# Product catalog
sqlite3 data/specifications.db < sql/queries/04_product_catalog.sql
```

## Understanding the Output

### JSON Structure

```json
{
  "spec_metadata": {
    "vendor": "coinbase",
    "base_url": "https://api.exchange.coinbase.com",
    "websocket_url": "wss://ws-feed.exchange.coinbase.com"
  },
  "rest_api": {
    "endpoints": [...]
  },
  "websocket_api": {
    "channels": [...]
  },
  "products": [
    {
      "symbol": "BTC-USD",
      "base_currency": "BTC",
      "quote_currency": "USD",
      "available_rest_feeds": [
        {
          "type": "ticker",
          "endpoint": "/products/{product_id}/ticker"
        },
        {
          "type": "candles",
          "endpoint": "/products/{product_id}/candles",
          "intervals": [60, 300, 900, 3600, 21600, 86400]
        }
      ],
      "available_ws_channels": ["ticker", "level2", "matches"]
    }
  ]
}
```

### Database Tables

- **vendors** - Exchange registry
- **discovery_runs** - Audit trail
- **rest_endpoints** - REST API endpoints
- **websocket_channels** - WebSocket channels
- **products** - Trading pairs
- **product_rest_feeds** - Product → REST feed mappings
- **product_ws_channels** - Product → WebSocket channel mappings

## Common Tasks

### Re-run discovery to detect changes

```bash
# Run discovery again
python3 main.py discover --vendor coinbase

# Check for changes
python3 main.py query "
SELECT change_type, detected_at 
FROM api_changes 
ORDER BY detected_at DESC 
LIMIT 10
"
```

### Export specific products

Since all products are in the database, you can query and export a subset:

```bash
# Query specific products
python3 main.py query "
SELECT symbol, base_currency, quote_currency 
FROM products 
WHERE base_currency IN ('BTC', 'ETH') 
AND quote_currency = 'USD'
"
```

### Check system health

```bash
# View latest discovery runs
python3 main.py query "SELECT * FROM v_latest_discovery_runs"

# Check product feed availability
python3 main.py query "SELECT * FROM v_product_feed_availability WHERE symbol = 'BTC-USD'"
```

## Next Steps

1. **Explore SQL queries** - Check `sql/queries/` for pre-built analysis queries
2. **Add new vendors** - See README.md for instructions on adding Binance, Kraken, etc.
3. **Integrate with your app** - Use the JSON specification for code generation
4. **Schedule updates** - Set up cron jobs to regularly update specifications

## Troubleshooting

### Database locked error
```bash
# Close any open SQLite connections
# Or remove the database and reinitialize
rm data/specifications.db
python3 main.py init
```

### No products discovered
```bash
# Check internet connection
# Verify Coinbase API is accessible
curl https://api.exchange.coinbase.com/products
```

### Import errors
```bash
# Ensure you're in the project directory
cd coinbase_catalog_to_json

# Install dependencies
pip install -r requirements.txt
```

## Support

For more detailed documentation, see [README.md](README.md).

For issues, check the log file: `api_spec_generator.log`
