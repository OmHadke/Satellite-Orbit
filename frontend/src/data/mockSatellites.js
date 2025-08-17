// Mock satellite data with orbital parameters
export const mockSatellites = [
  {
    id: 'iss',
    name: 'International Space Station (ISS)',
    type: 'Space Station',
    altitude: 408, // km above Earth
    inclination: 51.6, // degrees
    eccentricity: 0.0002,
    period: 92.68, // minutes
    color: '#00ff88',
    description: 'The largest artificial object in space and the third brightest object in the sky',
    active: true
  },
  {
    id: 'hubble',
    name: 'Hubble Space Telescope',
    type: 'Observatory',
    altitude: 547,
    inclination: 28.5,
    eccentricity: 0.0003,
    period: 95.42,
    color: '#ff6b35',
    description: 'Space telescope that has revolutionized astronomy since 1990',
    active: true
  },
  {
    id: 'gps-1',
    name: 'GPS Satellite Block IIF-1',
    type: 'Navigation',
    altitude: 20200,
    inclination: 55.0,
    eccentricity: 0.02,
    period: 718.97,
    color: '#4f9eff',
    description: 'Global Positioning System satellite for navigation',
    active: true
  },
  {
    id: 'gps-2',
    name: 'GPS Satellite Block IIF-2',
    type: 'Navigation',
    altitude: 20200,
    inclination: 55.0,
    eccentricity: 0.018,
    period: 718.97,
    color: '#4f9eff',
    description: 'Global Positioning System satellite for navigation',
    active: true
  },
  {
    id: 'gps-3',
    name: 'GPS Satellite Block IIF-3',
    type: 'Navigation',
    altitude: 20200,
    inclination: 55.0,
    eccentricity: 0.021,
    period: 718.97,
    color: '#4f9eff',
    description: 'Global Positioning System satellite for navigation',
    active: true
  },
  {
    id: 'landsat8',
    name: 'Landsat 8',
    type: 'Earth Observation',
    altitude: 705,
    inclination: 98.2,
    eccentricity: 0.0001,
    period: 99.2,
    color: '#ff4081',
    description: 'Earth observation satellite for land imaging',
    active: true
  }
];

// Orbital mechanics calculations
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