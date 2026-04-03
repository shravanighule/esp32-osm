from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "geodb")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "locations")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]


# Response Model
class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    message: str
    saved_id: str


# Startup event
@app.on_event("startup")
async def startup_db():
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_db():
    client.close()


# -------------------------------
# ✅ GET: Save location (lat, lon separately)
# -------------------------------
@app.get("/location", response_model=LocationResponse)
async def get_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    doc = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": datetime.now(timezone.utc),
    }

    result = await collection.insert_one(doc)

    return LocationResponse(
        latitude=lat,
        longitude=lon,
        message=f"Location ({lat}, {lon}) saved",
        saved_id=str(result.inserted_id),
    )


# -------------------------------
# ✅ POST: Save location from string "lat,lon"
# -------------------------------
@app.post("/location_from_string", response_model=LocationResponse)
async def location_from_string(
    loc: str = Query(..., description="Format: lat,lon (e.g. 18.52,73.85)")
):
    try:
        lat_str, lon_str = loc.split(",")

        lat = float(lat_str.strip())
        lon = float(lon_str.strip())

        if not (-90 <= lat <= 90):
            raise ValueError("Latitude out of range")
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude out of range")

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use: lat,lon (e.g. 18.52,73.85)"
        )

    doc = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": datetime.now(timezone.utc),
    }

    result = await collection.insert_one(doc)

    return LocationResponse(
        latitude=lat,
        longitude=lon,
        message=f"Location ({lat}, {lon}) saved from string",
        saved_id=str(result.inserted_id),
    )
