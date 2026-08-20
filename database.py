import sqlite3
import datetime
import os

DB_FILE = "cache.db"

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_locations (
            asset_id TEXT PRIMARY KEY,
            lat REAL,
            lng REAL,
            last_updated TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def upsert_asset_location(asset_id: str, lat: float, lng: float):
    """Inserts or updates the latest location for an asset."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc)
    cursor.execute('''
        INSERT INTO asset_locations (asset_id, lat, lng, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(asset_id) DO UPDATE SET
            lat=excluded.lat,
            lng=excluded.lng,
            last_updated=excluded.last_updated
    ''', (asset_id, lat, lng, now))
    conn.commit()
    conn.close()

def get_all_locations():
    """Returns a list of all latest asset locations in the cache."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT asset_id, lat, lng, last_updated FROM asset_locations')
    rows = cursor.fetchall()
    conn.close()
    return [{"asset_id": row["asset_id"], "lat": row["lat"], "lng": row["lng"], "last_updated": row["last_updated"]} for row in rows]

def clear_and_set_all_locations(locations: list):
    """Wipes the cache and populates it with a list of initial asset locations."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM asset_locations')
    now = datetime.datetime.now(datetime.timezone.utc)
    for loc in locations:
        asset_id = loc.get("AssetID") if "AssetID" in loc else loc.get("asset_id")
        cursor.execute('''
            INSERT INTO asset_locations (asset_id, lat, lng, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (str(asset_id), float(loc["lat"]), float(loc["lng"]), now))
    conn.commit()
    conn.close()
