# MAX EV SPORTS - Desktop Client

Professional sports betting analytics desktop application built with Electron + React.

## Features

### 🖥️ Multi-Window Support
- Open multiple screens simultaneously
- Drag windows to different monitors
- Each window is independent
- System remembers window positions

### 🎯 Available Windows
1. **Live Games** - Real-time game tracking and odds
2. **Alerts** - Betting opportunity notifications
3. **Analytics** - Performance tracking and insights
4. **Props** - Player prop betting analysis
5. **Tools** - Arbitrage and middle finders
6. **Odds** - Multi-sportsbook odds comparison

### 🔔 System Tray Integration
- Runs in background
- Right-click tray icon for quick access
- Open any window from tray menu
- Desktop notifications for alerts

### ⚡ Performance Benefits
- **Faster startup:** 0.5s vs 3s web load
- **Always-on monitoring:** Background alerts
- **Native notifications:** Never miss opportunities
- **Multi-monitor workflow:** Professional trading setup

---

## Development

### Prerequisites
```bash
Node.js 18+ and npm
```

### Install Dependencies
```bash
cd frontend
npm install
```

### Run in Development Mode
```bash
# Terminal 1: Start Vite dev server
npm run dev

# Terminal 2: Start Electron (points to localhost:5173)
npm run dev:electron
```

### Build for Production
```bash
# Build web assets first
npm run build

# Build desktop installer
npm run build:electron
```

This creates installers in `dist-electron/`:
- **Windows:** `MAX EV SPORTS Setup 1.0.0.exe` (NSIS installer) + portable EXE
- **Mac:** `MAX EV SPORTS-1.0.0.dmg` + ZIP
- **Linux:** `MAX EV SPORTS-1.0.0.AppImage` + `.deb` package

---

## Architecture

### File Structure
```
frontend/
├── electron/
│   ├── main.js          # Electron main process (window management)
│   └── preload.js       # Secure IPC bridge
├── src/
│   ├── components/
│   │   └── ElectronWindowControls.tsx  # Multi-window UI
│   └── App.tsx          # Main React app
├── dist/                # Vite build output (web assets)
└── dist-electron/       # Electron installers
```

### Multi-Window System

#### Opening New Windows
From the UI:
```typescript
// Click button in ElectronWindowControls component
window.electron.openWindow('alerts');
```

From system tray:
- Right-click tray icon
- Click "Alerts", "Analytics", etc.

From menu bar:
- File → New Window → Select page

#### Window Management
- **Tile Horizontally:** Stack windows vertically
- **Tile Vertically:** Arrange windows side-by-side
- **Cascade:** Offset windows diagonally

#### System Tray Features
- **Double-click:** Open/focus main window
- **Right-click:** Context menu with all pages
- **Show/Hide All:** Manage all windows at once

---

## Configuration

### Backend API URL
Development (localhost):
```javascript
// Vite proxy handles /api requests to localhost:8000
```

Production (VPS):
```javascript
// Update electron/main.js if needed:
// Change API base URL to https://max-ev-sports.com
```

### Window Sizes
Edit `electron/main.js`:
```javascript
const WINDOW_ROUTES = {
  'live-games': { width: 1400, height: 900 },
  'alerts': { width: 1200, height: 800 },
  // ... customize sizes
};
```

### Icons
Place icons in `public/`:
- `logo2.png` - Main app icon (used for taskbar, tray, installer)

---

## Distribution

### Windows Installer Features
- **NSIS installer** with custom branding
- Desktop shortcut creation
- Start menu integration
- Choose installation directory
- Automatic updates (can be configured)

### Portable Version
- No installation required
- Run from USB drive
- Perfect for multiple computers

### Auto-Updates (Optional)
Configure in `package.json`:
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "your-username",
      "repo": "max-ev-sports"
    }
  }
}
```

Then use `electron-updater` for automatic updates.

---

## Security

### IPC Communication
- **Context Isolation:** Enabled (no direct Node.js access in renderer)
- **Preload Script:** Exposes only specific APIs
- **No Remote Module:** Disabled for security

### Exposed APIs
Only these methods are available to React:
```typescript
window.electron.openWindow(route)
window.electron.getOpenWindows()
window.electron.platform
window.electron.isElectron
```

---

## Multi-Monitor Workflow Examples

### Professional Trader Setup (3 Monitors)
1. **Monitor 1 (Center):** Live Games - main action
2. **Monitor 2 (Left):** Alerts - opportunity notifications
3. **Monitor 3 (Right):** Analytics - performance tracking

### Quick Setup
1. Open all desired windows from system tray
2. Drag each to preferred monitor
3. Windows remember positions on next launch

### Hotkeys (Future Enhancement)
- `Ctrl+Shift+1` - Open Live Games
- `Ctrl+Shift+2` - Open Alerts
- `Ctrl+Shift+3` - Open Analytics
- `Ctrl+Shift+A` - Arrange windows (tile)

---

## Comparison: Web vs Desktop

| Feature | Web | Desktop |
|---------|-----|---------|
| Multi-window | Browser tabs | Native OS windows |
| Multi-monitor | Limited | Full support |
| Background alerts | Unreliable | Always works |
| Startup time | 2-5s | 0.5s |
| System tray | No | Yes |
| Notifications | Browser permission | OS native |
| Offline mode | No | Yes (cached data) |
| Professional feel | Good | Premium |

---

## Troubleshooting

### Electron won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

### Build fails
```bash
# Ensure web assets are built first
npm run build
# Then build Electron
npm run build:electron
```

### Windows Defender blocks installer
- Right-click installer → Properties → Unblock
- Or sign the executable (requires code signing certificate)

### Multiple instances opening
- App enforces single instance by default
- Second launch focuses existing window

---

## Elite Tier Exclusive

This desktop client is **exclusive to Elite tier ($129.99/mo) and above**:
- Elite: Desktop client included
- Professional: Desktop + priority support
- Elite Pro: Desktop + dedicated infrastructure

Free/Starter/Pro tiers use web version only.

---

## Support

- **Documentation:** https://max-ev-sports.com/learn
- **Issues:** Contact support or file GitHub issue
- **Updates:** App checks for updates on launch (if configured)

---

## License

© 2025 Casino Tears - MAX EV SPORTS™. All Rights Reserved.

Desktop client is proprietary software. Unauthorized distribution prohibited.
