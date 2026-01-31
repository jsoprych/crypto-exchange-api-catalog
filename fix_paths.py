#!/usr/bin/env python3
"""
Fix vendor field paths by removing channel name prefixes.
Updates field_mappings table to correct vendor_field_path values.
"""

import sqlite3
from pathlib import Path

db_path = Path("data/specifications.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Fixing vendor field paths...")

# Get all field mappings with their channel names
cursor.execute("""
    SELECT fm.mapping_id, fm.vendor_field_path, wc.channel_name
    FROM field_mappings fm
    JOIN websocket_channels wc ON fm.channel_id = wc.channel_id
""")

rows = cursor.fetchall()
updates = []

for row in rows:
    mapping_id = row['mapping_id']
    vendor_path = row['vendor_field_path']
    channel_name = row['channel_name']
    
    # Check if path starts with channel name prefix
    prefix = f"{channel_name}."
    if vendor_path.startswith(prefix):
        new_path = vendor_path[len(prefix):]
        updates.append((new_path, mapping_id))
        print(f"  {vendor_path} -> {new_path}")

# Apply updates
if updates:
    cursor.executemany(
        "UPDATE field_mappings SET vendor_field_path = ? WHERE mapping_id = ?",
        updates
    )
    conn.commit()
    print(f"\n✓ Updated {len(updates)} field paths")
else:
    print("\n✓ No paths need updating")

conn.close()
