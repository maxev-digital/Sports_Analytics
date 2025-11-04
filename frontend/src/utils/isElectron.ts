/**
 * Detect if the app is running in Electron (desktop client)
 * vs. running in a regular web browser
 */
export function isElectron(): boolean {
  // Check if we're in a browser environment first
  if (typeof window === 'undefined') {
    return false;
  }

  // Check for Electron-specific APIs
  const userAgent = window.navigator.userAgent.toLowerCase();

  // Electron sets a specific user agent
  if (userAgent.indexOf('electron') > -1) {
    return true;
  }

  // Check for window.electron or window.require (injected by preload)
  if ((window as any).electron || (window as any).require) {
    return true;
  }

  return false;
}
