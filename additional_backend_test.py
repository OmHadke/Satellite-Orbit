#!/usr/bin/env python3
"""
Additional Backend Tests for Satellite Orbital Mechanics and Edge Cases
"""

import requests
import json
import os
import math

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://orbit-explorer-3.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_orbital_mechanics():
    """Test that orbital calculations are mathematically correct"""
    print("🧮 Testing Orbital Mechanics Calculations")
    
    # Create a satellite with known parameters
    test_satellite = {
        "name": "ISS Test Replica",
        "type": "Test",
        "altitude": 408.0,  # ISS altitude
        "inclination": 51.6,  # ISS inclination
        "eccentricity": 0.0002,
        "color": "#00ff88",
        "description": "Test satellite matching ISS parameters"
    }
    
    response = requests.post(f"{API_BASE}/satellites/custom", json=test_satellite, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        satellite = data["satellite"]
        calculated_period = satellite["period"]
        
        # Calculate expected period manually
        earth_radius = 6371  # km
        mu = 398600.4418  # Earth's gravitational parameter (km³/s²)
        semi_major_axis = earth_radius + test_satellite["altitude"]
        expected_period_seconds = 2 * math.pi * ((semi_major_axis ** 3 / mu) ** 0.5)
        expected_period_minutes = expected_period_seconds / 60
        
        # Check if calculated period is close to expected (within 1% tolerance)
        tolerance = 0.01
        if abs(calculated_period - expected_period_minutes) / expected_period_minutes < tolerance:
            print(f"✅ Orbital period calculation correct: {calculated_period:.2f} minutes (expected: {expected_period_minutes:.2f})")
            return True
        else:
            print(f"❌ Orbital period calculation incorrect: {calculated_period:.2f} minutes (expected: {expected_period_minutes:.2f})")
            return False
    else:
        print(f"❌ Failed to create test satellite: {response.status_code}")
        return False

def test_database_persistence():
    """Test that satellites persist in database"""
    print("💾 Testing Database Persistence")
    
    # Get initial satellite count
    response1 = requests.get(f"{API_BASE}/satellites", timeout=10)
    if response1.status_code != 200:
        print("❌ Failed to get initial satellites")
        return False
    
    initial_count = len(response1.json()["satellites"])
    
    # Create a new satellite
    new_satellite = {
        "name": "Persistence Test Satellite",
        "type": "Test",
        "altitude": 500.0,
        "inclination": 90.0,
        "eccentricity": 0.01
    }
    
    response2 = requests.post(f"{API_BASE}/satellites/custom", json=new_satellite, timeout=10)
    if response2.status_code != 200:
        print("❌ Failed to create test satellite")
        return False
    
    # Get satellites again and check count increased
    response3 = requests.get(f"{API_BASE}/satellites", timeout=10)
    if response3.status_code != 200:
        print("❌ Failed to get satellites after creation")
        return False
    
    final_count = len(response3.json()["satellites"])
    
    if final_count == initial_count + 1:
        print(f"✅ Database persistence working: {initial_count} → {final_count} satellites")
        return True
    else:
        print(f"❌ Database persistence failed: expected {initial_count + 1}, got {final_count}")
        return False

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("🔍 Testing Edge Cases")
    
    # Test extreme but valid parameters
    edge_cases = [
        {
            "name": "Low Earth Orbit Edge",
            "altitude": 150.1,  # Just above minimum
            "inclination": 0.0,  # Equatorial
            "eccentricity": 0.0,  # Circular
            "should_pass": True
        },
        {
            "name": "High Orbit Edge", 
            "altitude": 35785.0,  # Just below geostationary
            "inclination": 180.0,  # Retrograde polar
            "eccentricity": 0.99,  # Highly elliptical
            "should_pass": True
        },
        {
            "name": "Invalid Low Altitude",
            "altitude": 149.9,  # Just below minimum
            "inclination": 45.0,
            "eccentricity": 0.1,
            "should_pass": False
        }
    ]
    
    passed = 0
    total = len(edge_cases)
    
    for case in edge_cases:
        test_data = {
            "name": case["name"],
            "type": "Edge Test",
            "altitude": case["altitude"],
            "inclination": case["inclination"],
            "eccentricity": case["eccentricity"]
        }
        
        response = requests.post(f"{API_BASE}/satellites/custom", json=test_data, timeout=10)
        
        if case["should_pass"]:
            if response.status_code == 200:
                print(f"✅ {case['name']}: Correctly accepted")
                passed += 1
            else:
                print(f"❌ {case['name']}: Should have been accepted but got {response.status_code}")
        else:
            if response.status_code == 400:
                print(f"✅ {case['name']}: Correctly rejected")
                passed += 1
            else:
                print(f"❌ {case['name']}: Should have been rejected but got {response.status_code}")
    
    return passed == total

def test_orbit_path_generation():
    """Test orbit path generation endpoint"""
    print("🛰️ Testing Orbit Path Generation")
    
    # Get a satellite ID first
    response = requests.get(f"{API_BASE}/satellites", timeout=10)
    if response.status_code != 200:
        print("❌ Failed to get satellites")
        return False
    
    satellites = response.json()["satellites"]
    if not satellites:
        print("❌ No satellites available for orbit path test")
        return False
    
    satellite_id = satellites[0]["id"]
    
    # Test orbit path generation
    response = requests.get(f"{API_BASE}/satellites/{satellite_id}/orbit-path?points=50", timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if "points" in data and len(data["points"]) == 50:
            # Check that points have x, y, z coordinates
            first_point = data["points"][0]
            if all(coord in first_point for coord in ["x", "y", "z"]):
                print(f"✅ Orbit path generation working: {len(data['points'])} points generated")
                return True
            else:
                print(f"❌ Orbit path points missing coordinates: {first_point}")
                return False
        else:
            print(f"❌ Orbit path generation failed: {data}")
            return False
    else:
        print(f"❌ Orbit path request failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🔬 Running Additional Backend Tests")
    print("=" * 50)
    
    tests = [
        test_orbital_mechanics,
        test_database_persistence,
        test_edge_cases,
        test_orbit_path_generation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Additional Tests: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All additional tests passed!")
    else:
        print("⚠️ Some additional tests failed.")