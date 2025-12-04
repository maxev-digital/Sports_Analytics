# Max EV Sports - X Campaign Implementation Plan
**Status:** Ready to Launch
**Owner:** @GTE_APW
**Timeline:** Nov 12-18, 2025
**Goal:** 200+ partners by Dec 15, 2025

---

## 📋 PHASE 1: API ACCESS SETUP (Today - Nov 12)

### Step 1: Apply for X API Elevated Access
**Time: 30 minutes**

1. Go to https://developer.x.com/en/portal/dashboard
2. Click "Elevated" access (required for DMs)
3. Fill out application:
   - **Use Case:** "Influencer outreach for sports betting platform partnership program"
   - **Will you make X content available to government entities?** No
   - **Will you display Tweets/X content off X?** No
   - **Describe in your own words what you are building:**
     ```
     Automated partnership outreach system for Max EV Sports (https://max-ev-sports.com).
     We're reaching out to 500+ sports betting influencers to offer them free beta access
     and revenue-sharing partnerships. System will:
     - Send personalized DMs to potential partners
     - Auto-reply to interested influencers with referral codes
     - Track partnerships in database
     - Notify team of new signups

     No spam - targeting qualified influencers only. Rate: 50 DMs/day max.
     ```

4. Submit & wait for approval (usually 1-3 days)

### Step 2: Get Your X API Credentials
**After Elevated Access Approved:**

1. In Developer Portal, go to your App Settings
2. Click "Keys and Tokens"
3. Generate:
   - ✅ API Key & Secret (OAuth 1.0a)
   - ✅ Access Token & Secret
   - ✅ Bearer Token (you already have this)

4. Add to `backend/.env`:
```env
# X API (Full Access for DM Campaign)
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_secret_here
X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAPg1wEAAAAAi6Z60obJKWo6bgcxRcY0KCly6Es%3DNBbSnIrHXjDrWJskX6JHwRTWY0LDec385AtWyEvIeaabhK1moN
```

### Step 3: Setup Google Sheets Service Account
**Time: 15 minutes**

1. Go to https://console.cloud.google.com/
2. Create new service account (or use existing)
3. Download JSON key
4. Save to: `backend/google_sheets/credentials/service-account-key.json`
5. Share target Google Sheet with service account email

---

## 📋 PHASE 2: BUILD CAMPAIGN INFRASTRUCTURE (Nov 13)

### Components to Build:

#### 1. Database Setup
- `backend/x_campaign/db_setup.py` - Create SQLite DB for tracking
- `backend/x_campaign/referrals.db` - Partners, codes, status

#### 2. Code Generation
- `backend/x_campaign/generate_codes.py` - Auto-create referral codes
- Integration with existing `backend/referrals.json`

#### 3. X API Client
- `backend/x_campaign/x_client.py` - Tweepy client setup
- `backend/x_campaign/send_dm.py` - Personalized DM sender
- `backend/x_campaign/listener.py` - Auto-reply to "BETA" responses

#### 4. Orchestration
- `backend/x_campaign/main.py` - Master scheduler
- Runs daily: 50 DMs at 9am CST
- Runs hourly: Check for replies

#### 5. Influencer Data
- `backend/x_campaign/influencers.csv` - 500+ targets
- Source from Grok's list + additional research

---

## 📋 PHASE 3: TESTING (Nov 14)

### Test Checklist:
- [ ] Send test DM to yourself
- [ ] Reply "BETA" and verify auto-response
- [ ] Check code generation (format: `MOORE_abc12`)
- [ ] Verify Google Sheets logging
- [ ] Test rate limiting (1 DM/minute)

---

## 📋 PHASE 4: LAUNCH (Nov 15-18)

### Daily Campaign Flow:
```
9:00 AM CST - Auto-send 50 DMs (batch #1-10 over 10 days)
Every Hour  - Check for "BETA" replies
            - Auto-respond with code + portal link
            - Update tracking sheet
11:00 PM    - Generate daily report
```

### Monitoring:
- Google Sheet: Track DM status, replies, onboardings
- SQLite DB: Store all partner data
- Console logs: Real-time DM sends

---

## 🎯 CURRENT ASSETS

### ✅ Already Built:
1. **Referral System** (`backend/referrals.json`)
   - Active tracking format
   - Commission structure (25% recurring)
   - Subscription tiers

2. **Partner Portal** (assumed from referrals.json)
   - URL: `https://beta.maxevsports.com/ref/{code}`
   - Dashboard for influencers

3. **Google Sheets Integration**
   - Sheet ID: `1bFNPXj2wOOBid8d-dnHbKmSs5U90a66X29-PFRmkgvo`
   - Just need service account file

### 🔨 Need to Build:
1. X Campaign scripts (send_dm.py, listener.py, main.py)
2. Influencers CSV (500+ targets from Grok's list)
3. SQLite tracking DB
4. Scheduler automation

---

## 💰 EXPECTED OUTCOMES

### Week 1 (Nov 15-21):
- 250 DMs sent
- 50 replies expected (20% response rate)
- 25 onboarded partners
- 5-10 test referrals

### Week 2 (Nov 22-28):
- 250 more DMs sent (total: 500)
- 100 total replies
- 50 onboarded partners
- 20-30 test referrals

### Launch Day (Dec 15):
- Target: 150+ active partners
- Projected: 50-75 paid referrals
- MRR: $10k-$15k (month 1)
- Partner payouts: $2.5k-$3.75k (25% commission)

---

## ⚠️ RISK MITIGATION

### X API Rate Limits:
- **DMs:** 1,000/day (we send 50/day = safe)
- **Read DMs:** 500/day (checking hourly = safe)
- **Solution:** Built-in delays (1-2 min between DMs)

### Spam Flags:
- **Risk:** Sending too many similar DMs
- **Solution:**
  - Personalize with `{handle}` and `why_target` field
  - Space DMs 1-2 minutes apart
  - Limit to 50/day max
  - Only DM accounts that follow sports betting topics

### Low Response Rate:
- **Backup:** Post public threads tagging 20 influencers
- **Backup:** Engage with their posts first (reply, like) before DMing

---

## 📊 SUCCESS METRICS

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| X API Access | Elevated | Basic (bearer only) | ⏳ Pending |
| Google Service Account | Active | Missing file | ⏳ Pending |
| Influencer List | 500+ | 0 | 🔨 To Build |
| DMs Sent | 500 | 0 | ⏳ Waiting |
| Replies | 100+ | 0 | ⏳ Waiting |
| Onboarded Partners | 150+ | 1 test | ⏳ Waiting |
| Projected MRR | $25k | $0 | ⏳ Waiting |

---

## 🚀 NEXT IMMEDIATE ACTIONS

1. **Apply for X API Elevated Access** (30 min) ← DO THIS NOW
2. **Download Google Service Account JSON** (15 min)
3. **Create influencers.csv** from Grok's list (30 min)
4. **Build x_campaign scripts** (2-3 hours)
5. **Test with 1 DM to yourself** (10 min)
6. **Launch batch #1: 50 DMs** (automated)

---

## 📁 PROJECT STRUCTURE

```
backend/
├── x_campaign/
│   ├── __init__.py
│   ├── config.py              # Load .env credentials
│   ├── db_setup.py            # Create referrals.db
│   ├── generate_codes.py      # Auto-generate referral codes
│   ├── x_client.py            # Tweepy client
│   ├── send_dm.py             # DM sender with personalization
│   ├── listener.py            # Auto-reply to "BETA"
│   ├── main.py                # Master orchestrator + scheduler
│   ├── influencers.csv        # 500+ targets
│   └── referrals.db           # SQLite tracking DB
├── google_sheets/
│   └── credentials/
│       └── service-account-key.json  # ← NEED THIS
└── .env                       # ← ADD X API KEYS

```

---

**Status:** Ready to implement once X API Elevated Access is approved.
**ETA:** 3-5 days from application to first DM sent.
