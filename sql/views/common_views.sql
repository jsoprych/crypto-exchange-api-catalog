-- sql/views/common_views.sql
-- Common views for easier querying

-- ==========================================
-- COMMON VIEWS FOR EASIER QUERYING
-- ==========================================

-- Active API surface across all vendors
CREATE VIEW IF NOT EXISTS v_active_api_surface AS
SELECT
    v.vendor_id,
    v.vendor_name,
    e.endpoint_id,
    'rest' as api_type,
    e.method || ' ' || e.path as api_identifier,
    e.authentication_required,
    e.status
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.status = 'active'
UNION ALL
SELECT
    v.vendor_id,
    v.vendor_name,
    w.channel_id,
    'websocket' as api_type,
    w.channel_name as api_identifier,
    w.authentication_required,
    w.status
FROM websocket_channels w
JOIN vendors v ON w.vendor_id = v.vendor_id
WHERE w.status = 'active';

-- Product feed availability
CREATE VIEW IF NOT EXISTS v_product_feed_availability AS
SELECT
    v.vendor_name,
    p.symbol,
    p.base_currency,
    p.quote_currency,
    p.status as product_status,
    COUNT(DISTINCT prf.endpoint_id) as rest_feed_count,
    COUNT(DISTINCT pwc.channel_id) as ws_channel_count,
    GROUP_CONCAT(DISTINCT prf.feed_type, ', ') as rest_feeds,
    GROUP_CONCAT(DISTINCT (SELECT channel_name FROM websocket_channels WHERE channel_id = pwc.channel_id), ', ') as ws_channels
FROM products p
JOIN vendors v ON p.vendor_id = v.vendor_id
LEFT JOIN product_rest_feeds prf ON p.product_id = prf.product_id
LEFT JOIN product_ws_channels pwc ON p.product_id = pwc.product_id
GROUP BY p.product_id;

-- Latest discovery run per vendor
CREATE VIEW IF NOT EXISTS v_latest_discovery_runs AS
SELECT
    dr.*,
    v.vendor_name
FROM discovery_runs dr
JOIN vendors v ON dr.vendor_id = v.vendor_id
WHERE dr.run_id = (
    SELECT MAX(run_id)
    FROM discovery_runs
    WHERE vendor_id = dr.vendor_id
);

-- Recent API changes (last 30 days)
CREATE VIEW IF NOT EXISTS v_recent_api_changes AS
SELECT
    v.vendor_name,
    ac.change_type,
    ac.entity_type,
    ac.detected_at,
    ac.old_value,
    ac.new_value
FROM api_changes ac
JOIN vendors v ON ac.vendor_id = v.vendor_id
WHERE ac.detected_at >= DATE('now', '-30 days')
ORDER BY ac.detected_at DESC;
