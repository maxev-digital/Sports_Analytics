/**
 * API Configuration for Development and Production
 * UPDATED: 2025-11-13 - Always use VPS backend (no localhost)
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// ALWAYS use production VPS backend - predictions/data live on VPS only
export const API_BASE_URL = 'https://max-ev-sports.com/api';

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // Always use production API for all endpoints
  return `${API_BASE_URL}/${cleanEndpoint}`;
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment: isDevelopment ? 'true (but using VPS backend)' : 'false',
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL,
  note: 'ALWAYS using VPS backend - All predictions/data on VPS'
});
