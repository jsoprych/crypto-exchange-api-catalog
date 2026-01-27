# SQL Query Library

This directory contains pre-built SQL queries for analyzing vendor API specifications.

## Directory Structure

```
sql/
├── schema.sql                    # Database schema (CREATE TABLE statements)
├── views/
│   └── common_views.sql         # Pre-built views for common operations
├── queries/
│   ├── 01_vendor_analysis.sql   # Vendor comparison and health checks
│   ├── 02_endpoint_discovery.sql # REST endpoint analysis
│   └── 04_product_catalog.sql   # Product/symbol queries
└── README.md                     # This file
```

## Usage

### Method 1: Using SQLite CLI

```bash
# Run a query file
sqlite3 data/specifications.db < sql/queries/01_vendor_analysis.sql

# Interactive mode
sqlite3 data/specifications.db
sqlite> .read sql/queries/01_vendor_analysis.sql
```

### Method 2: Using Python CLI

```bash
# Execute any SQL query
python3 main.py query "SELECT * FROM vendors"

# Multi-line queries
python3 main.py query "
SELECT v.vendor_name, COUNT(p.product_id) as products
FROM vendors v
JOIN products p ON v.vendor_id = p.vendor_id
GROUP BY v.vendor_id
"
```

### Method 3: Using Database Views

```bash
# Views are pre-created when you run 'init'
python3 main.py query "SELECT * FROM v_active_api_surface"
python3 main.py query "SELECT * FROM v_latest_discovery_runs"
```

## Query Files

### 01_vendor_analysis.sql

**Vendor comparison and health checks**

Contains queries for:
- List all vendors with API coverage
- Most recently updated vendors
- Vendor health check (stale discovery runs)

**Example:**
```sql
-- List all vendors with their current API coverage
SELECT 
    v.vendor_name,
    v.display_name,
    COUNT(DISTINCT e.endpoint_id) as total_rest_endpoints,
    COUNT(DISTINCT w.channel_id) as total_ws_channels,
    COUNT(DISTINCT p.product_id) as total_products
FROM vendors v
LEFT JOIN rest_endpoints e ON v.vendor_id = e.vendor_id
LEFT JOIN websocket_channels w ON v.vendor_id = w.vendor_id
LEFT JOIN products p ON v.vendor_id = p.vendor_id
GROUP BY v.vendor_id;
```

### 02_endpoint_discovery.sql

**REST endpoint discovery and analysis**

Contains queries for:
- All REST endpoints for a specific vendor
- Public vs authenticated endpoints
- Endpoints by HTTP method distribution
- Recently added/deprecated endpoints

**Example:**
```sql
-- Find all public (unauthenticated) endpoints
SELECT 
    v.vendor_name,
    e.method,
    e.path,
    e.description
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.authentication_required = 0
  AND e.status = 'active';
```

### 04_product_catalog.sql

**Product/symbol catalog queries**

Contains queries for:
- All active products for a vendor
- Products available on multiple vendors
- Products by base currency (BTC, ETH, etc.)
- Products with specific feeds (candles, ticker, etc.)
- Recently added products

**Example:**
```sql
-- Find all BTC pairs
SELECT 
    v.vendor_name,
    p.symbol,
    p.quote_currency,
    p.status
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.base_currency = 'BTC'
  AND p.status = 'online';
```

## Pre-Built Views

### v_active_api_surface

Shows all active REST endpoints and WebSocket channels across all vendors.

```sql
SELECT * FROM v_active_api_surface;
```

**Columns:**
- vendor_id, vendor_name
- endpoint_id / channel_id
- api_type (rest / websocket)
- api_identifier (method + path / channel name)
- authentication_required
- status

### v_product_feed_availability

Shows which feeds (REST + WebSocket) are available for each product.

```sql
SELECT * FROM v_product_feed_availability WHERE symbol = 'BTC-USD';
```

**Columns:**
- vendor_name
- symbol, base_currency, quote_currency
- product_status
- rest_feed_count, ws_channel_count
- rest_feeds (comma-separated)
- ws_channels (comma-separated)

### v_latest_discovery_runs

Shows the most recent discovery run for each vendor.

```sql
SELECT * FROM v_latest_discovery_runs;
```

**Columns:**
- run_id, vendor_id, vendor_name
- run_timestamp, duration_seconds
- discovery_method
- endpoints_discovered, websocket_channels_discovered, products_discovered
- success, error_message

### v_recent_api_changes

Shows API changes detected in the last 30 days.

```sql
SELECT * FROM v_recent_api_changes;
```

**Columns:**
- vendor_name
- change_type (endpoint_added, product_removed, etc.)
- entity_type (endpoint, channel, product)
- detected_at
- old_value, new_value (JSON)

## Common Query Patterns

### Find products with specific feeds

```sql
-- Products with candle feeds
SELECT 
    v.vendor_name,
    p.symbol,
    prf.intervals
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
JOIN product_rest_feeds prf ON p.product_id = prf.product_id
WHERE prf.feed_type = 'candles'
  AND p.status = 'online';
```

### Compare vendors

```sql
-- API coverage comparison
SELECT 
    v.vendor_name,
    COUNT(DISTINCT e.endpoint_id) as rest_endpoints,
    COUNT(DISTINCT w.channel_id) as ws_channels,
    COUNT(DISTINCT p.product_id) as products
FROM vendors v
LEFT JOIN rest_endpoints e ON v.vendor_id = e.vendor_id
LEFT JOIN websocket_channels w ON v.vendor_id = w.vendor_id
LEFT JOIN products p ON v.vendor_id = p.vendor_id
GROUP BY v.vendor_id;
```

### Track API changes

```sql
-- Recent changes for a vendor
SELECT 
    change_type,
    entity_type,
    detected_at,
    old_value,
    new_value
FROM api_changes ac
JOIN vendors v ON ac.vendor_id = v.vendor_id
WHERE v.vendor_name = 'coinbase'
ORDER BY detected_at DESC
LIMIT 10;
```

### Discovery run analytics

```sql
-- Discovery performance over time
SELECT 
    v.vendor_name,
    DATE(dr.run_timestamp) as run_date,
    AVG(dr.duration_seconds) as avg_duration,
    AVG(dr.products_discovered) as avg_products
FROM discovery_runs dr
JOIN vendors v ON dr.vendor_id = v.vendor_id
WHERE dr.success = 1
GROUP BY v.vendor_id, run_date
ORDER BY run_date DESC;
```

## Database Schema Reference

### Core Tables

- **vendors** - Exchange/vendor registry
- **discovery_runs** - Audit trail of all discovery runs
- **rest_endpoints** - REST API endpoints with parameters
- **websocket_channels** - WebSocket channels with message formats
- **products** - Trading pairs/symbols
- **product_rest_feeds** - Links products to REST endpoints
- **product_ws_channels** - Links products to WebSocket channels
- **api_changes** - Change tracking over time
- **spec_versions** - Versioned specification history

### Key Relationships

```
vendors (1) ─→ (N) rest_endpoints
vendors (1) ─→ (N) websocket_channels
vendors (1) ─→ (N) products
vendors (1) ─→ (N) discovery_runs

products (N) ←─→ (N) rest_endpoints (via product_rest_feeds)
products (N) ←─→ (N) websocket_channels (via product_ws_channels)
```

## Tips

### Pretty output in SQLite CLI

```sql
-- Enable column mode
.mode column
.headers on

-- Run your query
SELECT * FROM vendors;
```

### Export query results to CSV

```bash
sqlite3 data/specifications.db <<EOF
.mode csv
.output results.csv
SELECT * FROM products WHERE base_currency = 'BTC';
.quit
EOF
```

### JSON output from SQLite

```bash
sqlite3 data/specifications.db <<EOF
.mode json
SELECT * FROM products LIMIT 5;
EOF
```

### Count records in all tables

```sql
SELECT 'vendors' as table_name, COUNT(*) as count FROM vendors
UNION ALL
SELECT 'rest_endpoints', COUNT(*) FROM rest_endpoints
UNION ALL
SELECT 'websocket_channels', COUNT(*) FROM websocket_channels
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'discovery_runs', COUNT(*) FROM discovery_runs;
```

## Adding Your Own Queries

1. Create a new `.sql` file in `sql/queries/`
2. Use clear comments to explain what each query does
3. Test your queries before committing
4. Update this README with a description

Example template:

```sql
-- sql/queries/05_my_analysis.sql
-- Description of what this query file does

-- Query 1: Description
SELECT ...
FROM ...
WHERE ...;

-- Query 2: Description
SELECT ...
FROM ...
WHERE ...;
```

## Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQL Tutorial](https://www.sqltutorial.org/)
- Main project README: `../README.md`
- Quick start guide: `../QUICKSTART.md`
