from fastapi import FastAPI, Query
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


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    message: str
    saved_id: str


@app.on_event("startup")
async def startup_db():
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_db():
    client.close()


@app.get("/location", response_model=LocationResponse)
async def get_location(
    lat: float = Query(..., description="Latitude (-90 to 90)", ge=-90, le=90),
    lon: float = Query(..., description="Longitude (-180 to 180)", ge=-180, le=180),
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
        message=f"Location ({lat}, {lon}) saved to MongoDB",
        saved_id=str(result.inserted_id),
    )
