import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

class SatelliteAPI {
  // Satellite endpoints
  static async getSatellites() {
    try {
      const response = await axios.get(`${API}/satellites`);
      return response.data.satellites;
    } catch (error) {
      console.error('Error fetching satellites:', error);
      throw error;
    }
  }

  static async getSatellite(id) {
    try {
      const response = await axios.get(`${API}/satellites/${id}`);
      return response.data.satellite;
    } catch (error) {
      console.error('Error fetching satellite:', error);
      throw error;
    }
  }

  static async createCustomSatellite(satelliteData) {
    try {
      const response = await axios.post(`${API}/satellites/custom`, satelliteData);
      return response.data;
    } catch (error) {
      console.error('Error creating satellite:', error);
      throw error;
    }
  }

  static async updateSatellite(id, updates) {
    try {
      const response = await axios.put(`${API}/satellites/${id}`, updates);
      return response.data.satellite;
    } catch (error) {
      console.error('Error updating satellite:', error);
      throw error;
    }
  }

  // Configuration endpoints
  static async getConfigurations() {
    try {
      const response = await axios.get(`${API}/configurations`);
      return response.data.configurations;
    } catch (error) {
      console.error('Error fetching configurations:', error);
      throw error;
    }
  }

  static async saveConfiguration(configData) {
    try {
      const response = await axios.post(`${API}/configurations`, configData);
      return response.data;
    } catch (error) {
      console.error('Error saving configuration:', error);
      throw error;
    }
  }

  static async deleteConfiguration(id) {
    try {
      const response = await axios.delete(`${API}/configurations/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting configuration:', error);
      throw error;
    }
  }

  // Position tracking endpoints
  static async getSatellitePositions(satelliteId, start, end, limit = 100) {
    try {
      const params = new URLSearchParams();
      if (start) params.append('start', start.toISOString());
      if (end) params.append('end', end.toISOString());
      params.append('limit', limit.toString());

      const response = await axios.get(`${API}/satellites/${satelliteId}/positions?${params}`);
      return response.data.positions;
    } catch (error) {
      console.error('Error fetching positions:', error);
      throw error;
    }
  }

  static async startTrackingSatellite(satelliteId) {
    try {
      const response = await axios.post(`${API}/satellites/${satelliteId}/track`);
      return response.data;
    } catch (error) {
      console.error('Error starting tracking:', error);
      throw error;
    }
  }

  // Preferences endpoints
  static async getPreferences() {
    try {
      const response = await axios.get(`${API}/preferences`);
      return response.data.preferences;
    } catch (error) {
      console.error('Error fetching preferences:', error);
      throw error;
    }
  }

  static async updatePreferences(updates) {
    try {
      const response = await axios.put(`${API}/preferences`, updates);
      return response.data.preferences;
    } catch (error) {
      console.error('Error updating preferences:', error);
      throw error;
    }
  }

  // Utility endpoints
  static async getOrbitPath(satelliteId, points = 100) {
    try {
      const response = await axios.get(`${API}/satellites/${satelliteId}/orbit-path?points=${points}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching orbit path:', error);
      throw error;
    }
  }

  static async validateOrbitalParams(altitude, inclination, eccentricity) {
    try {
      const response = await axios.post(`${API}/validate-orbital-params`, {
        altitude,
        inclination,
        eccentricity
      });
      return response.data;
    } catch (error) {
      console.error('Error validating parameters:', error);
      throw error;
    }
  }

  static async healthCheck() {
    try {
      const response = await axios.get(`${API}/health`);
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }
}

export default SatelliteAPI;