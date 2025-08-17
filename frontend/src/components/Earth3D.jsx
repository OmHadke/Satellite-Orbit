import React, { useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { TextureLoader } from 'three';

const Earth3D = () => {
  const earthRef = useRef();

  // Create a simple blue-green Earth material without external textures
  const earthMaterial = {
    color: '#2563eb',
    transparent: false,
    opacity: 1
  };

  // Rotate Earth slowly
  useFrame(() => {
    if (earthRef.current) {
      earthRef.current.rotation.y += 0.002;
    }
  });

  return (
    <group>
      {/* Earth Sphere */}
      <mesh ref={earthRef} position={[0, 0, 0]}>
        <sphereGeometry args={[5, 64, 64]} />
        <meshLambertMaterial {...earthMaterial} />
      </mesh>
      
      {/* Atmosphere effect */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[5.1, 32, 32]} />
        <meshLambertMaterial 
          color="#87ceeb" 
          transparent={true} 
          opacity={0.1}
        />
      </mesh>

      {/* Simple continent outlines using wireframe */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[5.01, 16, 16]} />
        <meshBasicMaterial 
          color="#2d5a27" 
          wireframe={true}
          transparent={true}
          opacity={0.3}
        />
      </mesh>
    </group>
  );
};

export default Earth3D;