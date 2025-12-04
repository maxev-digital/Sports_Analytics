/**
 * API Configuration for Development and Production
 * UPDATED: 2025-12-01 - Nginx proxies to port 8888
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// Use localhost for local dev, production API for prod (proxied by nginx to port 8888)
export const API_BASE_URL = isDevelopment
  ? 'http://localhost:8888/api'
  : 'https://max-ev-sports.com/api';

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  return `${API_BASE_URL}/${cleanEndpoint}`;
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment,
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL,
  note: 'Production API proxied by nginx to port 8888 backend'
});
