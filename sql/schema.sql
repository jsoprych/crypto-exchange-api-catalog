-- sql/schema.sql
-- Database schema for Vendor API Specification system

-- ==========================================
-- VENDORS & DISCOVERY TRACKING
-- ==========================================

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT UNIQUE NOT NULL,  -- 'coinbase', 'binance', etc.
    display_name TEXT NOT NULL,        -- 'Coinbase Exchange'
    base_url TEXT,
    websocket_url TEXT,
    documentation_url TEXT,
    status TEXT CHECK(status IN ('active', 'deprecated', 'disabled')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discovery_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL,
    discovery_method TEXT,  -- 'hybrid', 'docs_only', 'live_only'
    endpoints_discovered INTEGER DEFAULT 0,
    websocket_channels_discovered INTEGER DEFAULT 0,
    products_discovered INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 0,
    error_message TEXT,
    metadata TEXT,  -- JSON metadata
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

-- ==========================================
-- REST API ENDPOINTS
-- ==========================================

CREATE TABLE IF NOT EXISTS rest_endpoints (
    endpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    path TEXT NOT NULL,  -- '/products/{product_id}/candles'
    method TEXT NOT NULL,  -- 'GET', 'POST', etc.
    authentication_required BOOLEAN DEFAULT 0,
    description TEXT,
    rate_limit_tier TEXT,  -- 'public', 'private', 'market_data'

    -- Discovery tracking
    first_discovered_run_id INTEGER,
    last_validated_run_id INTEGER,
    status TEXT CHECK(status IN ('active', 'deprecated', 'removed')) DEFAULT 'active',

    -- Request/Response schemas (JSON)
    path_parameters TEXT,  -- JSON
    query_parameters TEXT,  -- JSON
    request_schema TEXT,  -- JSON
    response_schema TEXT,  -- JSON

    -- Metadata
    vendor_metadata TEXT,  -- JSON - Raw vendor-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (first_discovered_run_id) REFERENCES discovery_runs(run_id),
    FOREIGN KEY (last_validated_run_id) REFERENCES discovery_runs(run_id),
    UNIQUE(vendor_id, path, method)
);

CREATE INDEX IF NOT EXISTS idx_endpoints_vendor ON rest_endpoints(vendor_id);
CREATE INDEX IF NOT EXISTS idx_endpoints_status ON rest_endpoints(status);
CREATE INDEX IF NOT EXISTS idx_endpoints_auth ON rest_endpoints(authentication_required);

-- ==========================================
-- WEBSOCKET CHANNELS
-- ==========================================

CREATE TABLE IF NOT EXISTS websocket_channels (
    channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    channel_name TEXT NOT NULL,  -- 'ticker', 'level2', 'matches'
    authentication_required BOOLEAN DEFAULT 0,
    description TEXT,

    -- Discovery tracking
    first_discovered_run_id INTEGER,
    last_validated_run_id INTEGER,
    status TEXT CHECK(status IN ('active', 'deprecated', 'removed')) DEFAULT 'active',

    -- Message formats (JSON)
    subscribe_format TEXT,  -- JSON
    unsubscribe_format TEXT,  -- JSON
    message_types TEXT,  -- JSON array: ['snapshot', 'update', 'l2update']
    message_schema TEXT,  -- JSON

    -- Metadata
    vendor_metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (first_discovered_run_id) REFERENCES discovery_runs(run_id),
    FOREIGN KEY (last_validated_run_id) REFERENCES discovery_runs(run_id),
    UNIQUE(vendor_id, channel_name)
);

CREATE INDEX IF NOT EXISTS idx_channels_vendor ON websocket_channels(vendor_id);
CREATE INDEX IF NOT EXISTS idx_channels_status ON websocket_channels(status);

-- ==========================================
-- PRODUCTS (Trading Pairs)
-- ==========================================

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,  -- 'BTC-USD'
    base_currency TEXT NOT NULL,  -- 'BTC'
    quote_currency TEXT NOT NULL,  -- 'USD'
    status TEXT CHECK(status IN ('online', 'offline', 'delisted')) DEFAULT 'online',

    -- Discovery tracking
    first_discovered_run_id INTEGER,
    last_validated_run_id INTEGER,

    -- Product details
    min_order_size REAL,
    max_order_size REAL,
    price_increment REAL,

    -- Metadata
    vendor_metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (first_discovered_run_id) REFERENCES discovery_runs(run_id),
    FOREIGN KEY (last_validated_run_id) REFERENCES discovery_runs(run_id),
    UNIQUE(vendor_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_products_vendor ON products(vendor_id);
CREATE INDEX IF NOT EXISTS idx_products_symbol ON products(symbol);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);

-- ==========================================
-- PRODUCT <-> ENDPOINT/CHANNEL RELATIONSHIPS
-- ==========================================

-- Which endpoints are available for which products?
CREATE TABLE IF NOT EXISTS product_rest_feeds (
    feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    endpoint_id INTEGER NOT NULL,
    feed_type TEXT,  -- 'ticker', 'candles', 'trades', 'orderbook'
    intervals TEXT,  -- JSON array: [60, 300, 900, 3600]
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (endpoint_id) REFERENCES rest_endpoints(endpoint_id),
    UNIQUE(product_id, endpoint_id)
);

-- Which WebSocket channels support which products?
CREATE TABLE IF NOT EXISTS product_ws_channels (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (channel_id) REFERENCES websocket_channels(channel_id),
    UNIQUE(product_id, channel_id)
);

-- ==========================================
-- CHANGE TRACKING
-- ==========================================

CREATE TABLE IF NOT EXISTS api_changes (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    run_id INTEGER NOT NULL,
    change_type TEXT CHECK(change_type IN (
        'endpoint_added', 'endpoint_removed', 'endpoint_modified',
        'channel_added', 'channel_removed', 'channel_modified',
        'product_added', 'product_removed', 'product_status_changed'
    )),
    entity_type TEXT CHECK(entity_type IN ('endpoint', 'channel', 'product')),
    entity_id INTEGER,
    old_value TEXT,  -- JSON
    new_value TEXT,  -- JSON
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (run_id) REFERENCES discovery_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_changes_vendor ON api_changes(vendor_id);
CREATE INDEX IF NOT EXISTS idx_changes_run ON api_changes(run_id);

-- ==========================================
-- SPECIFICATION VERSIONS
-- ==========================================

CREATE TABLE IF NOT EXISTS spec_versions (
    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    version TEXT NOT NULL,  -- '1.0', '1.1', etc.
    run_id INTEGER NOT NULL,
    spec_json TEXT NOT NULL,  -- Full JSON export for this version
    naming_convention TEXT CHECK(naming_convention IN ('snake_case', 'camelCase')),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (run_id) REFERENCES discovery_runs(run_id),
    UNIQUE(vendor_id, version)
);
