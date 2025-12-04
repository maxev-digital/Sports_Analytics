# X Campaign - Automated Influencer Outreach

Automated DM campaign for Max EV Sports partner program targeting 500+ sports betting influencers.

## Status: Ready to Launch

**Prerequisites:**
1. ✅ Database infrastructure built
2. ✅ DM automation scripts ready
3. ⏳ X API Elevated Access (apply at https://developer.x.com/en/portal/dashboard)
4. ⏳ Google service account JSON (for Sheets tracking)
5. ⏳ Influencer CSV list (500+ targets)

## Quick Start

### 1. Install Dependencies

```bash
cd backend/x_campaign
pip install -r requirements.txt
```

### 2. Setup Database

```bash
python -m backend.x_campaign.db_setup
```

This creates `referrals.db` with tables for:
- Partners tracking
- DM log
- Referrals
- Campaign stats

### 3. Import Influencers

Create `influencers.csv`:
```csv
handle,followers,niche,why_target,engagement_rate
@BenMoore_Sports,50000,nba,High NBA engagement,4.5
@SharpBettor,30000,betting,Sharp betting content,3.8
```

Import:
```bash
python -m backend.x_campaign.import_influencers influencers.csv
```

### 4. Configure API Credentials

Add to `backend/.env`:
```env
# X API (Full Access for DM Campaign)
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_secret_here

# Google Sheets (already configured)
GOOGLE_SHEETS_CREDENTIALS=google_sheets/credentials/service-account-key.json
GOOGLE_SHEETS_SHEET_ID=1bFNPXj2wOOBid8d-dnHbKmSs5U90a66X29-PFRmkgvo
```

### 5. Test Campaign

Run in test mode (DRY RUN - no real DMs sent):
```bash
python -m backend.x_campaign.main --test
```

This will:
- Show example DM messages
- Test database queries
- Generate sample report

### 6. Launch Campaign

Start automated scheduler:
```bash
python -m backend.x_campaign.main
```

**Schedule:**
- 9:00 AM CST: Send 50 DMs
- Every 60 min: Check for "BETA" replies, auto-respond
- 11:00 PM CST: Generate daily report

## Manual Operations

### Send DMs Manually

Dry run (preview only):
```bash
python -m backend.x_campaign.send_dm
```

Live send (real DMs):
```bash
python -m backend.x_campaign.send_dm --live
```

Custom batch size:
```bash
python -m backend.x_campaign.send_dm --live --batch 20
```

### Check for Replies

One-time check:
```bash
python -m backend.x_campaign.listener
```

Continuous monitoring:
```bash
python -m backend.x_campaign.listener --monitor --interval 30
```

### View Stats

```bash
python -m backend.x_campaign.db_setup
```

## Project Structure

```
backend/x_campaign/
├── __init__.py              # Package init
├── config.py                # Load env vars, DM templates
├── db_setup.py              # Database schema + operations
├── generate_codes.py        # Referral code generator
├── x_client.py              # X API wrapper (Tweepy)
├── send_dm.py               # DM sender with rate limiting
├── listener.py              # Reply monitor + auto-response
├── main.py                  # Master scheduler
├── import_influencers.py    # CSV import tool
├── requirements.txt         # Python dependencies
├── referrals.db             # SQLite database (created on first run)
└── README.md                # This file
```

## Campaign Flow

1. **Import Influencers** - Load 500+ targets from CSV
2. **Daily Send** - 50 DMs/day at 9am CST (personalized)
3. **Monitor Replies** - Check hourly for "BETA" keyword
4. **Auto-Onboard** - Generate code, send portal link
5. **Track Performance** - Database + Google Sheets

## DM Templates

### Initial Outreach
```
Hey {handle}! 👋

I'm with Max EV Sports - we just launched a sports betting analytics platform...

Interested? Reply "BETA" and I'll send your partner code + portal link.
```

### Auto-Reply (when they say "BETA")
```
Welcome to the Max EV Sports partner program! 🎉

Your Details:
• Referral Code: {code}
• Commission: 25% recurring
• Partner Portal: https://beta.maxevsports.com/ref/{code}
```

## Rate Limiting

- **DMs per day:** 50 (max 1,000 per X API)
- **Delay between DMs:** 2 minutes
- **Reply checks:** Every 60 minutes
- **Total send time:** ~100 minutes (50 DMs × 2 min)

## Expected Results

**Week 1 (Nov 15-21):**
- 250 DMs sent
- 50 replies (20% response rate)
- 25 onboarded partners

**Week 2 (Nov 22-28):**
- 500 total DMs sent
- 100 replies
- 50 onboarded partners

**Launch Day (Dec 15):**
- Target: 150+ active partners
- Projected: 50-75 paid referrals
- MRR: $10k-$15k

## Troubleshooting

### "Missing X API credentials"
- Apply for X API Elevated Access
- Generate API keys in Developer Portal
- Add to backend/.env

### "Cannot send DM - user may have DMs disabled"
- Normal - skip this user
- ~10-15% of users have DMs disabled

### "Rate limit exceeded"
- Wait 15 minutes
- Reduce DAILY_DM_LIMIT in config.py

### "Database locked"
- Close other processes using referrals.db
- Check that only one scheduler is running

## Next Steps

See [X_CAMPAIGN_ACTION_PLAN.md](../../X_CAMPAIGN_ACTION_PLAN.md) for:
- X API Elevated Access application
- Google service account setup
- Influencer list creation (Grok's 500+ list)
- Launch timeline

## Support

Questions? Contact:
- Max EV Sports Team
- partnerships@max-ev-sports.com
