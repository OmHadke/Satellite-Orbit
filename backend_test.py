#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Satellite Orbit Simulation
Tests all endpoints: satellites, configurations, health check, and validation
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://orbit-explorer-3.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SatelliteAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("Health Check", True, f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_get_satellites(self):
        """Test GET /api/satellites endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/satellites", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if "satellites" in data and isinstance(data["satellites"], list):
                    satellites = data["satellites"]
                    if len(satellites) > 0:
                        # Check if default satellites were initialized
                        satellite_names = [sat.get("name", "") for sat in satellites]
                        expected_defaults = ["International Space Station (ISS)", "Hubble Space Telescope", "GPS Satellite"]
                        has_defaults = any(any(expected in name for expected in expected_defaults) for name in satellite_names)
                        
                        # Validate satellite structure
                        first_sat = satellites[0]
                        required_fields = ["id", "name", "type", "altitude", "inclination", "eccentricity", "period"]
                        missing_fields = [field for field in required_fields if field not in first_sat]
                        
                        if missing_fields:
                            self.log_test("Get Satellites", False, f"Missing fields: {missing_fields}")
                            return False
                        
                        # Validate orbital calculations
                        if first_sat.get("period", 0) <= 0:
                            self.log_test("Get Satellites", False, "Invalid orbital period calculation")
                            return False
                            
                        self.log_test("Get Satellites", True, f"Retrieved {len(satellites)} satellites, defaults initialized: {has_defaults}")
                        return satellites
                    else:
                        self.log_test("Get Satellites", False, "No satellites returned")
                        return False
                else:
                    self.log_test("Get Satellites", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_test("Get Satellites", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Satellites", False, f"Exception: {str(e)}")
            return False
    
    def test_create_custom_satellite(self):
        """Test POST /api/satellites/custom endpoint"""
        try:
            # Test valid satellite creation
            valid_satellite = {
                "name": "Test Satellite Alpha",
                "type": "Test",
                "altitude": 500.0,
                "inclination": 45.0,
                "eccentricity": 0.01,
                "color": "#ff0000",
                "description": "Test satellite for API validation",
                "active": True
            }
            
            response = self.session.post(
                f"{API_BASE}/satellites/custom",
                json=valid_satellite,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "satellite" in data and "id" in data:
                    satellite = data["satellite"]
                    # Validate that period was calculated
                    if satellite.get("period", 0) > 0:
                        self.log_test("Create Custom Satellite (Valid)", True, f"Created satellite with ID: {data['id']}")
                        return data["id"]  # Return ID for further tests
                    else:
                        self.log_test("Create Custom Satellite (Valid)", False, "Period not calculated")
                        return False
                else:
                    self.log_test("Create Custom Satellite (Valid)", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Create Custom Satellite (Valid)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Custom Satellite (Valid)", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_satellite_creation(self):
        """Test satellite creation with invalid parameters"""
        try:
            # Test invalid altitude (too low)
            invalid_satellite = {
                "name": "Invalid Satellite",
                "type": "Test",
                "altitude": 100.0,  # Below 150km threshold
                "inclination": 45.0,
                "eccentricity": 0.01
            }
            
            response = self.session.post(
                f"{API_BASE}/satellites/custom",
                json=invalid_satellite,
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if "detail" in data and "errors" in data["detail"]:
                    errors = data["detail"]["errors"]
                    if any("150km" in error for error in errors):
                        self.log_test("Create Custom Satellite (Invalid Altitude)", True, f"Correctly rejected: {errors}")
                        return True
                    else:
                        self.log_test("Create Custom Satellite (Invalid Altitude)", False, f"Wrong error message: {errors}")
                        return False
                else:
                    self.log_test("Create Custom Satellite (Invalid Altitude)", False, f"Invalid error response: {data}")
                    return False
            else:
                self.log_test("Create Custom Satellite (Invalid Altitude)", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create Custom Satellite (Invalid Altitude)", False, f"Exception: {str(e)}")
            return False
    
    def test_update_satellite(self, satellite_id: str):
        """Test PUT /api/satellites/{id} endpoint"""
        try:
            # Test valid update
            update_data = {
                "altitude": 600.0,
                "active": False
            }
            
            response = self.session.put(
                f"{API_BASE}/satellites/{satellite_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "satellite" in data:
                    satellite = data["satellite"]
                    if satellite.get("altitude") == 600.0 and satellite.get("active") == False:
                        # Check if period was recalculated
                        if satellite.get("period", 0) > 0:
                            self.log_test("Update Satellite", True, f"Updated altitude to {satellite['altitude']}km, period recalculated")
                            return True
                        else:
                            self.log_test("Update Satellite", False, "Period not recalculated after altitude change")
                            return False
                    else:
                        self.log_test("Update Satellite", False, f"Update not applied correctly: {satellite}")
                        return False
                else:
                    self.log_test("Update Satellite", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Update Satellite", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Satellite", False, f"Exception: {str(e)}")
            return False
    
    def test_get_configurations(self):
        """Test GET /api/configurations endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/configurations", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "configurations" in data and isinstance(data["configurations"], list):
                    configs = data["configurations"]
                    self.log_test("Get Configurations", True, f"Retrieved {len(configs)} configurations")
                    return True
                else:
                    self.log_test("Get Configurations", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_test("Get Configurations", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Configurations", False, f"Exception: {str(e)}")
            return False
    
    def test_save_configuration(self):
        """Test POST /api/configurations endpoint"""
        try:
            config_data = {
                "name": "Test Configuration Alpha",
                "description": "Test configuration for API validation",
                "satellite_params": {
                    "altitude": 500,
                    "inclination": 45,
                    "eccentricity": 0.01
                },
                "time_speed": 2.0,
                "selected_satellite_id": "test-satellite-id"
            }
            
            response = self.session.post(
                f"{API_BASE}/configurations",
                json=config_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "configuration" in data and "id" in data:
                    config = data["configuration"]
                    if config.get("name") == config_data["name"]:
                        self.log_test("Save Configuration", True, f"Saved configuration with ID: {data['id']}")
                        return data["id"]
                    else:
                        self.log_test("Save Configuration", False, f"Configuration data mismatch: {config}")
                        return False
                else:
                    self.log_test("Save Configuration", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Save Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Save Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_orbital_validation(self):
        """Test orbital parameter validation endpoint"""
        try:
            # Test valid parameters
            response = self.session.post(
                f"{API_BASE}/validate-orbital-params",
                params={"altitude": 500, "inclination": 45, "eccentricity": 0.01},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") == True:
                    self.log_test("Orbital Validation (Valid Params)", True, "Parameters validated successfully")
                else:
                    self.log_test("Orbital Validation (Valid Params)", False, f"Valid parameters rejected: {data}")
                    return False
            else:
                self.log_test("Orbital Validation (Valid Params)", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Test invalid parameters
            response = self.session.post(
                f"{API_BASE}/validate-orbital-params",
                params={"altitude": 50, "inclination": 200, "eccentricity": 1.5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") == False and len(data.get("errors", [])) > 0:
                    self.log_test("Orbital Validation (Invalid Params)", True, f"Invalid parameters correctly rejected: {data['errors']}")
                    return True
                else:
                    self.log_test("Orbital Validation (Invalid Params)", False, f"Invalid parameters not rejected: {data}")
                    return False
            else:
                self.log_test("Orbital Validation (Invalid Params)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Orbital Validation", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"🚀 Starting Satellite Orbit Simulation Backend API Tests")
        print(f"Backend URL: {API_BASE}")
        print("=" * 60)
        
        # Test 1: Health Check
        health_ok = self.test_health_check()
        
        # Test 2: Get Satellites (should initialize defaults if empty)
        satellites = self.test_get_satellites()
        
        # Test 3: Create Custom Satellite
        satellite_id = self.test_create_custom_satellite()
        
        # Test 4: Invalid Satellite Creation
        self.test_invalid_satellite_creation()
        
        # Test 5: Update Satellite (if we have a satellite ID)
        if satellite_id:
            self.test_update_satellite(satellite_id)
        
        # Test 6: Get Configurations
        self.test_get_configurations()
        
        # Test 7: Save Configuration
        self.test_save_configuration()
        
        # Test 8: Orbital Parameter Validation
        self.test_orbital_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = SatelliteAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        exit(0)
    else:
        print("\n💥 Some tests failed. Check the details above.")
        exit(1)