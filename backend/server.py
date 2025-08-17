from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

# Import models and services
from models import (
    Satellite, SatelliteCreate, SatelliteUpdate, SatelliteListResponse,
    Configuration, ConfigurationCreate, ConfigurationListResponse,
    SatellitePosition, PositionListResponse,
    Preferences, PreferencesUpdate
)
from satellite_service import SatelliteService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Satellite Orbit Simulation API")

# Create API router
api_router = APIRouter(prefix="/api")

# Initialize satellite service
satellite_service = SatelliteService()

# Satellite endpoints
@api_router.get("/satellites", response_model=SatelliteListResponse)
async def get_satellites():
    """Get all satellites"""
    try:
        # Try to get from database first
        satellites_cursor = db.satellites.find()
        satellites_data = await satellites_cursor.to_list(100)
        
        # If no satellites in DB, initialize with defaults
        if not satellites_data:
            default_satellites = satellite_service.get_default_satellites()
            for sat_data in default_satellites:
                satellite = Satellite(**sat_data)
                satellite.calculate_period()
                await db.satellites.insert_one(satellite.dict())
            
            # Fetch again after initialization
            satellites_cursor = db.satellites.find()
            satellites_data = await satellites_cursor.to_list(100)
        
        satellites = [Satellite(**sat_data) for sat_data in satellites_data]
        return SatelliteListResponse(satellites=satellites)
        
    except Exception as e:
        logging.error(f"Error fetching satellites: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch satellites")

@api_router.get("/satellites/{satellite_id}")
async def get_satellite(satellite_id: str):
    """Get specific satellite by ID"""
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    satellite = Satellite(**satellite_data)
    return {"satellite": satellite}

@api_router.post("/satellites/custom")
async def create_custom_satellite(satellite_data: SatelliteCreate):
    """Create a custom satellite configuration"""
    # Validate orbital parameters
    validation = satellite_service.validate_orbital_parameters(
        satellite_data.altitude,
        satellite_data.inclination, 
        satellite_data.eccentricity
    )
    
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={"errors": validation["errors"]})
    
    # Create satellite object
    satellite = Satellite(**satellite_data.dict())
    satellite.calculate_period()
    
    # Save to database
    await db.satellites.insert_one(satellite.dict())
    
    return {"satellite": satellite, "id": satellite.id}

@api_router.put("/satellites/{satellite_id}")
async def update_satellite(satellite_id: str, updates: SatelliteUpdate):
    """Update satellite parameters"""
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    # Apply updates
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    
    # Validate if orbital parameters are being updated
    if any(key in update_dict for key in ['altitude', 'inclination', 'eccentricity']):
        current_satellite = Satellite(**satellite_data)
        test_altitude = update_dict.get('altitude', current_satellite.altitude)
        test_inclination = update_dict.get('inclination', current_satellite.inclination)
        test_eccentricity = update_dict.get('eccentricity', current_satellite.eccentricity)
        
        validation = satellite_service.validate_orbital_parameters(
            test_altitude, test_inclination, test_eccentricity
        )
        
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={"errors": validation["errors"]})
    
    # Update in database
    await db.satellites.update_one(
        {"id": satellite_id},
        {"$set": update_dict}
    )
    
    # Recalculate period if altitude changed
    if 'altitude' in update_dict:
        updated_data = await db.satellites.find_one({"id": satellite_id})
        satellite = Satellite(**updated_data)
        satellite.calculate_period()
        await db.satellites.update_one(
            {"id": satellite_id},
            {"$set": {"period": satellite.period}}
        )
        return {"satellite": satellite}
    
    # Return updated satellite
    updated_data = await db.satellites.find_one({"id": satellite_id})
    satellite = Satellite(**updated_data)
    return {"satellite": satellite}

# Configuration endpoints
@api_router.get("/configurations", response_model=ConfigurationListResponse)
async def get_configurations():
    """Get all saved configurations"""
    configs_cursor = db.configurations.find().sort("saved_at", -1)
    configs_data = await configs_cursor.to_list(100)
    configurations = [Configuration(**config_data) for config_data in configs_data]
    return ConfigurationListResponse(configurations=configurations)

@api_router.post("/configurations")
async def save_configuration(config_data: ConfigurationCreate):
    """Save current simulation configuration"""
    configuration = Configuration(**config_data.dict())
    await db.configurations.insert_one(configuration.dict())
    return {"configuration": configuration, "id": configuration.id}

@api_router.delete("/configurations/{config_id}")
async def delete_configuration(config_id: str):
    """Delete a saved configuration"""
    result = await db.configurations.delete_one({"id": config_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"success": True}

# Position tracking endpoints
@api_router.get("/satellites/{satellite_id}/positions")
async def get_satellite_positions(
    satellite_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100
):
    """Get historical satellite positions"""
    query = {"satellite_id": satellite_id}
    
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = start
        if end:
            query["timestamp"]["$lte"] = end
    
    positions_cursor = db.positions.find(query).sort("timestamp", -1).limit(limit)
    positions_data = await positions_cursor.to_list(limit)
    positions = [SatellitePosition(**pos_data) for pos_data in positions_data]
    
    return PositionListResponse(positions=positions)

@api_router.post("/satellites/{satellite_id}/track")
async def start_tracking_satellite(satellite_id: str):
    """Start tracking satellite positions"""
    # Verify satellite exists
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    # For now, just return success - real tracking would be a background task
    return {"tracking": True, "satellite_id": satellite_id}

# Preferences endpoints
@api_router.get("/preferences")
async def get_preferences():
    """Get user preferences"""
    prefs_data = await db.preferences.find_one() or {}
    preferences = Preferences(**prefs_data) if prefs_data else Preferences()
    return {"preferences": preferences}

@api_router.put("/preferences")
async def update_preferences(updates: PreferencesUpdate):
    """Update user preferences"""
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Upsert preferences
    result = await db.preferences.update_one(
        {},
        {"$set": update_dict},
        upsert=True
    )
    
    prefs_data = await db.preferences.find_one() or {}
    preferences = Preferences(**prefs_data)
    return {"preferences": preferences}

# Utility endpoints
@api_router.get("/satellites/{satellite_id}/orbit-path")
async def get_orbit_path(satellite_id: str, points: int = 100):
    """Get orbital path for visualization"""
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    satellite = Satellite(**satellite_data)
    path_points = satellite_service.generate_orbit_path(satellite, None, points)
    
    return {
        "satellite_id": satellite_id,
        "points": [{"x": p.x, "y": p.y, "z": p.z} for p in path_points]
    }

@api_router.post("/validate-orbital-params")
async def validate_orbital_params(altitude: float, inclination: float, eccentricity: float):
    """Validate orbital parameters"""
    validation = satellite_service.validate_orbital_parameters(altitude, inclination, eccentricity)
    return validation

# Health check
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()