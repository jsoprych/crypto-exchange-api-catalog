-- sql/queries/04_product_catalog.sql
-- Product/symbol catalog queries

-- ==========================================
-- PRODUCT/SYMBOL CATALOG QUERIES
-- ==========================================

-- All active products for a vendor
SELECT
    p.symbol,
    p.base_currency,
    p.quote_currency,
    p.status,
    p.min_order_size,
    p.max_order_size,
    p.price_increment
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE v.vendor_name = 'coinbase'
  AND p.status = 'online'
ORDER BY p.symbol;

-- Products available on multiple vendors (arbitrage opportunities)
SELECT
    p.symbol,
    COUNT(DISTINCT v.vendor_id) as vendor_count,
    GROUP_CONCAT(v.vendor_name, ', ') as available_on
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.status = 'online'
GROUP BY p.symbol
HAVING vendor_count > 1
ORDER BY vendor_count DESC, p.symbol;

-- Find all BTC pairs across all vendors
SELECT
    v.vendor_name,
    p.symbol,
    p.quote_currency,
    p.status
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.base_currency = 'BTC'
  AND p.status = 'online'
ORDER BY p.quote_currency, v.vendor_name;

-- Products with available REST feeds
SELECT
    v.vendor_name,
    p.symbol,
    COUNT(DISTINCT prf.endpoint_id) as feed_count,
    GROUP_CONCAT(DISTINCT prf.feed_type, ', ') as available_feeds
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
JOIN product_rest_feeds prf ON p.product_id = prf.product_id
WHERE p.status = 'online'
GROUP BY p.product_id
ORDER BY feed_count DESC, v.vendor_name, p.symbol;

-- Products supporting candles/bars with intervals
SELECT
    v.vendor_name,
    p.symbol,
    prf.intervals
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
JOIN product_rest_feeds prf ON p.product_id = prf.product_id
WHERE prf.feed_type = 'candles'
  AND p.status = 'online'
ORDER BY v.vendor_name, p.symbol;

-- Recently added products (last 7 days)
SELECT
    v.vendor_name,
    p.symbol,
    p.base_currency,
    p.quote_currency,
    p.created_at
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.created_at >= DATE('now', '-7 days')
ORDER BY p.created_at DESC;
