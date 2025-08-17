import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';

const SatelliteModel = ({ position, color, name, isSelected, onClick }) => {
  const satelliteRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame(() => {
    if (satelliteRef.current) {
      // Gentle rotation animation
      satelliteRef.current.rotation.x += 0.01;
      satelliteRef.current.rotation.y += 0.02;
    }
  });

  const scale = isSelected ? 1.5 : hovered ? 1.2 : 1;

  return (
    <group position={position}>
      {/* Satellite body */}
      <mesh
        ref={satelliteRef}
        scale={[scale, scale, scale]}
        onClick={onClick}
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        <boxGeometry args={[0.3, 0.3, 0.6]} />
        <meshStandardMaterial 
          color={color} 
          metalness={0.8}
          roughness={0.2}
          emissive={color}
          emissiveIntensity={isSelected ? 0.3 : 0.1}
        />
      </mesh>
      
      {/* Solar panels */}
      <mesh position={[-0.4, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <boxGeometry args={[0.8, 0.05, 0.3]} />
        <meshStandardMaterial color="#1a1a1a" metalness={0.9} roughness={0.1} />
      </mesh>
      
      <mesh position={[0.4, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <boxGeometry args={[0.8, 0.05, 0.3]} />
        <meshStandardMaterial color="#1a1a1a" metalness={0.9} roughness={0.1} />
      </mesh>

      {/* Satellite name label */}
      {(isSelected || hovered) && (
        <Text
          position={[0, 0.8, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
          characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?()[]{}.,;:-_/\\@#$%^&*+=<> "
        >
          {name}
        </Text>
      )}

      {/* Selection indicator */}
      {isSelected && (
        <mesh>
          <ringGeometry args={[0.8, 1, 32]} />
          <meshBasicMaterial 
            color={color}
            transparent={true}
            opacity={0.4}
            side={2}
          />
        </mesh>
      )}

      {/* Pulsing effect for tracking */}
      {isSelected && (
        <mesh>
          <sphereGeometry args={[1.2, 8, 6]} />
          <meshBasicMaterial 
            color={color}
            transparent={true}
            opacity={0.1}
            wireframe={true}
          />
        </mesh>
      )}
    </group>
  );
};

export default SatelliteModel;