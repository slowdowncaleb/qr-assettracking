"""
Demo data definitions, landmark coordinates, and journey generators.
Preserves exact asset names: Saguaro, Joshua Tree, Ocotillo, Agave, Cliffrose,
Gila Monster, Roadrunner, Sonoran Pronghorn, Desert Tortoise, Javelina.
"""

from datetime import datetime, timedelta

# 10 Assets with their official names and initial cities (all outside Phoenix)
LIVE_DEMO_ASSETS = [
    {"AssetID": 0, "Name": "Saguaro", "city": "Los Angeles, CA", "lat": 34.0522, "lng": -118.2437},
    {"AssetID": 1, "Name": "Joshua Tree", "city": "San Diego, CA", "lat": 32.7157, "lng": -117.1611},
    {"AssetID": 2, "Name": "Ocotillo", "city": "Las Vegas, NV", "lat": 36.1699, "lng": -115.1398},
    {"AssetID": 3, "Name": "Agave", "city": "Salt Lake City, UT", "lat": 40.7608, "lng": -111.8910},
    {"AssetID": 4, "Name": "Cliffrose", "city": "Denver, CO", "lat": 39.7392, "lng": -104.9903},
    {"AssetID": 5, "Name": "Gila Monster", "city": "Albuquerque, NM", "lat": 35.0844, "lng": -106.6504},
    {"AssetID": 6, "Name": "Roadrunner", "city": "Dallas, TX", "lat": 32.7767, "lng": -96.7970},
    {"AssetID": 7, "Name": "Sonoran Pronghorn", "city": "Seattle, WA", "lat": 47.6062, "lng": -122.3321},
    {"AssetID": 8, "Name": "Desert Tortoise", "city": "Chicago, IL", "lat": 41.8781, "lng": -87.6298},
    {"AssetID": 9, "Name": "Javelina", "city": "New York, NY", "lat": 40.7128, "lng": -74.0060},
]

# ASU Tempe Campus Landmarks for 5-Minute short-term history trail
ASU_LANDMARKS = [
    {"name": "Sun Devil Stadium", "lat": 33.42644, "lng": -111.93255},
    {"name": "Desert Financial Arena", "lat": 33.42485, "lng": -111.93150},
    {"name": "Novus Innovation Corridor", "lat": 33.42295, "lng": -111.92810},
    {"name": "Student Rec Complex", "lat": 33.41920, "lng": -111.93150},
    {"name": "Palm Walk & University", "lat": 33.42080, "lng": -111.93360},
    {"name": "Old Main", "lat": 33.42165, "lng": -111.93430},
    {"name": "A Mountain / Hayden Butte", "lat": 33.42850, "lng": -111.93600},
    {"name": "ASU Fulton Center", "lat": 33.42420, "lng": -111.94020},
    {"name": "Hayden Library", "lat": 33.41905, "lng": -111.93485},
    {"name": "Memorial Union", "lat": 33.41785, "lng": -111.93470},
    {"name": "ASU Gammage Auditorium", "lat": 33.41580, "lng": -111.93685},
    {"name": "Music Building", "lat": 33.41700, "lng": -111.93620},
    {"name": "Palo Verde Main", "lat": 33.42400, "lng": -111.93300},
]

# 30-Day City Itineraries for Long-Term Daily History
# Asset 0: Western & Mountain Tour
ASSET_0_MONTH_CITIES = [
    {"city": "Seattle, WA", "lat": 47.6062, "lng": -122.3321},
    {"city": "Tacoma, WA", "lat": 47.2529, "lng": -122.4443},
    {"city": "Portland, OR", "lat": 45.5152, "lng": -122.6784},
    {"city": "Salem, OR", "lat": 44.9429, "lng": -123.0351},
    {"city": "Eugene, OR", "lat": 44.0521, "lng": -123.0868},
    {"city": "Medford, OR", "lat": 42.3265, "lng": -122.8756},
    {"city": "Redding, CA", "lat": 40.5865, "lng": -122.3917},
    {"city": "Sacramento, CA", "lat": 38.5816, "lng": -121.4944},
    {"city": "San Francisco, CA", "lat": 37.7749, "lng": -122.4194},
    {"city": "San Jose, CA", "lat": 37.3382, "lng": -121.8863},
    {"city": "Monterey, CA", "lat": 36.6002, "lng": -121.8947},
    {"city": "San Luis Obispo, CA", "lat": 35.2828, "lng": -120.6596},
    {"city": "Santa Barbara, CA", "lat": 34.4208, "lng": -119.6982},
    {"city": "Los Angeles, CA", "lat": 34.0522, "lng": -118.2437},
    {"city": "San Diego, CA", "lat": 32.7157, "lng": -117.1611},
    {"city": "Palm Springs, CA", "lat": 33.8303, "lng": -116.5453},
    {"city": "Las Vegas, NV", "lat": 36.1699, "lng": -115.1398},
    {"city": "St. George, UT", "lat": 37.0965, "lng": -113.5684},
    {"city": "Cedar City, UT", "lat": 37.6775, "lng": -113.0619},
    {"city": "Provo, UT", "lat": 40.2338, "lng": -111.6585},
    {"city": "Salt Lake City, UT", "lat": 40.7608, "lng": -111.8910},
    {"city": "Park City, UT", "lat": 40.6461, "lng": -111.4980},
    {"city": "Moab, UT", "lat": 38.5733, "lng": -109.5498},
    {"city": "Grand Junction, CO", "lat": 39.0639, "lng": -108.5506},
    {"city": "Glenwood Springs, CO", "lat": 39.5505, "lng": -107.3248},
    {"city": "Vail, CO", "lat": 39.6403, "lng": -106.3742},
    {"city": "Denver, CO", "lat": 39.7392, "lng": -104.9903},
    {"city": "Colorado Springs, CO", "lat": 38.8339, "lng": -104.8214},
    {"city": "Santa Fe, NM", "lat": 35.6870, "lng": -105.9378},
    {"city": "Albuquerque, NM", "lat": 35.0844, "lng": -106.6504},
]

# Asset 1: Eastern & Sunbelt Tour
ASSET_1_MONTH_CITIES = [
    {"city": "Boston, MA", "lat": 42.3601, "lng": -71.0589},
    {"city": "Providence, RI", "lat": 41.8240, "lng": -71.4128},
    {"city": "New Haven, CT", "lat": 41.3083, "lng": -72.9279},
    {"city": "New York, NY", "lat": 40.7128, "lng": -74.0060},
    {"city": "Philadelphia, PA", "lat": 39.9526, "lng": -75.1652},
    {"city": "Wilmington, DE", "lat": 39.7447, "lng": -75.5484},
    {"city": "Baltimore, MD", "lat": 39.2904, "lng": -76.6122},
    {"city": "Washington, DC", "lat": 38.9072, "lng": -77.0369},
    {"city": "Richmond, VA", "lat": 37.5407, "lng": -77.4360},
    {"city": "Raleigh, NC", "lat": 35.7796, "lng": -78.6382},
    {"city": "Charlotte, NC", "lat": 35.2271, "lng": -80.8431},
    {"city": "Columbia, SC", "lat": 34.0007, "lng": -81.0348},
    {"city": "Charleston, SC", "lat": 32.7765, "lng": -79.9311},
    {"city": "Savannah, GA", "lat": 32.0809, "lng": -81.0912},
    {"city": "Jacksonville, FL", "lat": 30.3322, "lng": -81.6557},
    {"city": "Orlando, FL", "lat": 28.5383, "lng": -81.3792},
    {"city": "Tampa, FL", "lat": 27.9506, "lng": -82.4572},
    {"city": "Miami, FL", "lat": 25.7617, "lng": -80.1918},
    {"city": "Tallahassee, FL", "lat": 30.4383, "lng": -84.2807},
    {"city": "Mobile, AL", "lat": 30.6954, "lng": -88.0399},
    {"city": "New Orleans, LA", "lat": 29.9511, "lng": -90.0715},
    {"city": "Baton Rouge, LA", "lat": 30.4515, "lng": -91.1871},
    {"city": "Lafayette, LA", "lat": 30.2241, "lng": -92.0198},
    {"city": "Houston, TX", "lat": 29.7604, "lng": -95.3698},
    {"city": "San Antonio, TX", "lat": 29.4241, "lng": -98.4936},
    {"city": "Austin, TX", "lat": 30.2672, "lng": -97.7431},
    {"city": "Waco, TX", "lat": 31.5493, "lng": -97.1467},
    {"city": "Fort Worth, TX", "lat": 32.7555, "lng": -97.3308},
    {"city": "Dallas, TX", "lat": 32.7767, "lng": -96.7970},
    {"city": "El Paso, TX", "lat": 31.7619, "lng": -106.4850},
]


def generate_short_term_asu_points(asset_id: int = 0) -> list:
    """
    Generates a full 24-hour day of 5-minute increments (288 points)
    for the current day, tracing an asset around ASU Tempe campus landmarks.
    """
    now = datetime.now().astimezone()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    points = []
    num_landmarks = len(ASU_LANDMARKS)
    total_steps = 288  # 24 hours * 12 (5-min intervals per hour)
    
    for step in range(total_steps):
        time_step = today_midnight + timedelta(minutes=step * 5)
        epoch_ms = int(time_step.timestamp() * 1000)
        
        # Calculate smooth position between landmarks
        progress = (step / total_steps) * (num_landmarks - 1)
        idx = int(progress)
        frac = progress - idx
        
        lm_current = ASU_LANDMARKS[idx]
        lm_next = ASU_LANDMARKS[min(idx + 1, num_landmarks - 1)]
        
        lat = lm_current["lat"] + (lm_next["lat"] - lm_current["lat"]) * frac
        lng = lm_current["lng"] + (lm_next["lng"] - lm_current["lng"]) * frac
        
        points.append({
            "asset_id": asset_id,
            "time_ms": epoch_ms,
            "lat": round(lat, 6),
            "lng": round(lng, 6)
        })
        
    return points


def generate_long_term_daily_points() -> list:
    """
    Generates 30 days of daily increments leading up to today
    for 2 assets (Asset 0 'Saguaro' and Asset 1 'Joshua Tree') moving across the country.
    """
    now = datetime.now().astimezone()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    points = []
    num_days = 30
    
    for day_idx in range(num_days):
        # Days leading up to today (day_idx 0 = 29 days ago, day_idx 29 = today)
        day_date = today_midnight - timedelta(days=(num_days - 1 - day_idx))
        epoch_ms = int(day_date.timestamp() * 1000)
        
        # Asset 0 point
        c0 = ASSET_0_MONTH_CITIES[day_idx % len(ASSET_0_MONTH_CITIES)]
        points.append({
            "asset_id": 0,
            "date_ms": epoch_ms,
            "lat": c0["lat"],
            "lng": c0["lng"],
            "city": c0["city"]
        })
        
        # Asset 1 point
        c1 = ASSET_1_MONTH_CITIES[day_idx % len(ASSET_1_MONTH_CITIES)]
        points.append({
            "asset_id": 1,
            "date_ms": epoch_ms,
            "lat": c1["lat"],
            "lng": c1["lng"],
            "city": c1["city"]
        })
        
    return points
