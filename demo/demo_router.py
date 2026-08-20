"""
FastAPI router for demo control endpoints and UI.
"""

import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import database
from demo.seeder import (
    wipe_all_layers,
    seed_all_layers,
    reset_all_demo_data,
    trigger_5min_upload,
    trigger_midnight_rollover
)

demo_router = APIRouter(tags=["demo"])

STATIC_DEMO_DIR = os.path.join(os.path.dirname(__file__), "static")


@demo_router.get("/demo")
async def get_demo_dashboard():
    """Serves the interactive demo control panel."""
    html_path = os.path.join(STATIC_DEMO_DIR, "demo.html")
    return FileResponse(html_path)


@demo_router.post("/api/demo/wipe")
async def api_wipe_demo_data():
    """Wipes all 3 ArcGIS layers and clears the local SQLite cache."""
    result = wipe_all_layers()
    return JSONResponse(result)


@demo_router.post("/api/demo/seed")
async def api_seed_demo_data():
    """Populates all 3 ArcGIS layers with the demo datasets."""
    result = seed_all_layers()
    return JSONResponse(result)


@demo_router.post("/api/demo/reset")
async def api_reset_demo_data():
    """Wipes all 3 ArcGIS layers and re-seeds the demo dataset."""
    result = reset_all_demo_data()
    return JSONResponse(result)


@demo_router.post("/api/demo/trigger-5min")
async def api_trigger_5min():
    """Manually triggers the 5-minute snapshot upload to Layer 1."""
    result = trigger_5min_upload()
    return JSONResponse(result)


@demo_router.post("/api/demo/trigger-midnight")
async def api_trigger_midnight():
    """Manually triggers the midnight daily archiving and 5-min layer wipe."""
    result = trigger_midnight_rollover()
    return JSONResponse(result)


@demo_router.get("/api/demo/status")
async def api_demo_status():
    """Returns the current SQLite cache state."""
    locations = database.get_all_locations()
    return JSONResponse({
        "status": "success",
        "locations": locations
    })
