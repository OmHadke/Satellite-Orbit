import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from starlette.middleware.cors import CORSMiddleware

# Import models and services
from models import (
    Satellite, SatelliteCreate, SatelliteUpdate, SatelliteListResponse,
    Configuration, ConfigurationCreate, ConfigurationListResponse,
    SatellitePosition, PositionListResponse,
    Preferences, PreferencesUpdate
)
from satellite_service import SatelliteService
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import get_current_user, require_roles
from config import get_settings
from metrics import metrics_middleware, metrics_response
from telemetry import configure_telemetry

settings = get_settings()

# MongoDB connection
client = AsyncIOMotorClient(
    settings.mongo_url,
    serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
)
db = client[settings.db_name]

# Create the main app
app = FastAPI(title="Satellite Orbit Simulation API")
configure_telemetry(app)
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
if settings.metrics_enabled:
    app.middleware("http")(metrics_middleware)

#HEALTH
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/live")
def health_live():
    return {"status": "alive", "timestamp": datetime.utcnow()}


@app.get("/health/ready")
@limiter.limit(settings.rate_limit_default)
async def health_ready(request: Request):
    try:
        await db.command("ping")
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready", "timestamp": datetime.utcnow()}


@app.get("/metrics")
def metrics():
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return metrics_response()


# Create API router
api_router = APIRouter(prefix="/api")

# Initialize satellite service
satellite_service = SatelliteService()

# Satellite endpoints
@api_router.get("/satellites", response_model=SatelliteListResponse)
@limiter.limit(settings.rate_limit_default)
async def get_satellites(
    request: Request,
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size)
):
    """Get all satellites"""
    try:
        # Try to get from database first
        satellites_cursor = db.satellites.find().limit(limit)
        satellites_data = await satellites_cursor.to_list(limit)
        
        # If no satellites in DB, initialize with defaults
        if not satellites_data:
            default_satellites = satellite_service.get_default_satellites()
            for sat_data in default_satellites:
                satellite = Satellite(**sat_data)
                satellite.calculate_period()
                await db.satellites.insert_one(satellite.dict())
            
            # Fetch again after initialization
            satellites_cursor = db.satellites.find().limit(limit)
            satellites_data = await satellites_cursor.to_list(limit)
        
        satellites = [Satellite(**sat_data) for sat_data in satellites_data]
        return SatelliteListResponse(satellites=satellites)
        
    except Exception as e:
        logging.error(f"Error fetching satellites: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch satellites")

@api_router.get("/satellites/{satellite_id}")
@limiter.limit(settings.rate_limit_default)
async def get_satellite(request: Request, satellite_id: str):
    """Get specific satellite by ID"""
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    satellite = Satellite(**satellite_data)
    return {"satellite": satellite}

@api_router.post(
    "/satellites/custom",
    dependencies=[Depends(require_roles(settings.jwt_required_roles))],
)
@limiter.limit(settings.rate_limit_auth)
async def create_custom_satellite(request: Request, satellite_data: SatelliteCreate):
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

@api_router.put(
    "/satellites/{satellite_id}",
    dependencies=[Depends(require_roles(settings.jwt_required_roles))],
)
@limiter.limit(settings.rate_limit_auth)
async def update_satellite(
    request: Request, satellite_id: str, updates: SatelliteUpdate
):
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
@limiter.limit(settings.rate_limit_default)
async def get_configurations(request: Request):
    """Get all saved configurations"""
    configs_cursor = db.configurations.find().sort("saved_at", -1).limit(
        settings.default_page_size
    )
    configs_data = await configs_cursor.to_list(settings.default_page_size)
    configurations = [Configuration(**config_data) for config_data in configs_data]
    return ConfigurationListResponse(configurations=configurations)

@api_router.post(
    "/configurations", dependencies=[Depends(require_roles(settings.jwt_required_roles))]
)
@limiter.limit(settings.rate_limit_auth)
async def save_configuration(request: Request, config_data: ConfigurationCreate):
    """Save current simulation configuration"""
    configuration = Configuration(**config_data.dict())
    await db.configurations.insert_one(configuration.dict())
    return {"configuration": configuration, "id": configuration.id}

@api_router.delete(
    "/configurations/{config_id}",
    dependencies=[Depends(require_roles(settings.jwt_required_roles))],
)
@limiter.limit(settings.rate_limit_auth)
async def delete_configuration(request: Request, config_id: str):
    """Delete a saved configuration"""
    result = await db.configurations.delete_one({"id": config_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"success": True}

# Position tracking endpoints
@api_router.get("/satellites/{satellite_id}/positions")
@limiter.limit(settings.rate_limit_default)
async def get_satellite_positions(
    request: Request,
    satellite_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size)
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

@api_router.post(
    "/satellites/{satellite_id}/track",
    dependencies=[Depends(require_roles(settings.jwt_required_roles))],
)
@limiter.limit(settings.rate_limit_auth)
async def start_tracking_satellite(request: Request, satellite_id: str):
    """Start tracking satellite positions"""
    # Verify satellite exists
    satellite_data = await db.satellites.find_one({"id": satellite_id})
    if not satellite_data:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    # For now, just return success - real tracking would be a background task
    return {"tracking": True, "satellite_id": satellite_id}

# Preferences endpoints
@api_router.get("/preferences")
@limiter.limit(settings.rate_limit_default)
async def get_preferences(request: Request):
    """Get user preferences"""
    prefs_data = await db.preferences.find_one() or {}
    preferences = Preferences(**prefs_data) if prefs_data else Preferences()
    return {"preferences": preferences}

@api_router.put(
    "/preferences", dependencies=[Depends(require_roles(settings.jwt_required_roles))]
)
@limiter.limit(settings.rate_limit_auth)
async def update_preferences(request: Request, updates: PreferencesUpdate):
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
@limiter.limit(settings.rate_limit_default)
async def get_orbit_path(request: Request, satellite_id: str, points: int = 100):
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
@limiter.limit(settings.rate_limit_default)
async def validate_orbital_params(
    request: Request, altitude: float, inclination: float, eccentricity: float
):
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
cors_allow_origins = settings.allowed_origins or ["*"]
cors_allow_credentials = settings.allow_credentials
if "*" in cors_allow_origins and cors_allow_credentials:
    logging.warning(
        "CORS allow_credentials is incompatible with wildcard origins; disabling credentials."
    )
    cors_allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_credentials=cors_allow_credentials,
    allow_origins=cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    try:
        await db.command("ping")
        logger.info("Connected to MongoDB")
    except PyMongoError as exc:
        logger.error("Failed to connect to MongoDB", exc_info=exc)
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
