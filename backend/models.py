from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Satellite Models
class SatelliteBase(BaseModel):
    name: str
    type: str
    altitude: float  # km above Earth
    inclination: float  # degrees
    eccentricity: float
    color: str = "#00ff88"
    description: str = ""
    active: bool = True

class SatelliteCreate(SatelliteBase):
    pass

class SatelliteUpdate(BaseModel):
    altitude: Optional[float] = None
    inclination: Optional[float] = None
    eccentricity: Optional[float] = None
    active: Optional[bool] = None
    color: Optional[str] = None

class Satellite(SatelliteBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period: float  # calculated field in minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    def calculate_period(self):
        """Calculate orbital period based on altitude"""
        earth_radius = 6371  # km
        mu = 398600.4418  # Earth's gravitational parameter (km³/s²)
        semi_major_axis = earth_radius + self.altitude
        period_seconds = 2 * 3.14159 * ((semi_major_axis ** 3 / mu) ** 0.5)
        self.period = period_seconds / 60  # convert to minutes
        return self.period

# Configuration Models
class ConfigurationCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    satellite_params: Dict[str, Any]
    time_speed: float = 1.0
    selected_satellite_id: str

class Configuration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    satellite_params: Dict[str, Any]
    time_speed: float
    selected_satellite_id: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)

# Position Models
class Position(BaseModel):
    x: float
    y: float
    z: float

class Velocity(BaseModel):
    x: float
    y: float
    z: float

class SatellitePosition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    satellite_id: str
    timestamp: datetime
    position: Position
    velocity: Optional[Velocity] = None
    altitude: float

# Preferences Models
class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    default_speed: Optional[float] = None
    show_orbits: Optional[bool] = None
    camera_mode: Optional[str] = None

class Preferences(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    theme: str = "dark"
    default_speed: float = 1.0
    show_orbits: bool = True
    camera_mode: str = "free"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Response Models
class SatelliteListResponse(BaseModel):
    satellites: List[Satellite]

class ConfigurationListResponse(BaseModel):
    configurations: List[Configuration]

class PositionListResponse(BaseModel):
    positions: List[SatellitePosition]