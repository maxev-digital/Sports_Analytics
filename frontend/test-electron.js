// Minimal Electron test to verify installation
const { app, BrowserWindow } = require('electron');

console.log('✓ Electron modules loaded successfully');
console.log('✓ App version:', app.getVersion());
console.log('✓ Electron version:', process.versions.electron);

app.whenReady().then(() => {
  console.log('✓ App ready');

  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    }
  });

  win.loadURL('http://localhost:5173');
  console.log('✓ Window created and loading localhost:5173');

  win.on('ready-to-show', () => {
    console.log('✓ Window ready - Electron is working!');
    win.show();
  });
});

app.on('window-all-closed', () => {
  console.log('✓ All windows closed');
  app.quit();
});

console.log('✓ Test script running...');
