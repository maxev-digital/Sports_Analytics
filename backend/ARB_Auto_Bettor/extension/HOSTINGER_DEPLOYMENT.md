# ARB Auto Bettor™ - Hostinger Production Deployment Guide

## Overview

This guide walks you through deploying the ARB Auto Bettor system to Hostinger for production use. The system consists of:

1. **Frontend** (React/Vite) - User-facing website
2. **Backend** (FastAPI/Python) - API and WebSocket server
3. **Chrome Extension** - Browser automation tool

---

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Hostinger VPS account with SSH access
- [ ] Domain name configured (e.g., sporttrader.io or arbautobettor.com)
- [ ] SSL certificate for domain (Hostinger usually provides Let's Encrypt)
- [ ] Backend tested locally with live opportunities
- [ ] Frontend tested locally
- [ ] Chrome extension tested locally
- [ ] Python 3.12+ installed on Hostinger VPS
- [ ] Node.js 18+ installed on Hostinger VPS
- [ ] nginx or Apache web server installed

---

## Part 1: Backend Deployment (FastAPI + WebSocket)

### Step 1.1: Prepare Backend for Production

**1. Update CORS configuration for production domain:**

Edit `C:\Users\nashr\backend\scrapers\nba\backend\main.py`:

```python
# PRODUCTION CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production domains
        "https://sporttrader.io",
        "https://www.sporttrader.io",
        "https://api.sporttrader.io",
        # Chrome extension (all platforms)
        "chrome-extension://*",
        # Local development (keep for testing)
        "http://localhost:5173",
        "http://localhost:5179",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Create production environment file:**

Create `C:\Users\nashr\backend\scrapers\nba\backend\.env.production`:

```bash
# Production Environment Variables
ODDS_API_KEY=your_odds_api_key_here
GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json
GOOGLE_SHEETS_SHEET_ID=1bFNPXj2wOOBid8d-dnHbKmSs5U90a66X29-PFRmkgvo

# Production settings
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database (if applicable)
DATABASE_URL=postgresql://user:pass@localhost/arbdb

# Security
SECRET_KEY=generate_a_secure_random_key_here
ALLOWED_HOSTS=sporttrader.io,www.sporttrader.io,api.sporttrader.io
```

**3. Update requirements.txt:**

Create `C:\Users\nashr\backend\scrapers\nba\backend\requirements.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
python-dotenv==1.0.0
requests==2.31.0
pandas==2.1.3
numpy==1.26.2
gspread==5.12.0
oauth2client==4.1.3
nba-api==1.4.1
python-multipart==0.0.6
pydantic==2.5.0
```

### Step 1.2: Upload Backend to Hostinger

**1. Connect to Hostinger via SSH:**

```bash
ssh username@your-hostinger-ip
# Or use domain: ssh username@sporttrader.io
```

**2. Create application directory:**

```bash
mkdir -p /home/username/sporttrader-backend
cd /home/username/sporttrader-backend
```

**3. Upload backend files:**

**Option A: Using SCP from local machine:**
```bash
# From your local machine (Windows)
scp -r C:\Users\nashr\backend\scrapers\nba\backend\* username@sporttrader.io:/home/username/sporttrader-backend/
```

**Option B: Using Git (recommended):**
```bash
# On Hostinger VPS
cd /home/username/sporttrader-backend
git clone https://github.com/yourusername/sporttrader-backend.git .
```

**Option C: Using Hostinger File Manager:**
- Zip the `backend` folder locally
- Upload via Hostinger control panel
- Extract on server

**4. Install Python dependencies:**

```bash
cd /home/username/sporttrader-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 1.3: Configure Production WebSocket with SSL

WebSocket over HTTPS requires `wss://` (WebSocket Secure).

**1. Install nginx (if not already installed):**

```bash
sudo apt update
sudo apt install nginx
```

**2. Configure nginx as reverse proxy:**

Create `/etc/nginx/sites-available/sporttrader-api`:

```nginx
# Backend API & WebSocket
server {
    listen 80;
    server_name api.sporttrader.io;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.sporttrader.io;

    # SSL certificate (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.sporttrader.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.sporttrader.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # API endpoints
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeout settings
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

**3. Enable site and reload nginx:**

```bash
sudo ln -s /etc/nginx/sites-available/sporttrader-api /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**4. Obtain SSL certificate (Let's Encrypt):**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.sporttrader.io
```

### Step 1.4: Run Backend as System Service

**1. Create systemd service file:**

Create `/etc/systemd/system/sporttrader-backend.service`:

```ini
[Unit]
Description=SportTrader Backend API
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/sporttrader-backend
Environment="PATH=/home/username/sporttrader-backend/venv/bin"
EnvironmentFile=/home/username/sporttrader-backend/.env.production
ExecStart=/home/username/sporttrader-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. Enable and start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable sporttrader-backend
sudo systemctl start sporttrader-backend
sudo systemctl status sporttrader-backend
```

**3. Verify backend is running:**

```bash
curl http://localhost:8000/api/alerts/all
# Should return JSON with opportunities
```

---

## Part 2: Frontend Deployment (React/Vite)

### Step 2.1: Prepare Frontend for Production

**1. Update API URLs in frontend:**

Edit `C:\Users\nashr\backend\scrapers\nba\frontend\src\config.ts` (create if doesn't exist):

```typescript
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'https://api.sporttrader.io',
  wsURL: import.meta.env.VITE_WS_URL || 'wss://api.sporttrader.io/ws',
};
```

**2. Update environment files:**

Create `C:\Users\nashr\backend\scrapers\nba\frontend\.env.production`:

```bash
VITE_API_URL=https://api.sporttrader.io
VITE_WS_URL=wss://api.sporttrader.io/ws
```

**3. Build production bundle:**

```bash
cd C:\Users\nashr\backend\scrapers\nba\frontend
npm install
npm run build
```

This creates a `dist/` folder with optimized production files.

### Step 2.2: Upload Frontend to Hostinger

**1. Create frontend directory on server:**

```bash
ssh username@sporttrader.io
mkdir -p /home/username/sporttrader-frontend
```

**2. Upload dist folder:**

```bash
# From local machine
scp -r C:\Users\nashr\backend\scrapers\nba\frontend\dist\* username@sporttrader.io:/home/username/sporttrader-frontend/
```

**3. Configure nginx for frontend:**

Create `/etc/nginx/sites-available/sporttrader-frontend`:

```nginx
# Frontend website
server {
    listen 80;
    server_name sporttrader.io www.sporttrader.io;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sporttrader.io www.sporttrader.io;

    # SSL certificate
    ssl_certificate /etc/letsencrypt/live/sporttrader.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sporttrader.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    root /home/username/sporttrader-frontend;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing (React Router)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**4. Enable site and reload nginx:**

```bash
sudo ln -s /etc/nginx/sites-available/sporttrader-frontend /etc/nginx/sites-enabled/
sudo certbot --nginx -d sporttrader.io -d www.sporttrader.io
sudo nginx -t
sudo systemctl reload nginx
```

---

## Part 3: Chrome Extension Production Configuration

### Step 3.1: Update Extension for Production

**1. Update manifest.json host permissions:**

Edit `C:\Users\nashr\backend\ARB_Auto_Bettor\extension\manifest.json`:

```json
{
  "host_permissions": [
    "https://api.sporttrader.io/*",
    "https://sporttrader.io/*",
    "https://sportsbook.draftkings.com/*",
    "https://sportsbook.fanduel.com/*",
    "https://sports.betmgm.com/*",
    "https://www.caesars.com/sportsbook-and-casino/*",
    "https://www.betrivers.com/*",
    "https://*/williamhill/*",
    "https://fanatics.com/betting/*",
    "https://www.mybookie.ag/*",
    "https://www.betus.com.pa/*",
    "https://www.betonline.ag/*",
    "https://lowvig.ag/*"
  ]
}
```

**2. Update background.js WebSocket URL:**

Edit `C:\Users\nashr\backend\ARB_Auto_Bettor\extension\background.js`:

```javascript
// Production WebSocket configuration
const WS_URL = 'wss://api.sporttrader.io/ws';

function connectWebSocket() {
  console.log('[ARB] Connecting to production WebSocket:', WS_URL);
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('[ARB] Connected to production server');
    chrome.action.setBadgeText({ text: 'ON' });
    chrome.action.setBadgeBackgroundColor({ color: '#10B981' });

    // Subscribe to arbitrage alerts
    ws.send(JSON.stringify({
      type: 'subscribe',
      channel: 'arbitrage_alerts'
    }));
  };

  // ... rest of WebSocket logic
}
```

**3. Update popup.js API endpoints:**

Edit `C:\Users\nashr\backend\ARB_Auto_Bettor\extension\popup\popup.js`:

```javascript
// Production API configuration
const API_BASE_URL = 'https://api.sporttrader.io';

document.getElementById('settingsBtn').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://sporttrader.io/alerts' });
});
```

### Step 3.2: Package Extension for Distribution

**Option A: Chrome Web Store (Public Distribution)**

1. **Create a ZIP package:**
```bash
cd C:\Users\nashr\backend\ARB_Auto_Bettor
powershell Compress-Archive -Path extension\* -DestinationPath ARB_Auto_Bettor_v1.0.0.zip
```

2. **Create Chrome Web Store developer account:**
   - Go to: https://chrome.google.com/webstore/devconsole
   - Pay $5 one-time registration fee
   - Set up developer profile

3. **Upload extension:**
   - Click "New Item"
   - Upload `ARB_Auto_Bettor_v1.0.0.zip`
   - Fill in store listing details:
     - Title: "ARB Auto Bettor™"
     - Description: "Automated arbitrage betting assistant - 95% automated, 100% ToS compliant"
     - Category: "Productivity"
     - Screenshots: Required (capture popup, alerts page)
   - Submit for review (typically 1-3 days)

4. **Update manifest with Web Store ID:**
After approval, update `manifest.json`:
```json
{
  "key": "YOUR_WEB_STORE_KEY_HERE"
}
```

**Option B: Private Distribution (Load Unpacked)**

If not publishing publicly, users install via "Load unpacked":

1. **Host the ZIP file on your website:**
```bash
# Upload to Hostinger
scp ARB_Auto_Bettor_v1.0.0.zip username@sporttrader.io:/home/username/sporttrader-frontend/downloads/
```

2. **Create installation page:**
Add to your website at `https://sporttrader.io/extension`:
```html
<h1>ARB Auto Bettor™ Chrome Extension</h1>
<p>Download and install our automated arbitrage betting assistant.</p>
<a href="/downloads/ARB_Auto_Bettor_v1.0.0.zip">Download Extension v1.0.0</a>

<h2>Installation Instructions:</h2>
<ol>
  <li>Download the ZIP file above</li>
  <li>Extract to a folder on your computer</li>
  <li>Open Chrome and go to chrome://extensions/</li>
  <li>Enable "Developer mode" (top-right toggle)</li>
  <li>Click "Load unpacked"</li>
  <li>Select the extracted folder</li>
</ol>
```

---

## Part 4: Production Environment Configuration

### Step 4.1: Environment Variables

**Backend (.env.production):**
```bash
ENVIRONMENT=production
DEBUG=False
ODDS_API_KEY=your_production_key
GOOGLE_SHEETS_CREDENTIALS=/home/username/credentials.json
ALLOWED_HOSTS=sporttrader.io,www.sporttrader.io,api.sporttrader.io
SECRET_KEY=generate_secure_random_key_with_openssl
DATABASE_URL=postgresql://user:pass@localhost/arbdb
```

**Frontend (.env.production):**
```bash
VITE_API_URL=https://api.sporttrader.io
VITE_WS_URL=wss://api.sporttrader.io/ws
VITE_ENVIRONMENT=production
```

### Step 4.2: Security Hardening

**1. Firewall configuration (UFW):**
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**2. Fail2ban (brute force protection):**
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**3. Rate limiting in nginx:**

Edit nginx config:
```nginx
# Rate limiting (prevent API abuse)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api {
    limit_req zone=api_limit burst=20 nodelay;
    # ... rest of config
}
```

**4. HTTPS enforcement:**

All nginx configs already redirect HTTP → HTTPS (return 301).

---

## Part 5: Monitoring & Maintenance

### Step 5.1: Set Up Logging

**1. Backend logs:**
```bash
# View real-time logs
sudo journalctl -u sporttrader-backend -f

# View last 100 lines
sudo journalctl -u sporttrader-backend -n 100

# View logs from today
sudo journalctl -u sporttrader-backend --since today
```

**2. nginx logs:**
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

**3. Rotate logs (prevent disk full):**

Edit `/etc/logrotate.d/sporttrader`:
```
/var/log/sporttrader/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 username username
}
```

### Step 5.2: Performance Monitoring

**1. Install monitoring tools:**
```bash
sudo apt install htop iotop nethogs
```

**2. Monitor system resources:**
```bash
htop  # CPU, RAM usage
iotop  # Disk I/O
nethogs  # Network usage
```

**3. Set up uptime monitoring:**

Use services like:
- **UptimeRobot** (free, checks every 5 min)
- **Pingdom**
- **StatusCake**

Configure alerts for:
- Website downtime (https://sporttrader.io)
- API downtime (https://api.sporttrader.io/api/alerts/all)
- WebSocket downtime (wss://api.sporttrader.io/ws)

### Step 5.3: Backup Strategy

**1. Database backups (if using PostgreSQL):**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump arbdb > /home/username/backups/arbdb_$DATE.sql
find /home/username/backups -name "*.sql" -mtime +30 -delete  # Keep 30 days
```

**2. Code backups:**
```bash
# Push to Git repository daily
cd /home/username/sporttrader-backend
git add .
git commit -m "Daily backup $(date)"
git push origin main
```

**3. Automated backup script:**

Create `/home/username/backup.sh`:
```bash
#!/bin/bash
# Backup database
pg_dump arbdb > /home/username/backups/arbdb_$(date +%Y%m%d).sql

# Backup uploaded files
tar -czf /home/username/backups/files_$(date +%Y%m%d).tar.gz /home/username/sporttrader-frontend

# Upload to remote storage (AWS S3, Google Drive, etc.)
# aws s3 cp /home/username/backups/ s3://my-backup-bucket/ --recursive
```

Add to crontab:
```bash
crontab -e
# Add line:
0 2 * * * /home/username/backup.sh  # Run daily at 2 AM
```

---

## Part 6: Deployment Verification

### Step 6.1: Test Production Backend

```bash
# Test API endpoint
curl https://api.sporttrader.io/api/alerts/all

# Test WebSocket (using wscat)
npm install -g wscat
wscat -c wss://api.sporttrader.io/ws
# Should connect and show: [ARB] WebSocket connected
```

### Step 6.2: Test Production Frontend

1. Visit https://sporttrader.io
2. Check browser console for errors
3. Navigate to /alerts page
4. Verify arbitrage opportunities load
5. Check WebSocket connection status

### Step 6.3: Test Production Extension

1. Update extension files with production URLs
2. Load extension in Chrome (chrome://extensions/)
3. Click extension icon → Should show "Connected" status
4. Verify opportunities load in popup
5. Test clicking an opportunity → Should open sportsbook tabs
6. Test auto-fill on a sportsbook (if logged in)

---

## Part 7: Post-Deployment Tasks

### Step 7.1: DNS Configuration

Ensure DNS records point to Hostinger server:

```
A record:     sporttrader.io        →  your-hostinger-ip
A record:     www.sporttrader.io    →  your-hostinger-ip
A record:     api.sporttrader.io    →  your-hostinger-ip
```

Check DNS propagation:
```bash
nslookup sporttrader.io
nslookup api.sporttrader.io
```

### Step 7.2: SSL Certificate Auto-Renewal

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for auto-renewal
sudo crontab -e
# Add line:
0 0 1 * * certbot renew --quiet && systemctl reload nginx
```

### Step 7.3: Update Documentation

Update README.md with production URLs:
```markdown
# ARB Auto Bettor™

**Production Website**: https://sporttrader.io
**API Endpoint**: https://api.sporttrader.io
**WebSocket**: wss://api.sporttrader.io/ws
**Chrome Extension**: https://sporttrader.io/extension
```

---

## Troubleshooting Production Issues

### Issue 1: WebSocket Not Connecting

**Symptoms:** Extension shows "Disconnected", console errors

**Solutions:**
1. Check nginx WebSocket config (Upgrade header, Connection header)
2. Verify SSL certificate valid: `sudo certbot certificates`
3. Check backend service running: `sudo systemctl status sporttrader-backend`
4. Review nginx logs: `sudo tail -f /var/log/nginx/error.log`
5. Test WebSocket with wscat: `wscat -c wss://api.sporttrader.io/ws`

### Issue 2: CORS Errors

**Symptoms:** Browser console shows "CORS policy blocked"

**Solutions:**
1. Verify `allow_origins` in `main.py` includes production domain
2. Check nginx headers configured correctly
3. Ensure `allow_credentials=True` if using cookies
4. Restart backend service: `sudo systemctl restart sporttrader-backend`

### Issue 3: 502 Bad Gateway

**Symptoms:** API requests return 502 error

**Solutions:**
1. Check backend service: `sudo systemctl status sporttrader-backend`
2. Check backend logs: `sudo journalctl -u sporttrader-backend -n 50`
3. Verify backend listening on port 8000: `netstat -tuln | grep 8000`
4. Check nginx proxy_pass config points to correct port
5. Restart services:
```bash
sudo systemctl restart sporttrader-backend
sudo systemctl reload nginx
```

### Issue 4: Static Files Not Loading (Frontend)

**Symptoms:** Website shows but CSS/JS missing, blank page

**Solutions:**
1. Check nginx root directory correct: `/home/username/sporttrader-frontend`
2. Verify files uploaded: `ls -la /home/username/sporttrader-frontend`
3. Check file permissions: `chmod -R 755 /home/username/sporttrader-frontend`
4. Review nginx error log: `sudo tail -f /var/log/nginx/error.log`
5. Clear browser cache and hard refresh (Ctrl+Shift+R)

---

## Performance Optimization

### 1. Enable Caching

Edit nginx config:
```nginx
# Cache API responses (5 minutes)
location /api/alerts/all {
    proxy_pass http://127.0.0.1:8000;
    proxy_cache_valid 200 5m;
    add_header X-Cache-Status $upstream_cache_status;
}
```

### 2. Use CDN for Static Assets

Upload `dist/assets/` to Cloudflare or AWS CloudFront, update `index.html` references.

### 3. Database Indexing

If using PostgreSQL for storing opportunities:
```sql
CREATE INDEX idx_profit ON arbitrage_opportunities (profit_percentage DESC);
CREATE INDEX idx_commence_time ON arbitrage_opportunities (commence_time);
```

### 4. Backend Worker Processes

Increase uvicorn workers in systemd service:
```ini
ExecStart=/home/username/sporttrader-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Cost Estimation (Hostinger)

**Hosting:**
- VPS Plan: $4-12/month (2-4 GB RAM, 2-4 CPU cores)
- Domain: $10-15/year
- SSL: Free (Let's Encrypt)

**APIs:**
- Odds API: $0-100/month (depends on usage)

**Total:** ~$15-30/month

---

## Launch Checklist

Final checklist before going live:

- [ ] Backend deployed and running as system service
- [ ] Frontend built and deployed with nginx
- [ ] Chrome extension updated with production URLs
- [ ] DNS records configured correctly
- [ ] SSL certificates installed and auto-renewing
- [ ] CORS configured for production domain
- [ ] WebSocket working over wss://
- [ ] nginx reverse proxy configured
- [ ] Firewall rules in place
- [ ] Monitoring and logging set up
- [ ] Backup strategy implemented
- [ ] All production tests passing
- [ ] Documentation updated with production URLs
- [ ] Extension tested with live opportunities

---

**Version**: 1.0.0
**Last Updated**: October 17, 2025
**Deployment Target**: Hostinger VPS
**Estimated Deployment Time**: 2-4 hours

**Good luck with your production deployment tomorrow!**
