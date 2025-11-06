/**
 * API Configuration for Development and Production
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// ALWAYS use production backend to avoid doubling API calls
// API base URL
export const API_BASE_URL = 'https://max-ev-sports.com/api';

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // Always use production server (saves API quota)
  return `https://max-ev-sports.com/api/${cleanEndpoint}`;
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment,
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL
});
