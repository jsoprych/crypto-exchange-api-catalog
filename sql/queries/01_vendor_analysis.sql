-- sql/queries/01_vendor_analysis.sql
-- Vendor analysis and comparison queries

-- ==========================================
-- VENDOR ANALYSIS QUERIES
-- ==========================================

-- List all vendors with their current API coverage
SELECT
    v.vendor_name,
    v.display_name,
    v.status,
    COUNT(DISTINCT e.endpoint_id) as total_rest_endpoints,
    COUNT(DISTINCT w.channel_id) as total_ws_channels,
    COUNT(DISTINCT p.product_id) as total_products,
    v.documentation_url,
    v.created_at
FROM vendors v
LEFT JOIN rest_endpoints e ON v.vendor_id = e.vendor_id AND e.status = 'active'
LEFT JOIN websocket_channels w ON v.vendor_id = w.vendor_id AND w.status = 'active'
LEFT JOIN products p ON v.vendor_id = p.vendor_id AND p.status = 'online'
GROUP BY v.vendor_id
ORDER BY v.vendor_name;

-- Most recently updated vendor
SELECT
    v.vendor_name,
    v.updated_at,
    dr.run_timestamp as last_discovery_run,
    dr.success as last_run_successful
FROM vendors v
LEFT JOIN discovery_runs dr ON v.vendor_id = dr.vendor_id
WHERE dr.run_timestamp = (
    SELECT MAX(run_timestamp)
    FROM discovery_runs
    WHERE vendor_id = v.vendor_id
)
ORDER BY v.updated_at DESC;

-- Vendor health check: Find vendors with no recent discovery runs
SELECT
    v.vendor_name,
    v.display_name,
    MAX(dr.run_timestamp) as last_discovery,
    JULIANDAY('now') - JULIANDAY(MAX(dr.run_timestamp)) as days_since_last_run
FROM vendors v
LEFT JOIN discovery_runs dr ON v.vendor_id = dr.vendor_id
GROUP BY v.vendor_id
HAVING days_since_last_run > 7 OR last_discovery IS NULL
ORDER BY days_since_last_run DESC;
