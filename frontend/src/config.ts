/**
 * API Configuration for Development and Production
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// ALWAYS use production API (even in local dev/Electron)
// This saves resources by not running a local backend
export const API_BASE_URL = 'https://max-ev-sports.com/api';

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // TEMPORARY: Edge Lab endpoints use localhost for testing with C1's backend
  // TODO: Remove this once Edge Lab endpoints are deployed to production
  if (isDevelopment && (
    cleanEndpoint.startsWith('models/') ||
    cleanEndpoint.startsWith('simulation/') ||
    cleanEndpoint.startsWith('edge-scanner/')
  )) {
    return `http://localhost:8001/api/${cleanEndpoint}`;
  }

  // All other endpoints use production API
  return `https://max-ev-sports.com/api/${cleanEndpoint}`;
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment,
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL,
  note: 'Using production API for all environments'
});
