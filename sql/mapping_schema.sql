-- sql/mapping_schema.sql
-- Canonical field mapping system for vendor API normalization
-- Extends the existing vendor API catalog with unified field mapping

-- ==========================================
-- CANONICAL FIELD DEFINITIONS
-- ==========================================

-- Industry-standard field definitions that all exchanges should map to
CREATE TABLE IF NOT EXISTS canonical_fields (
    canonical_field_id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT UNIQUE NOT NULL,           -- 'bid_price', 'ask_price', 'volume_24h'
    display_name TEXT NOT NULL,                -- 'Bid Price', 'Ask Price', '24h Volume'
    description TEXT,                          -- Human-readable description
    data_type TEXT NOT NULL CHECK(data_type IN (
        'string', 'integer', 'float', 'numeric', 'boolean', 'datetime', 'array', 'object'
    )),
    category TEXT CHECK(category IN (
        'ticker', 'order_book', 'trade', 'candle', 'metadata', 'common'
    )) NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,        -- Whether this field is required for the data type
    is_core_field BOOLEAN DEFAULT TRUE,       -- Core field vs. optional extension
    example_value TEXT,                        -- Example value for documentation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for canonical_fields
CREATE INDEX IF NOT EXISTS idx_canonical_fields_category ON canonical_fields(category);
CREATE INDEX IF NOT EXISTS idx_canonical_fields_required ON canonical_fields(is_required);
CREATE INDEX IF NOT EXISTS idx_canonical_fields_core ON canonical_fields(is_core_field);

-- ==========================================
-- CANONICAL DATA TYPE TEMPLATES
-- ==========================================

-- Templates defining which canonical fields belong to each data type
CREATE TABLE IF NOT EXISTS canonical_data_types (
    data_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type_name TEXT UNIQUE NOT NULL,       -- 'ticker', 'candle', 'trade', 'order_book'
    display_name TEXT NOT NULL,                -- 'Ticker', 'Candle/OHLC', 'Trade', 'Order Book'
    description TEXT,                          -- Description of this data type
    schema_template TEXT,                      -- JSON schema template
    is_array_type BOOLEAN DEFAULT FALSE,      -- Whether this data type is typically an array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table linking data types to their required/optional fields
CREATE TABLE IF NOT EXISTS data_type_fields (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type_id INTEGER NOT NULL,
    canonical_field_id INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    array_index INTEGER,                       -- For array elements: which position in array (NULL for objects)
    field_order INTEGER DEFAULT 0,             -- Suggested display/processing order
    FOREIGN KEY (data_type_id) REFERENCES canonical_data_types(data_type_id),
    FOREIGN KEY (canonical_field_id) REFERENCES canonical_fields(canonical_field_id),
    UNIQUE(data_type_id, canonical_field_id, array_index)
);

-- ==========================================
-- VENDOR FIELD MAPPINGS
-- ==========================================

-- Maps vendor-specific field paths to canonical fields
CREATE TABLE IF NOT EXISTS field_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    canonical_field_id INTEGER NOT NULL,

    -- Source identification
    source_type TEXT NOT NULL CHECK(source_type IN ('rest', 'websocket', 'both')),
    entity_type TEXT CHECK(entity_type IN ('ticker', 'candle', 'trade', 'order_book', 'common')),

    -- Vendor-specific field path (JSON path notation)
    vendor_field_path TEXT NOT NULL,           -- e.g., 'price', 'best_bid', 'data[0].bid'

    -- REST endpoint mapping (if applicable)
    endpoint_id INTEGER,                       -- Reference to rest_endpoints table
    response_path TEXT,                        -- JSON path within REST response

    -- WebSocket channel mapping (if applicable)
    channel_id INTEGER,                        -- Reference to websocket_channels table
    message_type TEXT,                         -- Specific message type within channel

    -- Transformation rules
    transformation_rule TEXT,                  -- JSON: {"type": "scale", "factor": 0.001} or {"type": "string_to_float"}
    default_value TEXT,                        -- Default if field is missing/null

    -- Priority and validity
    priority INTEGER DEFAULT 0,                -- Higher priority = preferred mapping
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (canonical_field_id) REFERENCES canonical_fields(canonical_field_id),
    FOREIGN KEY (endpoint_id) REFERENCES rest_endpoints(endpoint_id),
    FOREIGN KEY (channel_id) REFERENCES websocket_channels(channel_id),

    -- Ensure we don't have duplicate mappings for same vendor+field+source
    UNIQUE(vendor_id, canonical_field_id, source_type, vendor_field_path, endpoint_id, channel_id)
);

-- Indexes for field_mappings
CREATE INDEX IF NOT EXISTS idx_field_mappings_vendor ON field_mappings(vendor_id);
CREATE INDEX IF NOT EXISTS idx_field_mappings_canonical ON field_mappings(canonical_field_id);
CREATE INDEX IF NOT EXISTS idx_field_mappings_source ON field_mappings(source_type);
CREATE INDEX IF NOT EXISTS idx_field_mappings_active ON field_mappings(is_active);
CREATE INDEX IF NOT EXISTS idx_field_mappings_priority ON field_mappings(priority DESC);

-- ==========================================
-- MAPPING VALIDATION & QUALITY METRICS
-- ==========================================

CREATE TABLE IF NOT EXISTS mapping_validation (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapping_id INTEGER NOT NULL,
    validation_type TEXT CHECK(validation_type IN ('syntax', 'type_check', 'live_test', 'coverage')),
    is_valid BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    test_value_input TEXT,                     -- Example input value used for testing
    test_value_output TEXT,                    -- Transformed output value
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mapping_id) REFERENCES field_mappings(mapping_id)
);

-- ==========================================
-- VIEWS FOR EASIER QUERYING
-- ==========================================

-- View showing all mappings for a vendor
CREATE VIEW IF NOT EXISTS vendor_mappings_view AS
SELECT
    v.vendor_name,
    f.field_name AS canonical_field,
    f.display_name AS canonical_display_name,
    fm.vendor_field_path,
    fm.source_type,
    fm.entity_type,
    fm.priority,
    fm.is_active,
    CASE
        WHEN fm.source_type = 'rest' AND re.path IS NOT NULL THEN re.path
        WHEN fm.source_type = 'websocket' AND wc.channel_name IS NOT NULL THEN wc.channel_name
        ELSE 'multiple/both'
    END AS source_location
FROM field_mappings fm
JOIN vendors v ON fm.vendor_id = v.vendor_id
JOIN canonical_fields f ON fm.canonical_field_id = f.canonical_field_id
LEFT JOIN rest_endpoints re ON fm.endpoint_id = re.endpoint_id
LEFT JOIN websocket_channels wc ON fm.channel_id = wc.channel_id
WHERE fm.is_active = TRUE
ORDER BY v.vendor_name, fm.priority DESC, f.field_name;

-- View showing canonical field coverage per vendor
CREATE VIEW IF NOT EXISTS vendor_coverage_view AS
SELECT
    v.vendor_name,
    dt.data_type_name,
    COUNT(DISTINCT cf.canonical_field_id) AS fields_defined,
    COUNT(DISTINCT fm.canonical_field_id) AS fields_mapped,
    ROUND(COUNT(DISTINCT fm.canonical_field_id) * 100.0 / COUNT(DISTINCT cf.canonical_field_id), 1) AS coverage_percent
FROM vendors v
CROSS JOIN canonical_data_types dt
JOIN data_type_fields dtf ON dt.data_type_id = dtf.data_type_id
JOIN canonical_fields cf ON dtf.canonical_field_id = cf.canonical_field_id
LEFT JOIN field_mappings fm ON v.vendor_id = fm.vendor_id
    AND cf.canonical_field_id = fm.canonical_field_id
    AND fm.is_active = TRUE
    AND fm.entity_type = dt.data_type_name
GROUP BY v.vendor_id, dt.data_type_id
ORDER BY v.vendor_name, dt.data_type_name;

-- ==========================================
-- TRIGGERS FOR UPDATED_AT
-- ==========================================

DROP TRIGGER IF EXISTS canonical_fields_updated;
CREATE TRIGGER IF NOT EXISTS canonical_fields_updated
AFTER UPDATE ON canonical_fields
FOR EACH ROW
BEGIN
    UPDATE canonical_fields SET updated_at = CURRENT_TIMESTAMP
    WHERE canonical_field_id = NEW.canonical_field_id;
END;

DROP TRIGGER IF EXISTS canonical_data_types_updated;
CREATE TRIGGER IF NOT EXISTS canonical_data_types_updated
AFTER UPDATE ON canonical_data_types
FOR EACH ROW
BEGIN
    UPDATE canonical_data_types SET updated_at = CURRENT_TIMESTAMP
    WHERE data_type_id = NEW.data_type_id;
END;

DROP TRIGGER IF EXISTS field_mappings_updated;
CREATE TRIGGER IF NOT EXISTS field_mappings_updated
AFTER UPDATE ON field_mappings
FOR EACH ROW
BEGIN
    UPDATE field_mappings SET updated_at = CURRENT_TIMESTAMP
    WHERE mapping_id = NEW.mapping_id;
END;

-- ==========================================
-- INITIAL CORE CANONICAL FIELDS
-- ==========================================

-- Note: These are example inserts. In production, these would be loaded via a script.
-- The following SQL is commented out but shows the expected canonical fields.

/*
-- Core ticker fields
INSERT OR IGNORE INTO canonical_fields (field_name, display_name, description, data_type, category, is_required, is_core_field) VALUES
    ('bid_price', 'Bid Price', 'Current best bid price', 'numeric', 'ticker', TRUE, TRUE),
    ('ask_price', 'Ask Price', 'Current best ask price', 'numeric', 'ticker', TRUE, TRUE),
    ('last_price', 'Last Price', 'Price of last trade', 'numeric', 'ticker', TRUE, TRUE),
    ('volume_24h', '24h Volume', '24-hour trading volume', 'numeric', 'ticker', TRUE, TRUE),
    ('high_24h', '24h High', '24-hour highest price', 'numeric', 'ticker', FALSE, TRUE),
    ('low_24h', '24h Low', '24-hour lowest price', 'numeric', 'ticker', FALSE, TRUE),
    ('open_24h', '24h Open', '24-hour opening price', 'numeric', 'ticker', FALSE, TRUE),
    ('volume_30d', '30d Volume', '30-day trading volume', 'numeric', 'ticker', FALSE, FALSE),
    ('best_bid_size', 'Best Bid Size', 'Size at best bid', 'numeric', 'ticker', FALSE, TRUE),
    ('best_ask_size', 'Best Ask Size', 'Size at best ask', 'numeric', 'ticker', FALSE, TRUE);

-- Core order book fields
INSERT OR IGNORE INTO canonical_fields (field_name, display_name, description, data_type, category, is_required, is_core_field) VALUES
    ('bid_price', 'Bid Price', 'Bid price level', 'numeric', 'order_book', TRUE, TRUE),
    ('bid_size', 'Bid Size', 'Bid size at price level', 'numeric', 'order_book', TRUE, TRUE),
    ('ask_price', 'Ask Price', 'Ask price level', 'numeric', 'order_book', TRUE, TRUE),
    ('ask_size', 'Ask Size', 'Ask size at price level', 'numeric', 'order_book', TRUE, TRUE),
    ('timestamp', 'Timestamp', 'Snapshot/update timestamp', 'datetime', 'order_book', TRUE, TRUE);

-- Core trade fields
INSERT OR IGNORE INTO canonical_fields (field_name, display_name, description, data_type, category, is_required, is_core_field) VALUES
    ('trade_id', 'Trade ID', 'Unique trade identifier', 'string', 'trade', TRUE, TRUE),
    ('price', 'Price', 'Trade price', 'numeric', 'trade', TRUE, TRUE),
    ('size', 'Size', 'Trade size/volume', 'numeric', 'trade', TRUE, TRUE),
    ('side', 'Side', 'Trade side (buy/sell)', 'string', 'trade', TRUE, TRUE),
    ('timestamp', 'Timestamp', 'Trade timestamp', 'datetime', 'trade', TRUE, TRUE);

-- Core candle/OHLC fields
INSERT OR IGNORE INTO canonical_fields (field_name, display_name, description, data_type, category, is_required, is_core_field) VALUES
    ('open', 'Open', 'Opening price', 'numeric', 'candle', TRUE, TRUE),
    ('high', 'High', 'Highest price', 'numeric', 'candle', TRUE, TRUE),
    ('low', 'Low', 'Lowest price', 'numeric', 'candle', TRUE, TRUE),
    ('close', 'Close', 'Closing price', 'numeric', 'candle', TRUE, TRUE),
    ('volume', 'Volume', 'Trading volume', 'numeric', 'candle', TRUE, TRUE),
    ('timestamp', 'Timestamp', 'Candle start time', 'datetime', 'candle', TRUE, TRUE),
    ('interval', 'Interval', 'Candle interval in seconds', 'integer', 'candle', TRUE, TRUE);

-- Common metadata fields
INSERT OR IGNORE INTO canonical_fields (field_name, display_name, description, data_type, category, is_required, is_core_field) VALUES
    ('symbol', 'Symbol', 'Trading pair symbol', 'string', 'common', TRUE, TRUE),
    ('timestamp', 'Timestamp', 'Data timestamp', 'datetime', 'common', TRUE, TRUE),
    ('sequence', 'Sequence', 'Message sequence number', 'integer', 'common', FALSE, TRUE),
    ('exchange', 'Exchange', 'Exchange name', 'string', 'common', TRUE, TRUE);

-- Canonical data types
INSERT OR IGNORE INTO canonical_data_types (data_type_name, display_name, description, is_array_type) VALUES
    ('ticker', 'Ticker', 'Real-time ticker/summary data', FALSE),
    ('order_book', 'Order Book', 'Order book snapshot/update data', TRUE),
    ('trade', 'Trade', 'Individual trade execution data', TRUE),
    ('candle', 'Candle/OHLC', 'OHLC candle data', TRUE);
*/
