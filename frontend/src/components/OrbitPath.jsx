import React, { useMemo } from 'react';
import { Line } from '@react-three/drei';

const OrbitPath = ({ points, color, opacity = 0.5 }) => {
  const linePoints = useMemo(() => {
    // Convert array of arrays to Vector3 format and close the orbit
    const processedPoints = [...points, points[0]]; // Close the orbit
    return processedPoints;
  }, [points]);

  return (
    <Line
      points={linePoints}
      color={color}
      transparent={true}
      opacity={opacity}
      lineWidth={2}
    />
  );
};

export default OrbitPath;