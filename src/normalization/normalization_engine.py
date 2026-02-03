"""
Normalization Engine for canonical field mapping.

This module provides the NormalizationEngine class which loads field mappings
from the database and applies them to vendor-specific data to produce
canonical, exchange-agnostic data structures.
"""

import json
import re
import sqlite3
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import datetime


class NormalizationEngine:
    """
    Main normalization engine for applying field mappings to vendor data.

    The engine loads field mappings from the SQLite database and applies them
    to convert vendor-specific field names and structures to canonical,
    exchange-agnostic field names.
    """

    def __init__(self, db_path: Union[str, Path]):
        """
        Initialize normalization engine with database path.

        Args:
            db_path: Path to SQLite database containing field mappings
        """
        self.db_path = str(db_path)
        self.conn = None
        self._mappings_cache: Dict[str, List[Dict]] = {}

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.

        Returns:
            SQLite connection object
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def load_mappings(
        self,
        vendor_name: str,
        data_type: str,
        source_type: str = 'websocket'
    ) -> List[Dict[str, Any]]:
        """
        Load field mappings for a specific vendor and data type.

        Args:
            vendor_name: Vendor name (e.g., 'coinbase', 'binance')
            data_type: Data type (e.g., 'ticker', 'trade', 'order_book', 'candle')
            source_type: Source type ('rest', 'websocket', or 'both')

        Returns:
            List of mapping dictionaries sorted by priority (highest first)
        """
        cache_key = f"{vendor_name}:{data_type}:{source_type}"
        if cache_key in self._mappings_cache:
            return self._mappings_cache[cache_key]

        conn = self.connect()
        cursor = conn.cursor()

        # Query to get all active mappings for this vendor and data type
        query = """
            SELECT
                fm.mapping_id,
                fm.vendor_field_path,
                fm.entity_type,
                fm.transformation_rule,
                fm.priority,
                cf.field_name as canonical_field_name,
                cf.data_type as canonical_data_type,
                fm.source_type,
                fm.channel_id,
                fm.endpoint_id
            FROM field_mappings fm
            JOIN vendors v ON fm.vendor_id = v.vendor_id
            JOIN canonical_fields cf ON fm.canonical_field_id = cf.canonical_field_id
            WHERE v.vendor_name = ?
                AND fm.entity_type = ?
                AND fm.is_active = TRUE
                AND (fm.source_type = ? OR fm.source_type = 'both')
            ORDER BY fm.priority DESC, fm.mapping_id
        """

        cursor.execute(query, (vendor_name, data_type, source_type))
        rows = cursor.fetchall()

        mappings = []
        for row in rows:
            mapping = dict(row)
            # Parse transformation rule JSON if present
            if mapping['transformation_rule']:
                try:
                    mapping['transformation_rule'] = json.loads(mapping['transformation_rule'])
                except json.JSONDecodeError:
                    mapping['transformation_rule'] = None
            else:
                mapping['transformation_rule'] = None

            mappings.append(mapping)

        self._mappings_cache[cache_key] = mappings
        return mappings

    def normalize(
        self,
        data: Union[Dict, List],
        vendor_name: str,
        data_type: str,
        source_type: str = 'websocket',
        channel_name: Optional[str] = None,
        endpoint_path: Optional[str] = None
    ) -> Union[Dict, List]:
        """
        Normalize vendor data using field mappings.

        Args:
            data: Vendor-specific data (dict or list)
            vendor_name: Vendor name (e.g., 'coinbase')
            data_type: Data type (e.g., 'ticker', 'trade')
            source_type: Source type ('rest' or 'websocket')
            channel_name: WebSocket channel name (optional, for logging/debugging)
            endpoint_path: REST endpoint path (optional, for logging/debugging)

        Returns:
            Normalized data with canonical field names
        """
        # Load mappings for this vendor and data type
        mappings = self.load_mappings(vendor_name, data_type, source_type)

        if not mappings:
            # No mappings found, return original data (or empty dict?)
            return {}

        if isinstance(data, list):
            # Handle array data - apply normalization to each element
            return [self._normalize_single(item, mappings, data_type, vendor_name) for item in data]
        else:
            # Handle single object
            return self._normalize_single(data, mappings, data_type, vendor_name)

    def _normalize_single(
        self,
        data: Dict[str, Any],
        mappings: List[Dict[str, Any]],
        data_type: str,
        vendor_name: str
    ) -> Dict[str, Any]:
        """
        Normalize a single data object.

        Args:
            data: Single vendor data object
            mappings: Field mappings for this vendor/data_type
            data_type: Data type (for context in transformations)

        Returns:
            Normalized single object
        """
        normalized = {}

        for mapping in mappings:
            vendor_path = mapping['vendor_field_path']
            canonical_field = mapping['canonical_field_name']
            transform_rule = mapping['transformation_rule']

            # Extract value from vendor data using path
            value = self._get_value_by_path(data, vendor_path)

            if value is not None:
                # Apply transformation if specified
                if transform_rule:
                    value = self._apply_transformation(value, transform_rule, data_type)

                # Store in normalized result
                normalized[canonical_field] = value

        # Add metadata
        normalized['_normalized'] = True
        normalized['_mappings_applied'] = len([m for m in mappings if self._get_value_by_path(data, m['vendor_field_path']) is not None])

        # Add derived fields
        normalized = self._add_derived_fields(normalized, vendor_name, data_type, data)

        return normalized

    def _add_derived_fields(
        self,
        normalized: Dict[str, Any],
        vendor_name: str,
        data_type: str,
        original_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add derived/implied fields that aren't directly mapped.

        Args:
            normalized: Partially normalized data (after mappings applied)
            vendor_name: Vendor name (e.g., 'coinbase')
            data_type: Data type (e.g., 'ticker')
            original_data: Original vendor data (for reference)

        Returns:
            Normalized data with derived fields added
        """
        # 1. Always add exchange field (implicit metadata)
        if 'exchange' not in normalized:
            normalized['exchange'] = vendor_name

        # 2. Handle missing timestamp
        if 'timestamp' not in normalized:
            # Try to derive from various sources
            timestamp = self._derive_timestamp(original_data, vendor_name, data_type)
            if timestamp:
                normalized['timestamp'] = timestamp
            else:
                # Fallback to current time (with warning in production)
                normalized['timestamp'] = datetime.datetime.now(datetime.timezone.utc)

        # 3. Handle missing symbol for Bitfinex
        if 'symbol' not in normalized and vendor_name == 'bitfinex':
            # Bitfinex symbol is in channel subscription, not message
            # Could extract from context or leave empty (trading daemon knows symbol)
            pass  # Trading daemon should provide symbol from context

        # 4. Handle missing open_24h for Bitfinex
        if 'open_24h' not in normalized and vendor_name == 'bitfinex':
            # Bitfinex doesn't provide open_24h in ticker
            # Could fetch from REST endpoint or use previous close
            pass  # Optional field, can be omitted

        # 5. Add metadata about derivation
        normalized['_derived_fields'] = [
            field for field in ['exchange', 'timestamp', 'symbol', 'open_24h']
            if field in normalized and field not in original_data
        ]

        return normalized

    def _derive_timestamp(
        self,
        data: Dict[str, Any],
        vendor_name: str,
        data_type: str
    ) -> Optional[datetime.datetime]:
        """
        Derive timestamp from various vendor-specific fields.

        Args:
            data: Original vendor data
            vendor_name: Vendor name
            data_type: Data type

        Returns:
            datetime object or None if cannot derive
        """
        # Try common timestamp field names
        timestamp_fields = []

        if vendor_name == 'coinbase':
            timestamp_fields = ['time', 'timestamp', 'created_at']
        elif vendor_name == 'binance':
            timestamp_fields = ['E', 'event_time', 'timestamp']
        elif vendor_name == 'kraken':
            timestamp_fields = ['timestamp']  # Kraken doesn't have in ticker
        elif vendor_name == 'bitfinex':
            timestamp_fields = ['timestamp', 'mts']  # Bitfinex uses mts (milliseconds)

        for field in timestamp_fields:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    # Assume milliseconds since epoch
                    return datetime.datetime.fromtimestamp(value / 1000.0, datetime.timezone.utc)
                elif isinstance(value, str):
                    # Try ISO format
                    try:
                        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        pass

        # Check for sequence-based timestamp (Kraken)
        if vendor_name == 'kraken' and 'channelID' in data:
            # Kraken uses channelID as sequence, no timestamp
            # Could use message receipt time instead
            pass

        return None

    def _get_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """
        Extract value from nested dictionary using dot notation path.

        Supports:
          - Simple paths: 'field.subfield'
          - Array indices: 'data[0].price'
          - Mixed: 'items[1].details.price'

        Args:
            data: Source dictionary
            path: Dot notation path

        Returns:
            Extracted value or None if path doesn't exist
        """
        if not path or not data:
            return None

        # Split path by dots, but handle array indices
        parts = []
        current = ''
        in_bracket = False

        for char in path:
            if char == '[':
                if current:
                    parts.append(current)
                current = '['
                in_bracket = True
            elif char == ']':
                current += char
                parts.append(current)
                current = ''
                in_bracket = False
            elif char == '.' and not in_bracket:
                if current:
                    parts.append(current)
                current = ''
            else:
                current += char

        if current:
            parts.append(current)

        # Navigate through data structure
        current_data = data
        for part in parts:
            if part.startswith('[') and part.endswith(']'):
                # Array index
                try:
                    index = int(part[1:-1])
                    if isinstance(current_data, list) and 0 <= index < len(current_data):
                        current_data = current_data[index]
                    else:
                        return None
                except (ValueError, TypeError):
                    return None
            else:
                # Dictionary key
                if isinstance(current_data, dict) and part in current_data:
                    current_data = current_data[part]
                else:
                    return None

        return current_data

    def _apply_transformation(
        self,
        value: Any,
        rule: Dict[str, Any],
        data_type: str
    ) -> Any:
        """
        Apply transformation rule to value.

        Supported transformation types:
          - 'identity': Return value as-is
          - 'string_to_numeric': Convert string to float/int
          - 'string_to_integer': Convert string to integer
          - 'string_to_datetime': Convert string to datetime
          - 'scale': Multiply by factor
          - 'inverse': 1/value

        Args:
            value: Input value
            rule: Transformation rule dictionary
            data_type: Data type for context

        Returns:
            Transformed value
        """
        if not rule or 'type' not in rule:
            return value

        transform_type = rule['type']

        try:
            if transform_type == 'identity':
                return value

            elif transform_type == 'string_to_numeric':
                # Try to convert string to appropriate numeric type
                if isinstance(value, str):
                    # Remove commas, spaces
                    cleaned = value.replace(',', '').strip()
                    # Check if it's an integer or float
                    if '.' in cleaned:
                        return float(cleaned)
                    else:
                        return int(cleaned)
                elif isinstance(value, (int, float)):
                    return value
                else:
                    return value

            elif transform_type == 'string_to_integer':
                if isinstance(value, str):
                    return int(value.replace(',', '').strip())
                elif isinstance(value, (int, float)):
                    return int(value)
                else:
                    return value

            elif transform_type == 'string_to_datetime':
                if isinstance(value, str):
                    # Try to parse ISO 8601 format
                    # This is a simple implementation - could be extended
                    # to handle various datetime formats
                    if 'format' in rule and rule['format'] == 'iso8601':
                        # Basic ISO 8601 parsing
                        from datetime import datetime
                        # Try to parse with timezone info if present
                        try:
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            # Fallback to simpler parsing
                            pass

                    # Return string as-is for now - could add more parsers
                    return value
                else:
                    return value

            elif transform_type == 'ms_to_datetime':
                if isinstance(value, (int, float)):
                    # Convert milliseconds to datetime
                    from datetime import datetime, timezone
                    # Convert to seconds
                    timestamp_seconds = value / 1000.0
                    return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                elif isinstance(value, str):
                    # Try to parse as integer first
                    try:
                        ms_value = int(value)
                        from datetime import datetime, timezone
                        timestamp_seconds = ms_value / 1000.0
                        return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                    except (ValueError, TypeError):
                        return value
                else:
                    return value

            elif transform_type == 'array_extract':
                # Extract element from array and optionally apply subtype transformation
                if isinstance(value, list):
                    index = rule.get('index', 0)
                    if 0 <= index < len(value):
                        element = value[index]
                        # Apply subtype transformation if specified
                        subtype = rule.get('subtype')
                        if subtype:
                            # Recursively apply subtype transformation
                            subtype_rule = {'type': subtype}
                            return self._apply_transformation(element, subtype_rule, data_type)
                        return element
                return None

            elif transform_type == 'array_extract_by_field':
                # Extract value from array of field-value pairs
                # Expects array like [["field1", "value1"], ["field2", "value2"]]
                if isinstance(value, list):
                    field_name = rule.get('field_name')
                    if field_name:
                        for item in value:
                            if isinstance(item, list) and len(item) >= 2:
                                if str(item[0]) == field_name:
                                    element = item[1]
                                    # Apply subtype transformation if specified
                                    subtype = rule.get('subtype')
                                    if subtype:
                                        subtype_rule = {'type': subtype}
                                        return self._apply_transformation(element, subtype_rule, data_type)
                                    return element
                return None

            elif transform_type == 'scale':
                if isinstance(value, (int, float)):
                    factor = rule.get('factor', 1.0)
                    return value * factor
                else:
                    return value

            elif transform_type == 'inverse':
                if isinstance(value, (int, float)) and value != 0:
                    return 1.0 / value
                else:
                    return value

            else:
                # Unknown transformation type
                return value

        except (ValueError, TypeError, AttributeError) as e:
            # Transformation failed, return original value
            return value

    def get_coverage_stats(self, vendor_name: str) -> Dict[str, Dict]:
        """
        Get coverage statistics for a vendor.

        Args:
            vendor_name: Vendor name

        Returns:
            Dictionary with coverage statistics per data type
        """
        conn = self.connect()
        cursor = conn.cursor()

        query = """
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = ?
            ORDER BY data_type_name
        """

        cursor.execute(query, (vendor_name,))
        rows = cursor.fetchall()

        stats = {}
        for row in rows:
            data_type = row['data_type_name']
            stats[data_type] = {
                'fields_defined': row['fields_defined'],
                'fields_mapped': row['fields_mapped'],
                'coverage_percent': row['coverage_percent']
            }

        return stats

    def test_mapping(
        self,
        vendor_name: str,
        data_type: str,
        test_data: Dict[str, Any],
        source_type: str = 'websocket'
    ) -> Dict[str, Any]:
        """
        Test mapping with sample data.

        Args:
            vendor_name: Vendor name
            data_type: Data type
            test_data: Sample vendor data
            source_type: Source type

        Returns:
            Dictionary with test results including:
              - normalized: Normalized output
              - applied_mappings: List of mappings that were applied
              - missed_mappings: List of mappings that couldn't be applied
        """
        mappings = self.load_mappings(vendor_name, data_type, source_type)

        applied = []
        missed = []

        # Check each mapping
        for mapping in mappings:
            vendor_path = mapping['vendor_field_path']
            value = self._get_value_by_path(test_data, vendor_path)

            if value is not None:
                applied.append({
                    'vendor_path': vendor_path,
                    'canonical_field': mapping['canonical_field_name'],
                    'value_found': value,
                    'transformation': mapping['transformation_rule']
                })
            else:
                missed.append({
                    'vendor_path': vendor_path,
                    'canonical_field': mapping['canonical_field_name'],
                    'reason': f"Path not found in test data"
                })

        # Apply normalization
        normalized = self.normalize(test_data, vendor_name, data_type, source_type)

        return {
            'normalized': normalized,
            'applied_mappings': applied,
            'missed_mappings': missed,
            'total_mappings': len(mappings),
            'applied_count': len(applied),
            'missed_count': len(missed)
        }


# Convenience functions
def normalize_message(
    message: Union[Dict, List],
    vendor: str,
    data_type: str,
    db_path: Union[str, Path],
    source_type: str = 'websocket'
) -> Union[Dict, List]:
    """
    Convenience function to normalize a message.

    Args:
        message: Vendor message to normalize
        vendor: Vendor name
        data_type: Data type
        db_path: Path to database
        source_type: Source type

    Returns:
        Normalized message
    """
    with NormalizationEngine(db_path) as engine:
        return engine.normalize(message, vendor, data_type, source_type)


def get_vendor_coverage(
    vendor: str,
    db_path: Union[str, Path]
) -> Dict[str, Dict]:
    """
    Get coverage statistics for a vendor.

    Args:
        vendor: Vendor name
        db_path: Path to database

    Returns:
        Coverage statistics
    """
    with NormalizationEngine(db_path) as engine:
        return engine.get_coverage_stats(vendor)
