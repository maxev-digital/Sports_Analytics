# Multi-Sport Live Betting Dashboard

Real-time sports betting analytics platform tracking NBA, NFL, NHL, and NCAAF games with arbitrage detection, steam moves, and line movement alerts.

## Quick Start

### 1. Environment Setup

Create `.env` file in `backend/` directory (parent of this folder):
```bash
ODDS_API_KEY=your_odds_api_key_here
GOOGLE_SHEETS_CREDENTIALS=google_sheets/credentials/service-account-key.json
GOOGLE_SHEETS_SHEET_ID=your_sheet_id
```

**IMPORTANT**: Never commit the `.env` file! It's already in `.gitignore`.

### 2. Install Backend Dependencies

```bash
cd backend
pip install fastapi uvicorn httpx pydantic python-dotenv gspread
```

Or if you have a `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Start the Backend

**IMPORTANT**: Use port **8001** (not 8000):
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: `http://localhost:8001`

### 5. Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5175` (or 5173/5174 if 5175 is in use)

## Architecture

```
backend/scrapers/nba/
├── backend/                    # FastAPI backend API
│   ├── main.py                # API endpoints + CORS config
│   ├── game_tracker.py        # Game data aggregation
│   ├── alert_monitor.py       # Arbitrage & alerts
│   ├── odds_client.py         # Odds API integration
│   ├── models.py              # Pydantic models
│   ├── config.py              # Configuration
│   ├── nba_stats_client.py    # NBA stats fetcher
│   ├── nfl_stats_client.py    # NFL stats fetcher
│   └── nhl_stats_client.py    # NHL stats fetcher
│
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── GameCard.tsx   # Game display card
│   │   │   └── Navigation.tsx # Navigation bar
│   │   ├── pages/             # Page components
│   │   │   ├── LiveGames.tsx  # Main dashboard
│   │   │   ├── Analytics.tsx  # Analytics page
│   │   │   ├── Alerts.tsx     # Alerts page
│   │   │   └── Props.tsx      # Player props page
│   │   ├── types.ts           # TypeScript types
│   │   └── App.tsx            # Main app
│   ├── package.json
│   └── vite.config.ts
│
└── README.md                   # This file
```

## Key Configuration

### Port Configuration

**Backend**: Port **8001** (configured in `main.py`)
**Frontend**: Port **5175** (auto-selected by Vite)

**Why port 8001?**
We use port 8001 instead of 8000 to avoid conflicts with zombie Python processes that can occupy port 8000.

### CORS Configuration

The backend (`main.py` lines 20-27) allows requests from:
- `http://localhost:5173`
- `http://localhost:5174`
- `http://localhost:5175`

If your frontend runs on a different port, add it to the `allow_origins` list in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Endpoints

### Games
- `GET /api/games` - Get all live/upcoming games
- `GET /api/games/{game_id}` - Get specific game
- `GET /api/health` - Health check

### Alerts
- `GET /api/alerts/arbitrage` - Arbitrage opportunities
- `GET /api/alerts/steam-moves` - Steam move alerts
- `GET /api/alerts/line-movements` - Line movement alerts
- `GET /api/alerts/all` - All alerts combined
- `GET /api/alerts/config` - Alert configuration
- `GET /api/alerts/performance` - Alert performance stats

### Player Props
- `GET /api/props/{sport}` - Player props for specific sport (nba, nfl, nhl, etc.)

## Features

- ✅ **Multi-Sport Coverage**: NBA, NFL, NHL, NCAAF
- ✅ **Real-Time Odds**: From 10+ sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- ✅ **Arbitrage Detection**: Finds guaranteed profit opportunities
- ✅ **Steam Moves**: Detects sharp money movement
- ✅ **Line Movements**: Tracks significant line changes
- ✅ **Live Stats**: Real-time game statistics and momentum
- ✅ **Auto-Refresh**: Updates every 5 seconds (frontend) / 10 seconds (backend)
- ✅ **Responsive Design**: Works on desktop and mobile

## Troubleshooting

### "CORS policy" error in browser console

**Problem**: `Access to fetch at 'http://localhost:8001/api/games' from origin 'http://localhost:5175' has been blocked by CORS policy`

**Solution**:
1. Check that backend is running on port **8001** (not 8000)
2. Check that frontend port (e.g., 5175) is in the `allow_origins` list in `backend/main.py`
3. Restart the backend after making CORS changes

### Port already in use

**Backend (port 8001)**:
```bash
# Windows
netstat -ano | findstr :8001
taskkill /F /PID <process_id>

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

**Frontend (port 5173/5174/5175)**: Vite will auto-select next available port

### Frontend shows but no games loading

1. Check backend is running: `curl http://localhost:8001/api/games`
2. Check browser console for errors (F12 → Console tab)
3. Verify CORS configuration includes your frontend port
4. Check that `.env` file has valid `ODDS_API_KEY`

### API key errors

**Error**: `401 Unauthorized` or `API requests remaining: 0`

**Solution**:
1. Get API key from https://the-odds-api.com/
2. Update `backend/.env` with: `ODDS_API_KEY=your_key_here`
3. Restart backend

## Development Workflow

### Making Changes

1. **Backend changes**: Backend auto-reloads with `--reload` flag
2. **Frontend changes**: Vite hot-reloads automatically
3. **Type changes**: Update `frontend/src/types.ts` and `backend/models.py`

### Adding a New Sport

1. Add sport to `alert_monitor.py` sports list
2. Add sport filter to `LiveGames.tsx` sports array
3. Create stats client if needed (e.g., `mlb_stats_client.py`)

## Deployment

### Local → VPS Migration

1. **Update CORS**: Change `allow_origins` to your VPS domain
2. **Update API URLs**: Change `http://localhost:8001` to `https://yourdomain.com`
3. **Environment**: Copy `.env` file to VPS (never commit it!)
4. **Process Manager**: Use PM2 or systemd to keep services running
5. **Reverse Proxy**: Use nginx to serve frontend and proxy API

### Example nginx config
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Testing

```bash
# Test backend
curl http://localhost:8001/api/games
curl http://localhost:8001/api/health
curl http://localhost:8001/api/alerts/all

# Test frontend
# Open browser to http://localhost:5175
# Open console (F12) and check for errors
```

## Git Workflow

```bash
# Initial setup
git init
git add .
git commit -m "Initial commit: Multi-sport betting dashboard"

# Create GitHub repo (on github.com)
git remote add origin https://github.com/yourusername/betting-dashboard.git
git push -u origin main

# Daily workflow
git add .
git commit -m "Description of changes"
git push
```

**NEVER commit**:
- `.env` file (contains API keys)
- `node_modules/` directory
- `__pycache__/` directories
- Large data files

## Support

For issues or questions:
1. Check this README first
2. Check browser console (F12) for frontend errors
3. Check backend terminal for API errors
4. Verify `.env` configuration

## License

Private project - All rights reserved
