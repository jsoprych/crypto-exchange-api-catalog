# Agent Context - Canonical Field Mapping System (Phase 2)

## Project Overview
This is Phase 2 of the crypto-exchange-api-catalog project, extending the existing vendor API catalog with a unified field‑mapping layer.

## Core Objective
Translate vendor‑specific WebSocket/REST fields into canonical, exchange‑agnostic field names to enable:
- Single normalization logic for all exchanges
- Zero‑code addition of new exchanges (just add mapping rows)
- Consistent data models across real‑time (WebSocket) and historical (REST) data

## Bounded Scope
- **Exchanges (4 only)**: Coinbase, Kraken, Binance, Bitfinex
- **Data Types**: Ticker, Order Book, Trade, Candle (OHLC)
- **Sources**: Both WebSocket channels and REST endpoints
- **Arrays**: Fully supported (same mapping per element)

## Current Assets
1. **specifications.db** - SQLite database with schemas for all 4 exchanges
2. **PROJECT‑CONTEXT‑PHASE2.yaml** - Scope definition and requirements
3. **IMPLEMENTATION‑SUMMARY.md** - Updated with Phase 2 plan
4. **IMPLEMENTATION‑STATUS.md** - Current status and next actions
5. **Trading Daemon** - Ready for integration (has hard‑coded conversion logic to replace)

## Database Schema Additions
Three new tables to add to specifications.db:

```sql
-- CANONICAL FIELD CATALOG
CREATE TABLE canonical_fields (
    field_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    data_type TEXT NOT NULL,
    unit TEXT,
    fix_tag INTEGER,
    bloomberg_field TEXT,
    iso20022_component TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VENDOR‑FIELD → CANONICAL‑FIELD MAPPINGS
CREATE TABLE field_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,  -- "rest_endpoint", "websocket_channel"
    entity_id INTEGER NOT NULL,
    vendor_field_path TEXT NOT NULL,
    canonical_field_id TEXT NOT NULL,
    transformation TEXT,
    is_required BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (canonical_field_id) REFERENCES canonical_fields(field_id),
    UNIQUE(vendor_id, entity_type, entity_id, vendor_field_path)
);

-- CANONICAL DATA‑TYPE TEMPLATES
CREATE TABLE canonical_data_types (
    type_id TEXT PRIMARY KEY,
    description TEXT,
    fields TEXT NOT NULL,  -- JSON array of field_id references
    sample_json TEXT,
    version TEXT DEFAULT '1.0'
);
```

## Day 1 Tasks (Schema + Field Inventory)
1. **Create SQL migration script** (`sql/schema_additions.sql`)
2. **Generate field inventory** from existing `message_schema` for all 4 exchanges
3. **Propose canonical field catalog** (~20 core fields)
4. **Create mapping import scripts** (CSV → SQLite)

## Field Inventory Sources
Extract all field names from `websocket_channels.message_schema`:
- Coinbase: ticker, level2, matches, heartbeat, status
- Kraken: ticker, ohlc, trade, spread, book
- Binance: trade, kline, miniTicker, ticker, bookTicker, depth, aggTrade
- Bitfinex: ticker, trades, book, candles, status

Also extract from `rest_endpoints.response_schema` for:
- Ticker endpoints
- Candle/OHLC endpoints
- Trade endpoints
- Order book endpoints

## Success Criteria
- [ ] All 4 exchanges mapped for ticker data (WebSocket + REST)
- [ ] Trading daemon uses mappings instead of hard‑coded conversions
- [ ] Hybrid bar‑building workflow works with canonical data
- [ ] New exchange addition requires only SQL inserts, no code changes

## Integration with Trading Daemon
- Trading daemon `Registry` loads canonical mappings from `specifications.db`
- Replaces 592+ lines of hard‑coded conversion logic in Kraken adapter
- Enables: `registry.Normalize(wsMsg, "kraken", "websocket_ticker")`

## Files to Create/Modify
1. `sql/schema_additions.sql` - New mapping tables
2. `src/mapping/` - Normalization engine (new package)
3. `src/cli/mapping_commands.py` - New CLI commands
4. `scripts/generate_field_inventory.py` - Field extraction
5. `scripts/import_mappings.py` - CSV → SQLite import

## Workflow
```
Vendor Discovery → Canonical Mapping → SQLite → JSON Export + Mapping Tables
```

## Starting Point
Begin with **Day 1: Schema + Field Inventory**.
Generate field inventory first, then propose canonical fields.
