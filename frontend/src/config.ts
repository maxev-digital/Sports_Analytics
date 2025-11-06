/**
 * API Configuration for Development and Production
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// API base URL - use localhost in development, main domain in production
export const API_BASE_URL = isDevelopment
  ? 'http://localhost:8000/api'
  : 'https://max-ev-sports.com/api';

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // Use localhost in development, main domain in production
  return isDevelopment
    ? `http://localhost:8000/api/${cleanEndpoint}`
    : `https://max-ev-sports.com/api/${cleanEndpoint}`;
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment,
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL
});
