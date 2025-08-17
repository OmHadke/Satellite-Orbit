import React, { useState, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, Text } from '@react-three/drei';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Play, Pause, RotateCcw, Target, Info, Save, Settings, Plus } from 'lucide-react';
import { calculateOrbitalPosition, generateOrbitPath, validateOrbitalParameters } from '../utils/orbitalCalculations';
import SatelliteAPI from '../services/satelliteApi';
import Earth3D from './Earth3D';
import SatelliteModel from './SatelliteModel';
import OrbitPath from './OrbitPath';
import { useToast } from '../hooks/use-toast';

const SatelliteSimulation = () => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [timeSpeed, setTimeSpeed] = useState(1);
  const [selectedSatellite, setSelectedSatellite] = useState(mockSatellites[0]);
  const [showInfo, setShowInfo] = useState(true);
  const [customParams, setCustomParams] = useState({
    altitude: selectedSatellite?.altitude || 408,
    inclination: selectedSatellite?.inclination || 51.6,
    eccentricity: selectedSatellite?.eccentricity || 0.0002
  });
  const [currentTime, setCurrentTime] = useState(0);
  const [trackingSatellite, setTrackingSatellite] = useState(null);
  
  const { toast } = useToast();
  const animationRef = useRef();

  // Animation loop
  useEffect(() => {
    if (isPlaying) {
      const animate = () => {
        setCurrentTime(prev => prev + timeSpeed);
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, timeSpeed]);

  const handleSatelliteSelect = (satelliteId) => {
    const satellite = mockSatellites.find(s => s.id === satelliteId);
    setSelectedSatellite(satellite);
    setCustomParams({
      altitude: satellite.altitude,
      inclination: satellite.inclination,
      eccentricity: satellite.eccentricity
    });
    toast({
      title: "Satellite Selected",
      description: `Now viewing: ${satellite.name}`,
    });
  };

  const handleTrackSatellite = (satellite) => {
    setTrackingSatellite(satellite);
    toast({
      title: "Tracking Enabled",
      description: `Camera following: ${satellite.name}`,
    });
  };

  const resetSimulation = () => {
    setCurrentTime(0);
    setTrackingSatellite(null);
    toast({
      title: "Simulation Reset",
      description: "Time reset to 0 and tracking disabled",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-2 bg-black/20 backdrop-blur-sm rounded-lg px-6 py-3 inline-block">
            🛰️ Satellite Orbit Simulation
          </h1>
          <p className="text-gray-300 ml-6">Interactive 3D visualization of satellite orbits around Earth</p>
        </div>
      </div>

      {/* 3D Visualization */}
      <div className="h-screen">
        <Canvas camera={{ position: [15, 15, 15], fov: 60 }}>
          <ambientLight intensity={0.6} />
          <pointLight position={[10, 10, 10]} intensity={1.5} />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ffffff" />
          <Stars radius={300} depth={60} count={3000} factor={4} saturation={0} fade speed={1} />
          
          {/* Earth */}
          <Earth3D />
          
          {/* Satellites and their orbits */}
          {mockSatellites.map((satellite) => {
            const isSelected = selectedSatellite?.id === satellite.id;
            const position = calculateOrbitalPosition(
              satellite, 
              currentTime, 
              isSelected ? customParams : {}
            );
            const orbitPath = generateOrbitPath(
              satellite, 
              isSelected ? customParams : {}
            );
            
            return (
              <group key={satellite.id}>
                <OrbitPath 
                  points={orbitPath} 
                  color={satellite.color}
                  opacity={isSelected ? 0.8 : 0.3}
                />
                <SatelliteModel
                  position={[position.x, position.y, position.z]}
                  color={satellite.color}
                  name={satellite.name}
                  isSelected={isSelected}
                  onClick={() => handleSatelliteSelect(satellite.id)}
                />
              </group>
            );
          })}
          
          <OrbitControls 
            enablePan={true} 
            enableZoom={true} 
            enableRotate={true}
            target={trackingSatellite ? 
              calculateOrbitalPosition(trackingSatellite, currentTime, 
                trackingSatellite.id === selectedSatellite?.id ? customParams : {}) : 
              [0, 0, 0]
            }
          />
        </Canvas>
      </div>

      {/* Control Panel */}
      <div className="absolute right-6 top-24 w-80 space-y-4 z-20">
        {/* Simulation Controls */}
        <Card className="p-6 bg-black/40 backdrop-blur-md border-gray-600">
          <h3 className="text-xl font-semibold text-white mb-4">Simulation Controls</h3>
          
          <div className="flex items-center space-x-3 mb-4">
            <Button
              onClick={() => setIsPlaying(!isPlaying)}
              variant="outline"
              size="sm"
              className="bg-white/10 border-gray-600 text-white hover:bg-white/20"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            <Button
              onClick={resetSimulation}
              variant="outline"
              size="sm"
              className="bg-white/10 border-gray-600 text-white hover:bg-white/20"
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
            <Badge variant="secondary" className="bg-white/20 text-white">
              {Math.floor(currentTime / 60)}m {Math.floor(currentTime % 60)}s
            </Badge>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-sm text-gray-300 mb-2 block">
                Time Speed: {timeSpeed}x
              </label>
              <Slider
                value={[timeSpeed]}
                onValueChange={(value) => setTimeSpeed(value[0])}
                max={10}
                min={0.1}
                step={0.1}
                className="w-full"
              />
            </div>
          </div>
        </Card>

        {/* Satellite Selection */}
        <Card className="p-6 bg-black/40 backdrop-blur-md border-gray-600">
          <h3 className="text-xl font-semibold text-white mb-4">Satellite Selection</h3>
          
          <Select value={selectedSatellite?.id} onValueChange={handleSatelliteSelect}>
            <SelectTrigger className="w-full bg-white/10 border-gray-600 text-white">
              <SelectValue placeholder="Select a satellite" />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-600">
              {mockSatellites.map((satellite) => (
                <SelectItem 
                  key={satellite.id} 
                  value={satellite.id}
                  className="text-white hover:bg-gray-700"
                >
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: satellite.color }}
                    />
                    <span>{satellite.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            onClick={() => handleTrackSatellite(selectedSatellite)}
            variant="outline"
            size="sm"
            className="w-full mt-3 bg-white/10 border-gray-600 text-white hover:bg-white/20"
          >
            <Target className="w-4 h-4 mr-2" />
            Track Satellite
          </Button>
        </Card>

        {/* Orbital Parameters */}
        <Card className="p-6 bg-black/40 backdrop-blur-md border-gray-600">
          <h3 className="text-xl font-semibold text-white mb-4">Orbital Parameters</h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-300 mb-2 block">
                Altitude: {customParams.altitude} km
              </label>
              <Slider
                value={[customParams.altitude]}
                onValueChange={(value) => setCustomParams(prev => ({ ...prev, altitude: value[0] }))}
                max={35786}
                min={200}
                step={10}
                className="w-full"
              />
            </div>
            
            <div>
              <label className="text-sm text-gray-300 mb-2 block">
                Inclination: {customParams.inclination}°
              </label>
              <Slider
                value={[customParams.inclination]}
                onValueChange={(value) => setCustomParams(prev => ({ ...prev, inclination: value[0] }))}
                max={180}
                min={0}
                step={1}
                className="w-full"
              />
            </div>
            
            <div>
              <label className="text-sm text-gray-300 mb-2 block">
                Eccentricity: {customParams.eccentricity.toFixed(4)}
              </label>
              <Slider
                value={[customParams.eccentricity]}
                onValueChange={(value) => setCustomParams(prev => ({ ...prev, eccentricity: value[0] }))}
                max={0.5}
                min={0}
                step={0.001}
                className="w-full"
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Satellite Info Panel */}
      {showInfo && selectedSatellite && (
        <Card className="absolute left-6 bottom-6 w-80 p-6 bg-black/40 backdrop-blur-md border-gray-600 z-20">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-lg font-semibold text-white">{selectedSatellite.name}</h3>
            <Button
              onClick={() => setShowInfo(false)}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              ✕
            </Button>
          </div>
          
          <Badge className="mb-3" style={{ backgroundColor: selectedSatellite.color }}>
            {selectedSatellite.type}
          </Badge>
          
          <p className="text-gray-300 text-sm mb-3">{selectedSatellite.description}</p>
          
          <div className="space-y-1 text-sm text-gray-300">
            <div>Altitude: {selectedSatellite.altitude} km</div>
            <div>Period: {selectedSatellite.period} minutes</div>
            <div>Inclination: {selectedSatellite.inclination}°</div>
          </div>
        </Card>
      )}

      {!showInfo && (
        <Button
          onClick={() => setShowInfo(true)}
          className="absolute left-6 bottom-6 bg-blue-600 hover:bg-blue-700 z-20"
        >
          <Info className="w-4 h-4 mr-2" />
          Show Info
        </Button>
      )}
    </div>
  );
};

export default SatelliteSimulation;