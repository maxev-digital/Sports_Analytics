const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electron', {
  // Open a new window for a specific route
  openWindow: (route) => ipcRenderer.invoke('open-window', route),

  // Get list of currently open windows
  getOpenWindows: () => ipcRenderer.invoke('get-open-windows'),

  // Platform info
  platform: process.platform,
  isElectron: true,
  version: process.versions.electron,
});
