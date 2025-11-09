const { app, BrowserWindow, Menu, Tray, ipcMain, screen } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

// Fix EPIPE errors on Windows (broken pipe when writing to stdout/stderr)
process.stdout.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Ignore EPIPE errors
    return;
  }
  console.error('stdout error:', err);
});

process.stderr.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Ignore EPIPE errors
    return;
  }
  console.error('stderr error:', err);
});

// Catch uncaught exceptions to prevent crashes
process.on('uncaughtException', (err) => {
  if (err.code === 'EPIPE') {
    // Ignore EPIPE errors
    return;
  }
  console.error('Uncaught exception:', err);
});

// Debug: Check if electron loaded properly
if (!app) {
  console.error('ERROR: Electron app module failed to load!');
  process.exit(1);
}

let mainWindow = null;
let tray = null;
const openWindows = new Map(); // Track open windows by route

// Multi-window configuration
const WINDOW_ROUTES = {
  'live-games': { title: 'Live Games - MAX EV SPORTS', width: 1400, height: 900 },
  'alerts': { title: 'Alerts - MAX EV SPORTS', width: 1200, height: 800 },
  'analytics': { title: 'Analytics - MAX EV SPORTS', width: 1400, height: 900 },
  'props': { title: 'Props - MAX EV SPORTS', width: 1300, height: 850 },
  'tools': { title: 'Tools - MAX EV SPORTS', width: 1200, height: 800 },
  'odds': { title: 'Odds - MAX EV SPORTS', width: 1400, height: 900 },
  'settings': { title: 'Settings - MAX EV SPORTS', width: 1000, height: 700 },
  'widget': { title: 'Alerts Widget - MAX EV SPORTS', width: 450, height: 1000, alwaysOnTop: true, resizable: true },
};

console.log('✅ WIDGET FEATURE LOADED - Routes available:', Object.keys(WINDOW_ROUTES));

function createWindow(route = 'live-games') {
  // Check if window already exists for this route
  if (openWindows.has(route)) {
    const existingWindow = openWindows.get(route);
    if (existingWindow && !existingWindow.isDestroyed()) {
      existingWindow.focus();
      return existingWindow;
    }
  }

  const config = WINDOW_ROUTES[route] || WINDOW_ROUTES['live-games'];

  const win = new BrowserWindow({
    width: config.width,
    height: config.height,
    minWidth: route === 'widget' ? 300 : 1000,
    minHeight: route === 'widget' ? 400 : 600,
    maxWidth: route === 'widget' ? 600 : undefined,  // Allow widget to be up to 600px wide
    title: config.title,
    icon: path.join(__dirname, '../public/logo2.png'),
    alwaysOnTop: config.alwaysOnTop || false,
    resizable: config.resizable !== undefined ? config.resizable : true,  // Use config or default to true
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false, // Allow loading external resources (production API)
    },
    backgroundColor: '#0f172a', // Slate-900 background
    show: false, // Show after ready-to-show to prevent flicker
  });

  // Load the app
  console.log('📍 Electron main: isDev =', isDev);
  console.log('📍 Electron main: NODE_ENV =', process.env.NODE_ENV);
  console.log('📍 Electron main: route =', route);

  if (isDev) {
    // Widget loads standalone HTML file
    if (route === 'widget') {
      const popupPath = path.join(__dirname, '../public/extension-widget/popup-desktop.html');
      console.log('📍 Loading widget from:', popupPath);
      win.loadFile(popupPath);
    } else {
      // DEV MODE: Load from localhost for instant updates with hot reload
      // This gives us latest code without deployment or Cloudflare caching
      const url = route === 'analytics'
        ? `http://localhost:5173/#/${route}?demo=true`
        : `http://localhost:5173/#/${route}`;
      console.log('📍 Loading URL:', url);
      win.loadURL(url);
    }

    // Log when page loads successfully
    win.webContents.once('did-finish-load', () => {
      console.log(`✅ Page did-finish-load for ${route}`);
      console.log(`📍 Current URL: ${win.webContents.getURL()}`);
    });

    // Log if page fails to load
    win.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
      console.error(`❌ Page failed to load for ${route}:`, errorCode, errorDescription, validatedURL);
    });

    // Log navigation events
    win.webContents.on('did-start-loading', () => {
      console.log(`📍 Started loading page for ${route}`);
    });

    win.webContents.on('did-stop-loading', () => {
      console.log(`📍 Stopped loading page for ${route}`);
      console.log(`📍 Final URL: ${win.webContents.getURL()}`);
    });

    // Capture renderer console messages in dev mode too
    win.webContents.on('console-message', (event, level, message, line, sourceId) => {
      console.log(`[RENDERER ${route}]:`, message);
    });
  } else {
    // Widget loads standalone HTML file
    if (route === 'widget') {
      const popupPath = path.join(__dirname, '../dist/extension-widget/popup-desktop.html');
      console.log('📍 Loading widget from:', popupPath);
      win.loadFile(popupPath);
    } else {
      // Load React app for other routes
      const indexPath = path.join(__dirname, '../dist/index.html');
      console.log('📍 Loading React app from:', indexPath);
      console.log('📍 With hash:', route);
      win.loadFile(indexPath, {
        hash: route
      });
    }

    // Log when page loads
    win.webContents.on('did-finish-load', () => {
      console.log(`✅ Page did-finish-load for ${route}`);
    });

    win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error(`❌ Page failed to load for ${route}:`, errorCode, errorDescription);
    });

    // Log console messages from the renderer process
    win.webContents.on('console-message', (event, level, message, line, sourceId) => {
      console.log(`[RENDERER ${route}]:`, message);
    });
  }

  // Show window immediately (don't wait for ready-to-show in dev mode)
  if (isDev) {
    console.log(`📍 Showing window immediately: ${route}`);
    win.show();
    if (route === 'live-games') {
      win.webContents.openDevTools();
    }
    console.log(`✅ Window shown: ${route}`);
  } else {
    // Production: wait for ready-to-show
    win.once('ready-to-show', () => {
      console.log(`✅ Window ready to show: ${route}`);
      win.show();
      if (route === 'live-games') {
        win.webContents.openDevTools();
      }
      console.log(`✅ Window shown: ${route}, size: ${win.getSize()}, position: ${win.getPosition()}`);
    });

    // DEBUGGING: Force show after 2 seconds if ready-to-show doesn't fire
    setTimeout(() => {
      if (!win.isDestroyed() && !win.isVisible()) {
        console.log(`⚠️ Forcing window to show (ready-to-show didn't fire): ${route}`);
        win.show();
        console.log(`✅ Window forced visible: ${route}, size: ${win.getSize()}, position: ${win.getPosition()}`);
      }
    }, 2000);
  }

  // Track window
  openWindows.set(route, win);

  // Clean up on close
  win.on('closed', () => {
    openWindows.delete(route);
    if (route === 'live-games') {
      mainWindow = null;
    }
  });

  // Set as main window if it's live-games
  if (route === 'live-games') {
    mainWindow = win;
  }

  console.log(`✅ Window created successfully: ${route}`);
  return win;
}

function createSystemTray() {
  const iconPath = path.join(__dirname, '../public/logo2.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '🔥 Live Games',
      click: () => createWindow('live-games'),
    },
    {
      label: '🚨 Alerts',
      click: () => createWindow('alerts'),
    },
    {
      label: '📲 Alerts Widget (Always On Top)',
      click: () => createWindow('widget'),
    },
    {
      label: '📊 Analytics',
      click: () => createWindow('analytics'),
    },
    {
      label: '🎯 Props',
      click: () => createWindow('props'),
    },
    {
      label: '🔧 Tools',
      click: () => createWindow('tools'),
    },
    {
      label: '📈 Odds',
      click: () => createWindow('odds'),
    },
    { type: 'separator' },
    {
      label: '⚙️ Settings',
      click: () => createWindow('settings'),
    },
    { type: 'separator' },
    {
      label: 'Show All Windows',
      click: () => {
        openWindows.forEach((win) => {
          if (!win.isDestroyed()) {
            win.show();
          }
        });
      },
    },
    {
      label: 'Hide All Windows',
      click: () => {
        openWindows.forEach((win) => {
          if (!win.isDestroyed()) {
            win.hide();
          }
        });
      },
    },
    { type: 'separator' },
    {
      label: 'Quit MAX EV SPORTS',
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setToolTip('MAX EV SPORTS - Desktop');
  tray.setContextMenu(contextMenu);

  // Double-click tray to open main window
  tray.on('double-click', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
    } else {
      createWindow('live-games');
    }
  });
}

// App menu for multi-window support
function createAppMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Window',
          submenu: [
            { label: 'Live Games', click: () => createWindow('live-games') },
            { label: 'Alerts', click: () => createWindow('alerts') },
            { label: 'Alerts Widget (Always On Top)', click: () => createWindow('widget') },
            { label: 'Analytics', click: () => createWindow('analytics') },
            { label: 'Props', click: () => createWindow('props') },
            { label: 'Tools', click: () => createWindow('tools') },
            { label: 'Odds', click: () => createWindow('odds') },
          ],
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        {
          label: 'Arrange Windows',
          submenu: [
            {
              label: 'Tile Horizontally',
              click: () => tileWindows('horizontal'),
            },
            {
              label: 'Tile Vertically',
              click: () => tileWindows('vertical'),
            },
            {
              label: 'Cascade',
              click: () => cascadeWindows(),
            },
          ],
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About MAX EV SPORTS',
          click: () => {
            const { dialog } = require('electron');
            dialog.showMessageBox({
              type: 'info',
              title: 'About MAX EV SPORTS',
              message: 'MAX EV SPORTS Desktop',
              detail: 'Version 1.0.0\n\nProfessional sports betting analytics and arbitrage detection.\n\n© 2025 Max EV Holdings, LLC. All rights reserved.',
            });
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Window arrangement functions
function tileWindows(orientation) {
  const displays = screen.getAllDisplays();
  const primaryDisplay = displays[0];
  const { width, height, x, y } = primaryDisplay.workArea;

  const windows = Array.from(openWindows.values()).filter(win => !win.isDestroyed());
  const count = windows.length;

  if (count === 0) return;

  if (orientation === 'horizontal') {
    const windowHeight = Math.floor(height / count);
    windows.forEach((win, index) => {
      win.setBounds({
        x: x,
        y: y + (windowHeight * index),
        width: width,
        height: windowHeight,
      });
    });
  } else {
    const windowWidth = Math.floor(width / count);
    windows.forEach((win, index) => {
      win.setBounds({
        x: x + (windowWidth * index),
        y: y,
        width: windowWidth,
        height: height,
      });
    });
  }
}

function cascadeWindows() {
  const displays = screen.getAllDisplays();
  const primaryDisplay = displays[0];
  const { x, y } = primaryDisplay.workArea;

  const windows = Array.from(openWindows.values()).filter(win => !win.isDestroyed());
  const offset = 30;

  windows.forEach((win, index) => {
    const config = WINDOW_ROUTES['live-games']; // Default size
    win.setBounds({
      x: x + (offset * index),
      y: y + (offset * index),
      width: config.width,
      height: config.height,
    });
  });
}

// App lifecycle
app.whenReady().then(() => {
  // IPC handlers for frontend communication (must be after app.whenReady)
  ipcMain.handle('open-window', (event, route) => {
    createWindow(route);
  });

  ipcMain.handle('get-open-windows', () => {
    return Array.from(openWindows.keys());
  });

  createAppMenu();
  createSystemTray();
  createWindow('live-games'); // Start with main window

  // DEMO: Open widget window immediately to show the feature
  // Temporarily disabled for debugging - focus on main window first
  // console.log('🚀 Opening widget window automatically for demo...');
  // createWindow('widget');

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow('live-games');
    }
  });
});

app.on('window-all-closed', () => {
  // Don't quit on macOS when all windows closed (app stays in tray)
  if (process.platform !== 'darwin') {
    // On Windows/Linux, keep running in system tray
    // User must quit from tray menu
  }
});

app.on('before-quit', () => {
  // Clean up tray
  if (tray) {
    tray.destroy();
  }
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // Focus main window if second instance is launched
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    } else {
      createWindow('live-games');
    }
  });
}
