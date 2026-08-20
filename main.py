import os
import contextlib
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from apscheduler.schedulers.background import BackgroundScheduler
import database
from demo.demo_router import demo_router
from demo.seeder import reset_all_demo_data

# Load environment variables
load_dotenv()

# Initialize APScheduler
scheduler = BackgroundScheduler()

def print_cache_status():
    """Prints the current contents of the local SQLite cache to the terminal."""
    locations = database.get_all_locations()
    print("\n========== [LOCAL CACHE STATE] ==========")
    if not locations:
        print("  Cache is currently empty.")
    else:
        for idx, loc in enumerate(locations, 1):
            print(f"  {idx}. AssetID: {loc['asset_id']} | Lat: {loc['lat']:.6f}, Lng: {loc['lng']:.6f} | Last Updated: {loc['last_updated']}")
    print("=========================================\n")

import sys

# Detect Demo Mode from command-line arguments (--demo / demo) or environment variable (DEMO_MODE=true)
IS_DEMO_MODE = "--demo" in sys.argv or "demo" in sys.argv or os.getenv("DEMO_MODE", "").lower() in ["true", "1", "yes"]

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    scheduler.start()
    print("Database initialized and APScheduler started.")
    
    # Run Demo Initialization on Server Startup ONLY if in demo mode
    if IS_DEMO_MODE:
        print("\n[DEMO MODE ACTIVATED] Wiping layers and populating demo datasets...")
        try:
            reset_all_demo_data()
        except Exception as e:
            print(f"[STARTUP ERROR] Demo reset encountered an issue: {e}")
    else:
        print("\n[STANDARD MODE] Server running normally. (Tip: Run with 'python main.py --demo' or visit http://localhost:8000/demo to seed demo data).")
        
    yield
    # Shutdown
    scheduler.shutdown()
    print("APScheduler shut down.")

app = FastAPI(title="QR Asset Tracker Demo Server", lifespan=lifespan)

# Mount static directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/demo-static", StaticFiles(directory="demo/static"), name="demo-static")

# Include Demo Router (for /demo dashboard and trigger APIs)
app.include_router(demo_router)

# Request Model
class UpdateRequest(BaseModel):
    asset_id: str
    lat: float
    lng: float

def get_gis():
    # 1. Direct User Login
    username = os.getenv("ARCGIS_USERNAME")
    password = os.getenv("ARCGIS_PASSWORD")
    if username and password:
        return GIS("https://www.arcgis.com", username=username, password=password)
        
    # 2. API Key Login
    api_key = os.getenv("ARCGIS_API_KEY")
    if api_key:
        return GIS("https://www.arcgis.com", api_key=api_key)

    # 3. App Login (Client Credentials)
    client_id = os.getenv("ARCGIS_CLIENT_ID")
    client_secret = os.getenv("ARCGIS_CLIENT_SECRET")
    if client_id and client_secret:
        return GIS("https://www.arcgis.com", client_id=client_id, client_secret=client_secret)
    return None

# --- Background Jobs ---

def push_5min_history():
    """Appends the latest known locations to the 5-Minute History Layer."""
    print("Running scheduled task: 5-Minute History Upload")
    gis = get_gis()
    url = os.getenv("FEATURE_LAYER_URL_5MIN")
    if not gis or not url or url == "YOUR_5MIN_HISTORY_LAYER_URL_HERE":
        print("Skipping 5-min history: Credentials or URL not configured.")
        return

    try:
        layer = FeatureLayer(url, gis=gis)
        locations = database.get_all_locations()
        if not locations:
            return
            
        adds = []
        now = datetime.now().astimezone()
        rounded_minute = (now.minute // 5) * 5
        rounded_time = now.replace(minute=rounded_minute, second=0, microsecond=0)
        # ArcGIS Date fields expect UTC Unix timestamp in milliseconds
        epoch_ms = int(rounded_time.timestamp() * 1000)
        
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
        
        layer.edit_features(adds=adds)
        print(f"Successfully uploaded {len(adds)} history points to 5-Min layer (Time: {rounded_time.strftime('%I:%M:%S %p')}).")
    except Exception as e:
        print(f"Error in 5-min history job: {str(e)}")

def push_daily_history():
    """Appends the latest known locations to the Daily History Layer."""
    print("Running scheduled task: Daily History Upload")
    gis = get_gis()
    url = os.getenv("FEATURE_LAYER_URL_DAILY")
    if not gis or not url or url == "YOUR_DAILY_HISTORY_LAYER_URL_HERE":
        print("Skipping daily history: Credentials or URL not configured.")
        return

    try:
        layer = FeatureLayer(url, gis=gis)
        locations = database.get_all_locations()
        if not locations:
            return
            
        adds = []
        now = datetime.now().astimezone()
        midnight_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
        epoch_ms_daily = int(midnight_local.timestamp() * 1000)
        
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
        
        layer.edit_features(adds=adds)
        print(f"Successfully uploaded {len(adds)} history points to Daily layer.")
    except Exception as e:
        print(f"Error in daily history job: {str(e)}")

def clear_5min_history():
    """Wipes all records from the 5-Minute History Layer at midnight."""
    print("Running scheduled task: Wiping 5-Minute History Layer")
    gis = get_gis()
    url = os.getenv("FEATURE_LAYER_URL_5MIN")
    if not gis or not url or url == "YOUR_5MIN_HISTORY_LAYER_URL_HERE":
        return

    try:
        layer = FeatureLayer(url, gis=gis)
        layer.delete_features(where="1=1")
        print("Successfully wiped 5-Min history layer.")
    except Exception as e:
        print(f"Error wiping 5-min history: {str(e)}")


# Register Jobs with APScheduler
# 1. 5-Minute History (Runs every 5 minutes)
scheduler.add_job(push_5min_history, 'interval', minutes=5)

# 2. Daily History (Runs at 11:50 PM every day, just before wipe)
scheduler.add_job(push_daily_history, 'cron', hour=23, minute=50)

# 3. Wipe 5-Minute History (Runs at Midnight every day)
scheduler.add_job(clear_5min_history, 'cron', hour=0, minute=0)


# --- API Routes ---

@app.get("/")
@app.get("/scan")
async def serve_frontend(request: Request):
    """Serve the frontend HTML file."""
    return FileResponse("static/index.html")

@app.post("/api/update")
async def update_asset_location(update_req: UpdateRequest):
    """
    Updates the local SQLite cache AND synchronously updates the Layer 0 (Live) ArcGIS server.
    """
    target_webmap_url = os.getenv("TARGET_WEB_MAP_URL")
    
    # Synchronously Update Layer 0 (Current Location)
    gis = get_gis()
    feature_layer_url = os.getenv("FEATURE_LAYER_URL")
    
    if not gis or not feature_layer_url or feature_layer_url == "YOUR_FEATURE_LAYER_URL_HERE":
        database.upsert_asset_location(update_req.asset_id, update_req.lat, update_req.lng)
        print(f"Updated local cache for Asset {update_req.asset_id} (ArcGIS skipped).")
        print_cache_status()
        return JSONResponse({
            "status": "success",
            "message": "Local cache updated. (ArcGIS skipped due to missing credentials).",
            "redirect_url": target_webmap_url
        })
        
    try:
        layer = FeatureLayer(feature_layer_url, gis=gis)
        
        # Find the matching AssetID field and detect its data type
        fields = layer.properties.get('fields', [])
        asset_field = next((f for f in fields if f.get('name', '').lower() == 'assetid'), None)
        
        if not asset_field:
            available_field_names = [f.get('name') for f in fields]
            raise HTTPException(
                status_code=400, 
                detail=f"Field 'AssetID' not found in layer. Available fields: {available_field_names}"
            )
            
        field_name = asset_field.get('name')
        field_type = asset_field.get('type', '')
        is_numeric = field_type in ['esriFieldTypeInteger', 'esriFieldTypeSmallInteger', 'esriFieldTypeOID', 'esriFieldTypeDouble', 'esriFieldTypeSingle']

        if is_numeric:
            if not update_req.asset_id.replace('-', '').replace('.', '').isdigit():
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' in ArcGIS is a number, but received non-numeric ID '{update_req.asset_id}'."
                )
            where_clause = f"{field_name} = {update_req.asset_id}"
        else:
            where_clause = f"{field_name} = '{update_req.asset_id}'"

        # Query the specific asset by its AssetID for Layer 0
        query_result = layer.query(where=where_clause)
        
        if not query_result.features:
            raise HTTPException(status_code=404, detail=f"Asset '{update_req.asset_id}' not found in Live Layer.")
            
        feature_to_update = query_result.features[0]
        
        feature_to_update.geometry = {
            "x": update_req.lng,
            "y": update_req.lat,
            "spatialReference": {"wkid": 4326}
        }
        
        update_result = layer.edit_features(updates=[feature_to_update])
        
        if update_result.get('updateResults') and update_result['updateResults'][0].get('success'):
            # Save to local cache only after Live Layer update succeeds
            database.upsert_asset_location(update_req.asset_id, update_req.lat, update_req.lng)
            print(f"Live upload complete for Asset {update_req.asset_id} to Live Layer.")
            print_cache_status()
            return JSONResponse({
                "status": "success", 
                "message": "Asset location updated successfully.",
                "redirect_url": target_webmap_url
            })
        else:
            raise Exception("Failed to apply edits to the feature layer.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating ArcGIS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Filter custom flags so uvicorn doesn't parse them as server options
    sys.argv = [arg for arg in sys.argv if arg not in ["--demo", "demo"]]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
