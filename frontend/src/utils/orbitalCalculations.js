// Orbital mechanics calculations for frontend
export const calculateOrbitalPosition = (satellite, time, customParams = {}) => {
  const params = { ...satellite, ...customParams };
  const earthRadius = 6371; // km
  const totalRadius = earthRadius + params.altitude;
  
  // Convert period from minutes to seconds for calculation
  const periodSeconds = params.period * 60;
  
  // Calculate mean motion (radians per second)
  const meanMotion = (2 * Math.PI) / periodSeconds;
  
  // Mean anomaly (simplified)
  const meanAnomaly = (meanMotion * time) % (2 * Math.PI);
  
  // For simplicity, assume circular orbit (eccentricity effects minimal for display)
  const trueAnomaly = meanAnomaly;
  
  // Calculate position in orbital plane
  const x = totalRadius * Math.cos(trueAnomaly);
  const y = totalRadius * Math.sin(trueAnomaly);
  
  // Apply inclination (rotate around x-axis)
  const inclinationRad = (params.inclination * Math.PI) / 180;
  const z = y * Math.sin(inclinationRad);
  const yInclined = y * Math.cos(inclinationRad);
  
  // Scale down for Three.js scene (Earth radius = 5 units)
  const scale = 5 / earthRadius;
  
  return {
    x: x * scale,
    y: yInclined * scale,
    z: z * scale
  };
};

// Generate orbit path points
export const generateOrbitPath = (satellite, customParams = {}, points = 100) => {
  const pathPoints = [];
  const timeStep = (satellite.period * 60) / points; // Full orbit in seconds
  
  for (let i = 0; i < points; i++) {
    const time = i * timeStep;
    const position = calculateOrbitalPosition(satellite, time, customParams);
    pathPoints.push([position.x, position.y, position.z]);
  }
  
  return pathPoints;
};

// Calculate orbital period based on altitude
export const calculateOrbitalPeriod = (altitude) => {
  const earthRadius = 6371; // km
  const mu = 398600.4418; // Earth's gravitational parameter (km³/s²)
  const semiMajorAxis = earthRadius + altitude;
  const periodSeconds = 2 * Math.PI * Math.sqrt((semiMajorAxis ** 3) / mu);
  return periodSeconds / 60; // convert to minutes
};

// Validate orbital parameters
export const validateOrbitalParameters = (altitude, inclination, eccentricity) => {
  const errors = [];
  
  // Altitude validation
  if (altitude < 150) {
    errors.push("Altitude must be above 150km (atmospheric drag)");
  } else if (altitude > 35786) {
    errors.push("Altitude above 35,786km not supported in this simulation");
  }
  
  // Inclination validation  
  if (inclination < 0 || inclination > 180) {
    errors.push("Inclination must be between 0° and 180°");
  }
  
  // Eccentricity validation
  if (eccentricity < 0 || eccentricity >= 1) {
    errors.push("Eccentricity must be between 0 and 1 (elliptical orbit)");
  }
  
  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: []
  };
};