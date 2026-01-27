-- sql/queries/02_endpoint_discovery.sql
-- REST endpoint discovery and analysis queries

-- ==========================================
-- REST ENDPOINT DISCOVERY QUERIES
-- ==========================================

-- All REST endpoints for a specific vendor (replace 'coinbase' with desired vendor)
SELECT
    e.method,
    e.path,
    e.description,
    e.authentication_required,
    e.rate_limit_tier,
    e.status
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE v.vendor_name = 'coinbase'
  AND e.status = 'active'
ORDER BY e.path, e.method;

-- Public (unauthenticated) endpoints only
SELECT
    v.vendor_name,
    e.method,
    e.path,
    e.description
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.authentication_required = 0
  AND e.status = 'active'
ORDER BY v.vendor_name, e.path;

-- Authenticated endpoints requiring API keys
SELECT
    v.vendor_name,
    e.method,
    e.path,
    e.description,
    e.rate_limit_tier
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.authentication_required = 1
  AND e.status = 'active'
ORDER BY v.vendor_name, e.rate_limit_tier, e.path;

-- Endpoints by HTTP method distribution
SELECT
    v.vendor_name,
    e.method,
    COUNT(*) as endpoint_count
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.status = 'active'
GROUP BY v.vendor_id, e.method
ORDER BY v.vendor_name, endpoint_count DESC;

-- Recently added endpoints (last 30 days)
SELECT
    v.vendor_name,
    e.path,
    e.method,
    e.description,
    e.created_at
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.created_at >= DATE('now', '-30 days')
ORDER BY e.created_at DESC;

-- Deprecated or removed endpoints
SELECT
    v.vendor_name,
    e.path,
    e.method,
    e.status,
    e.updated_at
FROM rest_endpoints e
JOIN vendors v ON e.vendor_id = v.vendor_id
WHERE e.status IN ('deprecated', 'removed')
ORDER BY e.updated_at DESC;
