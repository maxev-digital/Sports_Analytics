// Debug what's actually being imported
const electron = require('electron');

console.log('=== ELECTRON DEBUG ===');
console.log('typeof electron:', typeof electron);
console.log('electron value:', electron);
console.log('electron keys:', Object.keys(electron || {}));
console.log('electron.app:', electron?.app);
console.log('electron.BrowserWindow:', electron?.BrowserWindow);

// Try destructuring
try {
  const { app, BrowserWindow } = require('electron');
  console.log('Destructure worked!');
  console.log('app:', app);
  console.log('BrowserWindow:', BrowserWindow);
} catch (err) {
  console.error('Destructure failed:', err.message);
}
