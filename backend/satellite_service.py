import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models import Satellite, SatellitePosition, Position, Velocity

class SatelliteService:
    
    @staticmethod
    def calculate_orbital_position(satellite: Satellite, time_seconds: float, custom_params: Optional[Dict] = None) -> Position:
        """Calculate satellite position using orbital mechanics"""
        params = satellite.dict()
        if custom_params:
            params.update(custom_params)
        
        earth_radius = 6371  # km
        total_radius = earth_radius + params['altitude']
        
        # Convert period from minutes to seconds
        period_seconds = params.get('period', satellite.period) * 60
        
        # Calculate mean motion (radians per second)
        mean_motion = (2 * math.pi) / period_seconds
        
        # Mean anomaly
        mean_anomaly = (mean_motion * time_seconds) % (2 * math.pi)
        
        # For simplicity, assume circular orbit (eccentricity effects minimal)
        true_anomaly = mean_anomaly + (2 * params['eccentricity'] * math.sin(mean_anomaly))
        
        # Position in orbital plane
        x = total_radius * math.cos(true_anomaly)
        y = total_radius * math.sin(true_anomaly)
        
        # Apply inclination (rotate around x-axis)
        inclination_rad = math.radians(params['inclination'])
        z = y * math.sin(inclination_rad)
        y_inclined = y * math.cos(inclination_rad)
        
        # Scale for Three.js scene (Earth radius = 5 units)
        scale = 5 / earth_radius
        
        return Position(
            x=x * scale,
            y=y_inclined * scale,
            z=z * scale
        )
    
    @staticmethod
    def calculate_velocity(satellite: Satellite, time_seconds: float, custom_params: Optional[Dict] = None) -> Velocity:
        """Calculate satellite velocity vector"""
        params = satellite.dict()
        if custom_params:
            params.update(custom_params)
            
        earth_radius = 6371
        total_radius = earth_radius + params['altitude']
        
        # Simplified circular orbit velocity
        mu = 398600.4418  # Earth's gravitational parameter
        orbital_speed = math.sqrt(mu / total_radius)  # km/s
        
        # Convert to scene coordinates
        scale = 5 / earth_radius
        
        period_seconds = params.get('period', satellite.period) * 60
        angular_velocity = (2 * math.pi) / period_seconds
        
        # Calculate velocity components (simplified)
        angle = (angular_velocity * time_seconds) % (2 * math.pi)
        
        return Velocity(
            x=-orbital_speed * math.sin(angle) * scale,
            y=orbital_speed * math.cos(angle) * scale,
            z=0
        )
    
    @staticmethod
    def generate_orbit_path(satellite: Satellite, custom_params: Optional[Dict] = None, points: int = 100) -> List[Position]:
        """Generate orbit path points"""
        params = satellite.dict()
        if custom_params:
            params.update(custom_params)
            
        path_points = []
        period_seconds = params.get('period', satellite.period) * 60
        time_step = period_seconds / points
        
        for i in range(points):
            time = i * time_step
            position = SatelliteService.calculate_orbital_position(satellite, time, custom_params)
            path_points.append(position)
        
        return path_points
    
    @staticmethod
    def validate_orbital_parameters(altitude: float, inclination: float, eccentricity: float) -> Dict[str, Any]:
        """Validate orbital parameters"""
        errors = []
        
        # Altitude validation
        if altitude < 150:  # Below atmosphere
            errors.append("Altitude must be above 150km (atmospheric drag)")
        elif altitude > 35786:  # Above geostationary
            errors.append("Altitude above 35,786km not supported in this simulation")
        
        # Inclination validation  
        if not (0 <= inclination <= 180):
            errors.append("Inclination must be between 0° and 180°")
        
        # Eccentricity validation
        if not (0 <= eccentricity < 1):
            errors.append("Eccentricity must be between 0 and 1 (elliptical orbit)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    
    @staticmethod
    def get_default_satellites() -> List[Dict]:
        """Get predefined satellite configurations"""
        return [
            {
                "id": "iss",
                "name": "International Space Station (ISS)",
                "type": "Space Station",
                "altitude": 408,
                "inclination": 51.6,
                "eccentricity": 0.0002,
                "color": "#00ff88",
                "description": "The largest artificial object in space and the third brightest object in the sky",
                "active": True
            },
            {
                "id": "hubble",
                "name": "Hubble Space Telescope",
                "type": "Observatory",
                "altitude": 547,
                "inclination": 28.5,
                "eccentricity": 0.0003,
                "color": "#ff6b35",
                "description": "Space telescope that has revolutionized astronomy since 1990",
                "active": True
            },
            {
                "id": "gps-1",
                "name": "GPS Satellite Block IIF-1",
                "type": "Navigation",
                "altitude": 20200,
                "inclination": 55.0,
                "eccentricity": 0.02,
                "color": "#4f9eff",
                "description": "Global Positioning System satellite for navigation",
                "active": True
            },
            {
                "id": "gps-2", 
                "name": "GPS Satellite Block IIF-2",
                "type": "Navigation",
                "altitude": 20200,
                "inclination": 55.0,
                "eccentricity": 0.018,
                "color": "#4f9eff", 
                "description": "Global Positioning System satellite for navigation",
                "active": True
            },
            {
                "id": "gps-3",
                "name": "GPS Satellite Block IIF-3", 
                "type": "Navigation",
                "altitude": 20200,
                "inclination": 55.0,
                "eccentricity": 0.021,
                "color": "#4f9eff",
                "description": "Global Positioning System satellite for navigation",
                "active": True
            },
            {
                "id": "landsat8",
                "name": "Landsat 8",
                "type": "Earth Observation", 
                "altitude": 705,
                "inclination": 98.2,
                "eccentricity": 0.0001,
                "color": "#ff4081",
                "description": "Earth observation satellite for land imaging",
                "active": True
            }
        ]