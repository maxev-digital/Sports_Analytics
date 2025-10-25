# Desktop Client Dashboard Setup Guide for Max EV Sports

This guide outlines how to build a **desktop client dashboard prototype** for Max EV Sports using **Electron**, providing **Professional ($249.99/mo)** and **Elite Pro ($599.99/mo)** users with a standalone, cross-platform (Windows, macOS, Linux) app. The dashboard reuses your existing React 18 frontend (`EnhancedGameCard.tsx`, `MLAlerts.tsx`) and integrates with the ultimate tech stack (Sportradar sub-1s feeds, AWS Fargate, EC2 G5/G4dn, RDS PostgreSQL, MSK, Redis, CloudFront, SNS) for real-time alerts (<500ms), ML-driven features (true odds, arbitrage, sharp money), 30+ strategy toggles, and Kelly Criterion bet sizing. It supports offline caching, system tray alerts, and direct API access for premium users, enhancing UX for pro bettors.

## Prerequisites
- **Skills**: React 18, Vite, FastAPI, Sportradar API (from `odds_fetcher.py`).
- **Tools**: Node.js (v18+), npm, Git, AWS CLI, VS Code.
- **Project**: Existing React/FastAPI codebase, Sportradar API key, AWS credentials (Fargate, RDS, MSK).
- **Cost**: $0 (your time) + existing stack ($2,836-$3,336/mo).
- **Timeline**: 2-3 weeks (~80-120 hours solo).

## Implementation Steps

### 1. Initialize Electron (1 Day, ~8 Hours)
- **Goal**: Package React web app into a desktop client with system tray.
- **Steps**:
  1. Install Electron in `frontend/`:
     ```
     npm install electron electron-builder --save-dev
     ```
  2. Create main process (`frontend/electron/main.js`):
     ```javascript
     const { app, BrowserWindow, Tray } = require('electron');
     const path = require('path');

     let win, tray;

     app.whenReady().then(() => {
       win = new BrowserWindow({
         width: 1200,
         height: 800,
         webPreferences: {
           preload: path.join(__dirname, 'preload.js')
         }
       });
       win.loadFile('dist/index.html'); // Vite build

       tray = new Tray(path.join(__dirname, 'assets/icon.png'));
       tray.setToolTip('Max EV Sports');
       tray.on('click', () => win.isVisible() ? win.hide() : win.show());
     });

     app.on('window-all-closed', () => {
       if (process.platform !== 'darwin') app.quit();
     });
     ```
  3. Add preload script (`frontend/electron/preload.js`):
     ```javascript
     const { contextBridge, ipcRenderer } = require('electron');
     contextBridge.exposeInMainWorld('electronAPI', {
       onAlert: (callback) => ipcRenderer.on('alert', callback)
     });
     ```
  4. Update `package.json`:
     ```json
     {
       "main": "electron/main.js",
       "scripts": {
         "start": "electron .",
         "build": "vite build && electron-builder"
       },
       "build": {
         "appId": "com.maxevsports.desktop",
         "files": ["dist/**/*", "electron/**/*"],
         "win": { "target": "nsis" },
         "mac": { "target": "dmg" },
         "linux": { "target": "AppImage" }
       }
     }
     ```
  5. Test: Build React (`npm run build`), run Electron (`npm start`).
- **Output**: Desktop app with web UI (`LiveGames.tsx`, `MLAlerts.tsx`), tray icon.
- **UX**: Familiar interface, tray alerts (e.g., “Arbitrage: 5% profit”).

### 2. Integrate Sportradar WebSocket (2 Days, ~16 Hours)
- **Goal**: Stream sub-1s odds, scores, stats, injuries for real-time alerts.
- **Steps**:
  1. Add WebSocket client (`frontend/src/sportradar.js`):
     ```javascript
     const WebSocket = require('ws');
     export function connectSportradar(token) {
       const ws = new WebSocket(`wss://push.sportradar.com?key=${process.env.VITE_SPORTRADAR_API_KEY}&token=${token}`);
       ws.on('message', (data) => {
         const { odds, scores, injuries } = JSON.parse(data);
         localStorage.setItem('cached_odds', JSON.stringify(odds));
         window.postMessage({ type: 'SPORTRADAR_UPDATE', data }, '*');
       });
       return ws;
     }
     ```
  2. Update `MLAlerts.tsx` for real-time updates:
     ```javascript
     useEffect(() => {
       const ws = connectSportradar(localStorage.getItem('token'));
       window.addEventListener('message', (event) => {
         if (event.data.type === 'SPORTRADAR_UPDATE') {
           setAlerts(event.data.data.alerts);
         }
       });
       return () => ws.close();
     }, []);
     ```
  3. Backend sync (`odds_fetcher.py`): Stream to MSK Serverless ($75-$150/mo).
- **Output**: <500ms alerts (e.g., “Steam move: Warriors -3.5”); offline odds caching.
- **UX**: Instant updates, seamless alert display in `MLAlerts.tsx`.

### 3. API Access for ML Features (3 Days, ~24 Hours)
- **Goal**: Secure, rate-limited API for Professional (10,000 calls/day) and Elite Pro (unlimited, sub-50ms).
- **Steps**:
  1. Add FastAPI endpoints (`main.py`):
     ```javascript
     // Pseudo-code for Claude compatibility (actual Python in main.py)
     GET /api/ml-alerts: Returns ML-driven alerts (arbitrage, sharp money)
     POST /api/predict-true-odds: Returns true odds, Kelly sizing
     Dependencies: OAuth2 (fastapi-users), Redis rate-limiting
     ```
  2. Secure with OAuth 2.0:
     - Use `fastapi-users` for token issuance.
     - Rate-limit Professional via Redis ($15-$100/mo): 10,000 calls/day.
     - Elite Pro: Unlimited, sub-50ms via dedicated G4dn ($131-$262/mo).
  3. Client API call (`frontend/src/api.js`):
     ```javascript
     import axios from 'axios';
     export async function getMLAlerts() {
       const { data } = await axios.get('/api/ml-alerts', {
         headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
       });
       return data.alerts;
     }
     ```
- **Output**: Secure API with <500ms (Professional) or <50ms (Elite Pro) responses.
- **UX**: Real-time ML alerts (e.g., “5% arbitrage, 88% confidence”) in dashboard.

### 4. Offline ML and Kelly Criterion (4 Days, ~32 Hours)
- **Goal**: Embed pre-trained ML models for offline Kelly sizing.
- **Steps**:
  1. Export XGBoost/LSTM models from G5 ($29/mo):
     ```javascript
     // Pseudo-code: Export models to frontend/models/
     Save xgb_true_odds.pkl and lstm_momentum.pth
     ```
  2. Load in client (`frontend/src/ml.js`):
     ```javascript
     import { XGBoost } from 'xgboost';
     const model = XGBoost.load('models/xgb_true_odds.pkl');
     export function offlineKelly(gameData, bankroll) {
       const features = extractFeatures(gameData);
       const prob = model.predict(features);
       return calculateKelly(prob, bankroll); // e.g., "Bet $50"
     }
     ```
  3. Integrate in `EnhancedGameCard.tsx`:
     ```javascript
     const kellyBet =