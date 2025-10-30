/**
 * API Configuration for Development and Production
 */

// Detect if we're in development or production
const isDevelopment =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

// API base URL
export const API_BASE_URL = isDevelopment
  ? '/api'  // Proxied by Vite dev server in development
  : 'https://max-ev-sports.com/api';  // Direct to VPS in production

// Helper function to build API URLs
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  if (isDevelopment) {
    // In development, use the proxy
    return `/api/${cleanEndpoint}`;
  } else {
    // In production, use full URL
    return `https://max-ev-sports.com/api/${cleanEndpoint}`;
  }
}

// Debug logging
console.log('🔧 API Config:', {
  isDevelopment,
  hostname: window.location.hostname,
  protocol: window.location.protocol,
  API_BASE_URL
});
