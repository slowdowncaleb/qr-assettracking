"""
Seeder module for wiping and repopulating ArcGIS layers with demo datasets.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import database
from demo.demo_data import (
    LIVE_DEMO_ASSETS,
    generate_short_term_asu_points,
    generate_long_term_daily_points
)

load_dotenv()


def get_gis():
    """Authenticates and returns the ArcGIS GIS connection object."""
    # 1. Direct User Login
    username = os.getenv("ARCGIS_USERNAME")
    password = os.getenv("ARCGIS_PASSWORD")
    if username and password:
        return GIS("https://www.arcgis.com", username=username, password=password)
        
    # 2. API Key Login
    api_key = os.getenv("ARCGIS_API_KEY")
    if api_key:
        return GIS("https://www.arcgis.com", api_key=api_key)

    # 3. Client Credentials
    client_id = os.getenv("ARCGIS_CLIENT_ID")
    client_secret = os.getenv("ARCGIS_CLIENT_SECRET")
    if client_id and client_secret:
        return GIS("https://www.arcgis.com", client_id=client_id, client_secret=client_secret)
        
    return None


def wipe_layer(layer: FeatureLayer, layer_name: str = "Layer") -> int:
    """Deletes all existing features from the given FeatureLayer."""
    try:
        count_before = layer.query(where="1=1", return_count_only=True)
        if count_before > 0:
            layer.delete_features(where="1=1")
            print(f"  [WIPE] Cleaned {count_before} existing features from {layer_name}.")
        else:
            print(f"  [WIPE] {layer_name} is already empty.")
        return count_before
    except Exception as e:
        print(f"  [WARN] Error wiping {layer_name}: {e}")
        return 0


def wipe_all_layers(gis=None) -> dict:
    """
    Wipes all features from Layer 0, Layer 1, and Layer 2, and clears the SQLite cache.
    """
    print("\n=======================================================")
    print("[RESET ACTION] Wiping all 3 ArcGIS Feature Layers & SQLite Cache")
    print("=======================================================")
    gis = gis or get_gis()
    if not gis:
        return {"status": "error", "message": "ArcGIS authentication failed."}

    wiped_counts = {}
    for name, env_key in [("live", "FEATURE_LAYER_URL"), ("short_term", "FEATURE_LAYER_URL_5MIN"), ("long_term", "FEATURE_LAYER_URL_DAILY")]:
        url = os.getenv(env_key)
        if url and url != "YOUR_FEATURE_LAYER_URL_HERE":
            layer = FeatureLayer(url, gis=gis)
            wiped_counts[name] = wipe_layer(layer, f"{name} Layer")

    database.clear_and_set_all_locations([])
    print("  [CACHE] Cleared local SQLite cache.")
    print("=======================================================\n")
    return {
        "status": "success",
        "action": "wipe_all",
        "wiped_counts": wiped_counts,
        "message": f"Successfully wiped all 3 layers and cleared local cache."
    }


def seed_live_layer(gis=None) -> dict:
    """
    Seeds Layer 0 (Live) with 10 assets across 10 US cities (excluding Phoenix).
    Also synchronizes the local SQLite cache with these initial positions.
    """
    gis = gis or get_gis()
    url = os.getenv("FEATURE_LAYER_URL")
    if not gis or not url:
        raise ValueError("ArcGIS GIS connection or FEATURE_LAYER_URL is missing.")

    print("\n--- Seeding Live Layer (Layer 0) ---")
    layer = FeatureLayer(url, gis=gis)
    wipe_layer(layer, "Live Layer (0)")

    adds = []
    for asset in LIVE_DEMO_ASSETS:
        adds.append({
            "attributes": {
                "AssetID": asset["AssetID"],
                "Name": asset["Name"]
            },
            "geometry": {
                "x": asset["lng"],
                "y": asset["lat"],
                "spatialReference": {"wkid": 4326}
            }
        })

    res = layer.edit_features(adds=adds)
    added_count = len([r for r in res.get("addResults", []) if r.get("success")])
    print(f"  [SUCCESS] Uploaded {added_count} live assets across US cities.")

    # Synchronize local SQLite cache
    database.clear_and_set_all_locations(LIVE_DEMO_ASSETS)
    print("  [CACHE] Synchronized local SQLite cache with the 10 initial asset locations.")

    return {
        "layer": "Live Layer (0)",
        "assets_seeded": added_count,
        "assets": [f"{a['Name']} (ID: {a['AssetID']}) -> {a['city']}" for a in LIVE_DEMO_ASSETS]
    }


def seed_short_term_layer(gis=None) -> dict:
    """
    Seeds Layer 1 (Short Term - 5 Min) with 288 points (full 24-hr day of current date)
    tracing 1 asset touring ASU Tempe campus landmarks.
    """
    gis = gis or get_gis()
    url = os.getenv("FEATURE_LAYER_URL_5MIN")
    if not gis or not url:
        raise ValueError("ArcGIS GIS connection or FEATURE_LAYER_URL_5MIN is missing.")

    print("\n--- Seeding Short Term Layer (Layer 1 - ASU 5-Min Tour) ---")
    layer = FeatureLayer(url, gis=gis)
    wipe_layer(layer, "Short Term Layer (1)")

    points = generate_short_term_asu_points(asset_id=0)
    adds = []
    for pt in points:
        adds.append({
            "attributes": {
                "AssetID": pt["asset_id"],
                "TimeScan": pt["time_ms"]
            },
            "geometry": {
                "x": pt["lng"],
                "y": pt["lat"],
                "spatialReference": {"wkid": 4326}
            }
        })

    chunk_size = 100
    total_added = 0
    for i in range(0, len(adds), chunk_size):
        chunk = adds[i:i + chunk_size]
        res = layer.edit_features(adds=chunk)
        successes = len([r for r in res.get("addResults", []) if r.get("success")])
        total_added += successes

    print(f"  [SUCCESS] Uploaded {total_added} points (5-min intervals for today) around ASU Tempe.")
    return {
        "layer": "Short Term Layer (1)",
        "points_seeded": total_added,
        "date_covered": datetime.now().strftime("%Y-%m-%d"),
        "location": "ASU Tempe Campus Landmarks"
    }


def seed_long_term_layer(gis=None) -> dict:
    """
    Seeds Layer 2 (Long Term - Daily) with 30 days of daily positions leading up to today
    for 2 assets (Asset 0 'Saguaro' and Asset 1 'Joshua Tree') moving across US cities.
    """
    gis = gis or get_gis()
    url = os.getenv("FEATURE_LAYER_URL_DAILY")
    if not gis or not url:
        raise ValueError("ArcGIS GIS connection or FEATURE_LAYER_URL_DAILY is missing.")

    print("\n--- Seeding Long Term Layer (Layer 2 - 30-Day Nationwide Journey) ---")
    layer = FeatureLayer(url, gis=gis)
    wipe_layer(layer, "Long Term Layer (2)")

    points = generate_long_term_daily_points()
    adds = []
    for pt in points:
        adds.append({
            "attributes": {
                "AssetID": pt["asset_id"],
                "DateScan": pt["date_ms"]
            },
            "geometry": {
                "x": pt["lng"],
                "y": pt["lat"],
                "spatialReference": {"wkid": 4326}
            }
        })

    res = layer.edit_features(adds=adds)
    total_added = len([r for r in res.get("addResults", []) if r.get("success")])
    print(f"  [SUCCESS] Uploaded {total_added} daily journey points (30 days x 2 assets) across US cities.")

    return {
        "layer": "Long Term Layer (2)",
        "points_seeded": total_added,
        "days_covered": 30,
        "assets_tracked": ["Saguaro (ID: 0)", "Joshua Tree (ID: 1)"]
    }


def seed_all_layers(gis=None) -> dict:
    """
    Populates all 3 layers with the demo dataset.
    """
    print("\n=======================================================")
    print("[RESEED ACTION] Populating Demo Datasets to ArcGIS")
    print("=======================================================")
    gis = gis or get_gis()
    if not gis:
        return {"status": "error", "message": "ArcGIS authentication failed."}

    results = {
        "live_layer": seed_live_layer(gis),
        "short_term_layer": seed_short_term_layer(gis),
        "long_term_layer": seed_long_term_layer(gis),
        "status": "success",
        "action": "seed_all",
        "timestamp": datetime.now().isoformat()
    }
    print("=======================================================\n")
    return results


def reset_all_demo_data(gis=None) -> dict:
    """
    Combined convenience routine: Wipes and repopulates all 3 layers.
    """
    return seed_all_layers(gis)


def trigger_5min_upload(gis=None) -> dict:
    """
    Simulates the scheduled 5-minute batch upload on demand.
    Appends the latest known locations from local cache to Layer 1.
    """
    print("\n[MANUAL TRIGGER] 5-Minute History Snapshot Upload")
    gis = gis or get_gis()
    url = os.getenv("FEATURE_LAYER_URL_5MIN")
    if not gis or not url:
        return {"status": "error", "message": "GIS connection or URL not configured."}

    locations = database.get_all_locations()
    if not locations:
        return {"status": "warning", "message": "Local cache is empty."}

    layer = FeatureLayer(url, gis=gis)
    now = datetime.now().astimezone()
    rounded_minute = (now.minute // 5) * 5
    rounded_time = now.replace(minute=rounded_minute, second=0, microsecond=0)
    epoch_ms = int(rounded_time.timestamp() * 1000)

    adds = []
    for loc in locations:
        adds.append({
            "attributes": {
                "AssetID": int(loc["asset_id"]),
                "TimeScan": epoch_ms
            },
            "geometry": {
                "x": float(loc["lng"]),
                "y": float(loc["lat"]),
                "spatialReference": {"wkid": 4326}
            }
        })

    res = layer.edit_features(adds=adds)
    added = len([r for r in res.get("addResults", []) if r.get("success")])
    time_str = rounded_time.strftime('%I:%M:%S %p')
    print(f"  [SUCCESS] Uploaded {added} points to 5-Min layer (Timestamp: {time_str}).")
    
    return {
        "status": "success",
        "points_uploaded": added,
        "time_stamped": time_str,
        "message": f"Successfully uploaded {added} points to 5-Min History Layer ({time_str})."
    }


def trigger_midnight_rollover(gis=None) -> dict:
    """
    Simulates the midnight rollover workflow:
    1. Uploads latest locations to the Daily Long-Term Layer.
    2. Wipes the 5-Minute Short-Term Layer for the next day.
    """
    print("\n[MANUAL TRIGGER] Midnight Rollover Workflow")
    gis = gis or get_gis()
    daily_url = os.getenv("FEATURE_LAYER_URL_DAILY")
    short_url = os.getenv("FEATURE_LAYER_URL_5MIN")

    if not gis or not daily_url or not short_url:
        return {"status": "error", "message": "GIS connection or layer URLs not configured."}

    locations = database.get_all_locations()
    now = datetime.now().astimezone()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    epoch_ms_daily = int(today_midnight.timestamp() * 1000)

    # 1. Archive to Daily Layer
    daily_layer = FeatureLayer(daily_url, gis=gis)
    adds = []
    for loc in locations:
        adds.append({
            "attributes": {
                "AssetID": int(loc["asset_id"]),
                "DateScan": epoch_ms_daily
            },
            "geometry": {
                "x": float(loc["lng"]),
                "y": float(loc["lat"]),
                "spatialReference": {"wkid": 4326}
            }
        })
    daily_res = daily_layer.edit_features(adds=adds)
    daily_added = len([r for r in daily_res.get("addResults", []) if r.get("success")])

    # 2. Wipe 5-Minute Short-Term Layer
    short_layer = FeatureLayer(short_url, gis=gis)
    wiped_count = wipe_layer(short_layer, "5-Minute Short-Term Layer")

    print(f"  [SUCCESS] Archived {daily_added} assets to Daily Layer and wiped 5-Minute Layer ({wiped_count} points cleared).")

    return {
        "status": "success",
        "daily_archived_count": daily_added,
        "short_term_wiped_count": wiped_count,
        "message": f"Midnight rollover executed: {daily_added} points archived to Daily layer, Short-Term layer wiped."
    }
