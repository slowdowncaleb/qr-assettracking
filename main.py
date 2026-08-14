import os
import contextlib
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from apscheduler.schedulers.background import BackgroundScheduler
import database

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

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    scheduler.start()
    print("Database initialized and APScheduler started.")
    update_webmap_timelines()
    yield
    # Shutdown
    scheduler.shutdown()
    print("APScheduler shut down.")

app = FastAPI(title="QR Asset Tracker", lifespan=lifespan)

# Mount the static directory to serve CSS, JS, and Images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request Model
class UpdateRequest(BaseModel):
    asset_id: str
    lat: float
    lng: float

def get_gis():
    # 1. Direct User Login (Full owner permissions over Web Maps)
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
            # We add new features to build a history timeline.
            adds.append({
                "attributes": {
                    "AssetID": loc["asset_id"],
                    "TimeScan": epoch_ms
                },
                "geometry": {
                    "x": loc["lng"],
                    "y": loc["lat"],
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
                    "AssetID": loc["asset_id"],
                    "DateScan": epoch_ms_daily
                },
                "geometry": {
                    "x": loc["lng"],
                    "y": loc["lat"],
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
        # Delete all features by matching all OBJECTIDs (where 1=1)
        layer.delete_features(where="1=1")
        print("Successfully wiped 5-Min history layer.")
    except Exception as e:
        print(f"Error wiping 5-min history: {str(e)}")
    
    # Update timeline widgets on both webmaps after daily cycle
    update_webmap_timelines()

def update_webmap_timelines():
    """Updates the Time Slider widget on both the Short Term and Long Term Web Maps."""
    print("Running task: Updating Web Map Timeline Widgets...")
    gis = get_gis()
    if not gis:
        print("Skipping Web Map timeline update: Credentials not configured.")
        return

    now = datetime.now().astimezone()
    today_midnight_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_midnight_end = today_midnight_start + timedelta(days=1)
    
    start_ms_today = int(today_midnight_start.timestamp() * 1000)
    end_ms_today = int(today_midnight_end.timestamp() * 1000)

    # 1. Update Short Term Web Map (5-Min Layer: Current day midnight to midnight, 5-min intervals)
    short_map_id = os.getenv("WEBMAP_ID_SHORT")
    if short_map_id:
        try:
            item = gis.content.get(short_map_id)
            if item:
                data = item.get_data()
                data["widgets"] = data.get("widgets", {})
                data["widgets"]["timeSlider"] = {
                    "properties": {
                        "startTime": start_ms_today,
                        "endTime": end_ms_today,
                        "currentTimeExtent": [start_ms_today, start_ms_today],
                        "thumbCount": 1,
                        "thumbMovingRate": 2000,
                        "timeStopInterval": {
                            "interval": 5,
                            "units": "esriTimeUnitsMinutes"
                        }
                    }
                }
                item.update(data=data)
                print(f"Successfully updated Timeline on Short Term Web Map ({short_map_id}) to current day (00:00 to 23:59).")
        except Exception as e:
            print(f"Error updating Short Term Web Map timeline: {str(e)}")

    # 2. Update Long Term Web Map (Daily Layer: Earliest day midnight to current day, 1-day intervals)
    long_map_id = os.getenv("WEBMAP_ID_LONG")
    daily_layer_url = os.getenv("FEATURE_LAYER_URL_DAILY")
    if long_map_id:
        try:
            earliest_ms = start_ms_today
            if daily_layer_url and daily_layer_url != "YOUR_DAILY_HISTORY_LAYER_URL_HERE":
                try:
                    daily_layer = FeatureLayer(daily_layer_url, gis=gis)
                    q = daily_layer.query(where="1=1", out_fields="DateScan", order_by_fields="DateScan ASC", result_record_count=1)
                    if q.features and q.features[0].attributes.get("DateScan"):
                        raw_date_val = q.features[0].attributes.get("DateScan")
                        if isinstance(raw_date_val, (int, float)):
                            earliest_dt = datetime.fromtimestamp(raw_date_val / 1000.0).astimezone()
                            earliest_midnight = earliest_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                            earliest_ms = int(earliest_midnight.timestamp() * 1000)
                except Exception as ex:
                    print(f"Could not query earliest date from daily layer, using today: {ex}")

            item = gis.content.get(long_map_id)
            if item:
                data = item.get_data()
                data["widgets"] = data.get("widgets", {})
                data["widgets"]["timeSlider"] = {
                    "properties": {
                        "startTime": earliest_ms,
                        "endTime": end_ms_today,
                        "currentTimeExtent": [earliest_ms, earliest_ms],
                        "thumbCount": 1,
                        "thumbMovingRate": 2000,
                        "timeStopInterval": {
                            "interval": 1,
                            "units": "esriTimeUnitsDays"
                        }
                    }
                }
                item.update(data=data)
                print(f"Successfully updated Timeline on Long Term Web Map ({long_map_id}) from earliest day to today.")
        except Exception as e:
            print(f"Error updating Long Term Web Map timeline: {str(e)}")


# Register Jobs with APScheduler
# 1. 5-Minute History (Runs every 5 minutes)
scheduler.add_job(push_5min_history, 'interval', minutes=5)

# 2. Daily History (Runs at 11:50 PM every day, just before wipe)
scheduler.add_job(push_daily_history, 'cron', hour=23, minute=50)

# 3. Wipe 5-Minute History & Update Web Map Timelines (Runs at Midnight every day)
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
    Updates the local SQLite cache AND synchronously updates the Layer 1 ArcGIS server.
    """
    target_webmap_url = os.getenv("TARGET_WEB_MAP_URL")
    
    # Synchronously Update Layer 1 (Current Location)
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
        
        # Validate that this is actually a Feature Layer
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
                    detail=f"Field '{field_name}' in ArcGIS is a number, but received non-numeric ID '{update_req.asset_id}'. Please scan/pass a real number (e.g., ?id=1)."
                )
            where_clause = f"{field_name} = {update_req.asset_id}"
        else:
            where_clause = f"{field_name} = '{update_req.asset_id}'"

        # Query the specific asset by its AssetID for Layer 1
        query_result = layer.query(where=where_clause)
        
        if not query_result.features:
            raise HTTPException(status_code=404, detail=f"Asset '{update_req.asset_id}' not found in Layer 1.")
            
        feature_to_update = query_result.features[0]
        
        feature_to_update.geometry = {
            "x": update_req.lng,
            "y": update_req.lat,
            "spatialReference": {"wkid": 4326}
        }
        
        update_result = layer.edit_features(updates=[feature_to_update])
        
        if update_result.get('updateResults') and update_result['updateResults'][0].get('success'):
            # Save to local cache only after Layer 1 update succeeds
            database.upsert_asset_location(update_req.asset_id, update_req.lat, update_req.lng)
            print(f"Live upload complete for Asset {update_req.asset_id} to Layer 1.")
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
