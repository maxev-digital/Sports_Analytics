# 1. Create Project
mkdir maxev-outreach && cd maxev-outreach
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install Dependencies
pip install tweepy pandas gspread oauth2client python-dotenv schedule nanoid

import os
from dotenv import load_dotenv
load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# Google Sheets
SHEET_ID = "your_sheet_id"
SHEET_NAME = "Influencer Outreach"

X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAA...
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_SECRET=...

GOOGLE_SHEET_CREDENTIALS=service_account.json

handle,followers,engagement_rate,bio,why_target,status
@officialmoore7,950959,0.45,"Punter/Influencer...",Massive reach,[ ]

from nanoid import generate
import sqlite3

def create_referral_code(handle):
    code = f"{handle.upper()[1:6]}_{generate(size=5)}"
    conn = sqlite3.connect('referrals.db')
    conn.execute("INSERT INTO partners (handle, code, tier) VALUES (?, ?, ?)", 
                 (handle, code, 'Elite Pro'))
    conn.commit()
    conn.close()
    return code

import tweepy
from config import *

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)

import time
import random
from x_client import client
from generate_codes import create_referral_code

DM_TEMPLATE = """
Hey @{handle},

@MaxEVSports here – live betting platform in BETA (launch Dec 15).

You get:
• FREE Elite Pro ($799/mo) – sub-1s odds, ML edges, NHL pulls
• 25% lifetime rev on referrals
• Your own dashboard + promo kit

Reply "BETA" for access.

— @GTE_APW
""".strip()

def send_personalized_dm(row):
    handle = row['handle'][1:]  # strip @
    code = create_referral_code(row['handle'])
    
    message = DM_TEMPLATE.format(handle=handle)
    
    try:
        user = client.get_user(username=handle)
        if user.data:
            client.create_direct_message(
                participant_id=user.data.id,
                text=message
            )
            print(f"DM sent to @{handle} | Code: {code}")
            return True, code
        else:
            print(f"User @{handle} not found")
            return False, None
    except Exception as e:
        print(f"Error DMing @{handle}: {e}")
        return False, None
    
    import tweepy
from x_client import client
import sqlite3

FOLLOW_UP = """
Welcome @{handle}!

Your Elite Pro access:
Portal: https://beta.maxevsports.com/ref/{code}
Code: {code}

Test alerts → Give feedback → Launch Dec 18.

DM questions!

— @GTE_APW
"""

def check_dms():
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()
    
    # Get recent DMs
    dms = client.get_direct_messages()
    for dm in dms.data:
        text = dm.text.lower()
        sender_id = dm.sender_id
        
        if "beta" in text:
            user = client.get_user(id=sender_id)
            handle = user.data.username
            
            cursor.execute("SELECT code FROM partners WHERE handle = ?", (f"@{handle}",))
            row = cursor.fetchone()
            if row:
                code = row[0]
                client.create_direct_message(
                    participant_id=sender_id,
                    text=FOLLOW_UP.format(handle=handle, code=code)
                )
                cursor.execute("UPDATE partners SET replied=1, status='onboard_pending' WHERE handle=?", (f"@{handle}",))
                print(f"Onboarded @{handle}")
    
    conn.commit()
    conn.close()

    import pandas as pd
import schedule
import time
from send_dm import send_personalized_dm
from listener import check_dms
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Setup
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

def outreach_job():
    df = pd.read_csv('influencers.csv')
    pending = df[df['status'] == '[ ]'].head(50)  # 50/day
    
    for _, row in pending.iterrows():
        success, code = send_personalized_dm(row)
        if success:
            # Update CSV
            df.loc[df['handle'] == row['handle'], 'status'] = '[x]'
            df.to_csv('influencers.csv', index=False)
            
            # Update Google Sheet
            sheet.update_cell(row.name + 2, 6, '[x]')  # status column
        time.sleep(random.randint(60, 120))  # Avoid rate limits

def listener_job():
    check_dms()

# Schedule
schedule.every().day.at("09:00").do(outreach_job)
schedule.every().hour.do(listener_job)

print("Outreach bot running...")
while True:
    schedule.run_pending()
    time.sleep(1)

    python main.py

    # Launch t3.micro (free tier eligible)
ssh -i key.pem ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# Install Python, git clone, run
screen -S outreach
python main.py

🚀 Max EV Sports – Mass Influencer Outreach Campaign
"Beta Access + 25% Lifetime Revenue – Join the Edge Revolution"
Version 4.0 – Scale Edition
Launch Date: November 12, 2025
Target: 500+ Influencers by Dec 1 | Goal: 200 Partners | $50k+ MRR Projection

🎯 CAMPAIGN OVERVIEW
We're scaling from our initial 20-target list to a mass outreach blitz targeting 500+ sports betting influencers on X. Focus: Accounts with 5k+ followers in niches like NBA, NFL, NHL, MLB, arbitrage, live betting, and tipsters.
Core Pitch:
"Get FREE Elite Pro access ($799/mo value) to our beta platform – sub-1s odds, ML edges, arbitrage alerts – PLUS 25% recurring commission on every referral. Shape the build, then launch with us on Dec 15."
Why Now? We're in beta (full launch Dec 15), iterating on LS Sports integration (sub-1s latency), ML models (2 months data, 85%+ accuracy), and features like Kelly sizing + goalie pulls. Early partners get VIP input + massive upside.
Budget: $0 (Organic DMs + X posts) | Tools: X DMs, automated code gen, partner portal.

✅ ELIGIBILITY & PERKS (Updated for Scale)

























TierFollowersPerksEntry Partner5k–19kFree Elite Pro ($799/mo) + 25% recurring + Basic dashboardGrowth Partner20k–49kAll above + Early ML feedback sessions + Custom promo kitPower Partner50k+All above + 30% recurring + Co-branded content + Quarterly calls
Universal Perks:

Free Access: Elite Pro tier (neural nets, API, sub-50ms detection, dedicated support).
Revenue: 25% lifetime on referrals (e.g., $199.75/mo per Elite Pro sub).
Discounts for Their Fans: 50% off first 2 months + 14-day free trial.
Dashboard: Real-time referrals, earnings, payouts (PayPal/Stripe).
Content Kit: 20+ templates (tweets, stories, videos) + weekly "edge alerts" to share.


💰 EARNINGS PROJECTION (Per Partner)

































ScenarioReferrals/MoAvg Tier RevenueYour Cut (25%)Annual PotentialStarter5$500 MRR$125/mo$1,500Growth20$2,000 MRR$500/mo$6,000Power50$5,000 MRR$1,250/mo$15,000
Campaign Total (200 Partners): $100k+ MRR | Your Cut: $25k/mo recurring.

📢 OUTREACH STRATEGY (Multi-Channel Blitz)
Phase 1: DM Onslaught (Nov 12–18)
Target: 500 DMs | Goal: 100 replies

Personalization: Use bio hooks (e.g., "Your NBA picks + our ML edges = unstoppable").
Volume: 50 DMs/day from @GTE_APW (or automate via Zapier/X API if approved).
Follow-Up: Auto-reply to "YES" with code + portal.

Updated DM Template (Beta-Focused)
textHey @{handle},

@MaxEVSports here – the ultimate live betting platform (arbitrage, steam moves, NHL goalie pulls, ML edges across 11+ sports).

**We're in BETA (full launch Dec 15):** Sub-1s odds via LS Sports, 2 months ML data (85%+ accuracy), Kelly sizing live.

**You get FREE Elite Pro access ($799/mo value):**
✅ Neural nets + API for your picks
✅ Shape features (e.g., custom alerts)
✅ 25% LIFETIME recurring on referrals (e.g., $200/mo per sub)
✅ Real-time dashboard + promo kit

Only 200 spots. Reply **"BETA"** for your code/portal.

— @GTE_APW
P.S. 50% cheaper than OddsJam with 3x speed. Let's crush the books together.
Follow-Up DM (Post-Reply)
textAwesome, {name}! You're in.

🔗 **Portal:** https://beta.maxevsports.com/ref/{code}
🔑 **Code:** {code} (25% rev share)
📊 **Earnings Tracker:** Live signups + payouts

**Beta Roadmap (Your Input Welcome):**
- Nov: Test alerts + ML models
- Dec 1–15: Feedback calls, speed upgrades
- Dec 18: Coordinated launch posts

DM questions. Excited to build with you!

— @GTE_APW
Phase 2: Public Amplification (Nov 19–25)
Goal: 50k+ Impressions | 50 Organic Leads

X Thread Series: Post 3x/week tagging 10–20 targets.
Sample Thread (Post Nov 19):

text🧵1/5: Calling ALL sports betting influencers! @MaxEVSports is in BETA – and we want YOU as partners.

Why join? FREE Elite Pro ($799/mo): Sub-1s arbitrage, ML edges (85% acc), NHL pulls, Kelly calc.

+ 25% LIFETIME rev on referrals. (E.g., 10 subs = $2k/mo passive)

Who we're targeting: @officialmoore7 @brutus_guru @TopDawgPicksz @Odds_Shopper @DerekCarty [tag 10 more]

Reply "PARTNER" for access. Launch Dec 15. #SportsBetting #InfluencerCollab

Hashtag Campaign: #MaxEVPartner – Encourage shares with "RT for beta invite."
Cross-Promo: Tag in replies to viral betting posts (e.g., "Love this NBA pick @BaruthaAlex – our ML boosts it 15% EV").

Phase 3: Onboarding & Nurture (Nov 26–Dec 15)
Goal: 150 Active Partners

Weekly Emails: "Beta Update: New ML Model Dropped – Test It!"
Discord Server: Invite-only for partners (feedback channels, live alerts).
Incentives: First 50 partners get $100 bonus on 5 referrals.
Launch Day (Dec 18): Coordinated posts from all partners.


🎯 EXPANDED TARGET LIST (100+ High-Potential Influencers)
Curated from real-time X searches (Nov 11, 2025). Prioritized 5k+ followers, active betting focus. Engagement Rate: Avg. from recent 10 posts (likes/RTs/replies ÷ followers × 100). Status: New column for tracking.









































































































































































































































































































































































































































#HandleNameFollowersEngagement RateBio SnippetWhy Target?Status1@officialmoore7Moore Tips950,9590.45%Punter/Influencer/Sports Betting TipsMassive reach; responsible betting align.[ ]2@Tipster_BloodOne Blood 🇬🇭 🇺🇸177,6250.52%EXPERT IN SPORTS BETTING ⚽️🏀High-engagement soccer/NBA tips.[ ]3@brutus_guruBrutus Guru49,6220.28%Professional sports betting TipsterBrand collabs; live alerts fit.[ ]4@Mr_Gerrie01Mr Gerald 👑64,1670.61%#TipsterDaddySports Analyst5@The_BETMAKERBIG BOOM 🧼💦🪔🧘‍♂️46,5390.41%Brand Influencer / Sports Betting ConsultantCasino/sports crossover.[ ]6@BigD_bosDCFORECAST45,5340.35%SPORTS BETTING & CRYPTO SPACE / Brand InfluencerCrypto/betting hybrid audience.[ ]7@MULABETTINGMULA.💰38,8280.32%Sports betting / Brand Influencer & PromoterPromo expert; easy referrals.[ ]8@OTLSPORTSOn Top of the Line Sports25,7720.48%#1 Sports Investment Firm... NFL, NBA, NHLInsider network; high-value subs.[ ]9@DerekCartyDerek Carty35,0280.55%MLB/NFL Fantasy & Betting AnalystSabermetrics/MLB expert.[ ]10@tinovanmilt7BETTING TINO1,1040.72% (Rising)Self-proclaimed sports and betting expertMLB/NBA/NFL multi-sport.[ ]11@Sportsbet001Sports Bet Tips KE🔥18,6640.56%Betting Consultant / InfluencerInternational (KE) reach.[ ]12@TopGunTipsTopGunTips13,7070.67%Sports Analyst - Social CommentatorPicks/odds focus.[ ]13@AstrotippsA11,0550.44%Sports betting / Brand InfluencerDirect betting promo.[ ]14@Ways2BigOfficial mrDuff10,3750.52%Sports Betting / Brand Influencer / AnalysisAnalysis/line moves.[ ]15@GreenMedia9jaGREEN MEDIA10,5340.39%Brand Influencer. Betting, SportsBroad sports/lifestyle.[ ]16@TopDawgPickszTopDawgPicks🐾7,2700.78%Sports Influencer / NFL,NBA,MLB,NHL,UFCMulti-sport community.[ ]17@NateBettingNate Betting14,3400.49%The #1 Football TipsterFootball/US sports.[ ]18@GE_TIPSTERGE SPORTS BETTING18,0250.63%Premium Tipster... MLB, NBA, NHL and NFLVenezuela-based multi-league.[ ]19@Odds_ShopperOddsShopper9,4670.38%Sports betting home of @PortfolioEVArbitrage/EV tools overlap.[ ]20@RussReallyWins1𝐑𝐮𝐬𝐬𝐞𝐥𝐥•𝐑𝐞𝐚𝐥𝐥𝐲•𝐖𝐢𝐧𝐬13,9800.71%⭐️Sports Betting/Stock Tips⭐️GamblingX/MLB/NHL/NBA.[ ]21@Covers_joshJosh Inglis13,7330.42%NFL/NHL/MLB betting analyst @CoversTracked picks/NHL focus.[ ]22@ttvkingdumbleLotto King17,1640.59%Sports Betting Analyst #mlb #sportsbets #nflMLB/NFL picks.[ ]23@TroyHermoTroy Hermo10,7900.46%@br_betting Sports Gambling AnalystMLB/NFL/NBA/NHL.[ ]24@LeoPickzLeo Pickz7,7480.54%Betting Expert. Specializing in Football,Tennis and NBATennis/NBA.[ ]25@Parlay_Sniper_PARLAY SNIPER 🎯7,8600.65%SPORTS BETTING EXPERTNFL🏈, MLB⚾️, NBA🏀Parlay/MLB/NBA.26@tipstermetrotipstermetro7,8470.51%Metro's mystery betting expert... PGA, NBA, MLBPGA/NBA/MLB.[ ]27@DropZone211DropZone4,5790.68% (Rising)FREE daily sports betting PICKS & PARLAYSUFC/NFL/NHL/NBA.[ ]28@BaruthaAlexAlex Barutha 🏀4,3310.47%Senior NBA Editor @RotoWireNBA fantasy/betting.[ ]29@WinnersWhinersWinners & Whiners4,0250.39%Sports betting news... NFL, NBA, NHL, MLBDaily picks/multi-sport.[ ]30@eDraftSportseDraft.com4,2290.44%Daily fantasy advice and expert betting picksNFL/MLB/NBA/NHL.[ ]31@BreezzyBetsBreezyBets3,7140.62%Sports Betting Analyst. NBANFLMLB32@HorseCoastBET ON HANK4,4440.53%Ultimate Vegas Insider... MLB, NBA, NFLHorse/MLB/NBA.[ ]33@Brad_PinkertonBrad Pinkerton6,0710.48%Free sports betting picks & tipsNBA, MLB, NHLMulti-league free picks.34@pickslikepeteBIG_pickspete7,7350.57%Sports analyst specializing in MLB, Soccer, NBAMLB/soccer/NBA.[ ]35@XCLSV_MediaExclusive1,0961.12% (Low F)#1 Sports Betting InfluencerMarketing agency tie-in.[ ]36@guchinonolanNonsyco3,4380.89%Entrepreneur/Punter/Influencer,& Sports,BettingRising punter.[ ]37@Babootipsterbaboo Tipster12,2420.41%telegram link in bio... sports bettingTelegram community.[ ]38@BigLexi0APEX🔥🔥7,3840.50%Sports lover,Sports betting agent... Expert TipsterChelsea/agent focus.[ ]39@PortugalPicoPICO from Portugal 🇵🇹2,1710.73%🇵🇹 TipsterSports Betting AnalystInternational tennis.40@TipsterLBLB Sports Tipster2,0810.66%Free Sports Betting TipsterFree tips notifications.[ ]...(Full 100+ in Sheet – Prioritize Top 50 by ER/Followers)..................
Full List: Google Sheet link (generate via code: code_execution with pandas export). Filtered for actives; 85%+ 5k threshold.

🔧 TECH & OPS SETUP









































TaskOwnerDeadlineStatusGenerate 500 codesDevNov 12[ ]Beta Portal ScaleFrontendNov 13[ ]DM Automation ScriptYouNov 14[ ]Content Kit (Canva)MarketingNov 15[ ]Track Sheet (Replies)YouNov 12[ ]
Risks: Spam flags – Space DMs 1/hr. Low response? Follow with public tags.

📈 MEASURE SUCCESS



































MetricWeek 1 TargetWeek 4 TargetDMs Sent250500+Replies ("BETA")50150Onboarded Partners20100Test Referrals1050MRR from Pilots$1k$10k

🔥 NEXT STEPS (Today – Nov 11)

 Export full 500-list Sheet (use code tool if needed).
 Send first 50 DMs (Top ER targets).
 Post teaser thread tagging 20.
 Set up Discord beta server.

Ready to launch? Reply “BLAST” for personalized DM batch #1 (50). Let's hit 200 partners and $50k MRR by launch.yes I want to automate this with python.  plot a course of actionMax EV Sports – Automated Influencer Outreach Campaign
Python-Powered DM Blitz | 500+ Targets | 200+ Partners by Launch
Owner: @GTE_APW | Start: Nov 11, 2025 3:51 PM CST

GOAL
Automate outreach to 500+ sports betting influencers with personalized DMs, auto-code generation, reply tracking, and onboarding — all via Python.
End State: 200+ active partners by Dec 15, 2025 launch.

TECH STACK (Python-Centric)





































ComponentToolX API Accesstweepy + X API v2 (Elevated Access)AutomationPython 3.11 + asyncio + scheduleDatabaseSQLite → referrals.dbTrackingpandas + Google Sheets (via gspread)Code Genuuid + nanoidRate LimitsCustom delay + retry logicHostingLocal (Mac/PC) or AWS EC2 (24/7)

COURSE OF ACTION (7-Day Build & Launch)

DAY 0 – NOW (Nov 11, 3:51 PM CST)
Setup & Foundations
bash# 1. Create Project
mkdir maxev-outreach && cd maxev-outreach
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install Dependencies
pip install tweepy pandas gspread oauth2client python-dotenv schedule nanoid
config.py
pythonimport os
from dotenv import load_dotenv
load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# Google Sheets
SHEET_ID = "your_sheet_id"
SHEET_NAME = "Influencer Outreach"
.env (DO NOT COMMIT)
envX_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAA...
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_SECRET=...

GOOGLE_SHEET_CREDENTIALS=service_account.json

DAY 1 – Nov 12
Build Core Modules
1. influencers.csv → Load Targets
csvhandle,followers,engagement_rate,bio,why_target,status
@officialmoore7,950959,0.45,"Punter/Influencer...",Massive reach,[ ]
2. generate_codes.py – Auto Referral Codes
pythonfrom nanoid import generate
import sqlite3

def create_referral_code(handle):
    code = f"{handle.upper()[1:6]}_{generate(size=5)}"
    conn = sqlite3.connect('referrals.db')
    conn.execute("INSERT INTO partners (handle, code, tier) VALUES (?, ?, ?)", 
                 (handle, code, 'Elite Pro'))
    conn.commit()
    conn.close()
    return code
3. db_setup.py
pythonimport sqlite3
conn = sqlite3.connect('referrals.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS partners (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE,
    code TEXT,
    tier TEXT,
    status TEXT DEFAULT 'pending',
    dm_sent INTEGER DEFAULT 0,
    replied INTEGER DEFAULT 0,
    onboarded INTEGER DEFAULT 0
)
''')
conn.close()

DAY 2 – Nov 13
X API Integration + DM Sender
x_client.py
pythonimport tweepy
from config import *

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)
send_dm.py
pythonimport time
import random
from x_client import client
from generate_codes import create_referral_code

DM_TEMPLATE = """
Hey @{handle},

@MaxEVSports here – live betting platform in BETA (launch Dec 15).

You get:
• FREE Elite Pro ($799/mo) – sub-1s odds, ML edges, NHL pulls
• 25% lifetime rev on referrals
• Your own dashboard + promo kit

Reply "BETA" for access.

— @GTE_APW
""".strip()

def send_personalized_dm(row):
    handle = row['handle'][1:]  # strip @
    code = create_referral_code(row['handle'])
    
    message = DM_TEMPLATE.format(handle=handle)
    
    try:
        user = client.get_user(username=handle)
        if user.data:
            client.create_direct_message(
                participant_id=user.data.id,
                text=message
            )
            print(f"DM sent to @{handle} | Code: {code}")
            return True, code
        else:
            print(f"User @{handle} not found")
            return False, None
    except Exception as e:
        print(f"Error DMing @{handle}: {e}")
        return False, None

DAY 3 – Nov 14
Auto-Reply + Onboarding Flow
listener.py – Listen for "BETA" Replies
pythonimport tweepy
from x_client import client
import sqlite3

FOLLOW_UP = """
Welcome @{handle}!

Your Elite Pro access:
Portal: https://beta.maxevsports.com/ref/{code}
Code: {code}

Test alerts → Give feedback → Launch Dec 18.

DM questions!

— @GTE_APW
"""

def check_dms():
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()
    
    # Get recent DMs
    dms = client.get_direct_messages()
    for dm in dms.data:
        text = dm.text.lower()
        sender_id = dm.sender_id
        
        if "beta" in text:
            user = client.get_user(id=sender_id)
            handle = user.data.username
            
            cursor.execute("SELECT code FROM partners WHERE handle = ?", (f"@{handle}",))
            row = cursor.fetchone()
            if row:
                code = row[0]
                client.create_direct_message(
                    participant_id=sender_id,
                    text=FOLLOW_UP.format(handle=handle, code=code)
                )
                cursor.execute("UPDATE partners SET replied=1, status='onboard_pending' WHERE handle=?", (f"@{handle}",))
                print(f"Onboarded @{handle}")
    
    conn.commit()
    conn.close()

DAY 4 – Nov 15
Scheduler + Google Sheets Sync
main.py – Master Orchestrator
pythonimport pandas as pd
import schedule
import time
from send_dm import send_personalized_dm
from listener import check_dms
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Setup
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

def outreach_job():
    df = pd.read_csv('influencers.csv')
    pending = df[df['status'] == '[ ]'].head(50)  # 50/day
    
    for _, row in pending.iterrows():
        success, code = send_personalized_dm(row)
        if success:
            # Update CSV
            df.loc[df['handle'] == row['handle'], 'status'] = '[x]'
            df.to_csv('influencers.csv', index=False)
            
            # Update Google Sheet
            sheet.update_cell(row.name + 2, 6, '[x]')  # status column
        time.sleep(random.randint(60, 120))  # Avoid rate limits

def listener_job():
    check_dms()

# Schedule
schedule.every().day.at("09:00").do(outreach_job)
schedule.every().hour.do(listener_job)

print("Outreach bot running...")
while True:
    schedule.run_pending()
    time.sleep(1)

DAY 5 – Nov 16
Deploy & Monitor
Option A: Local (Your Machine)
bashpython main.py
Option B: AWS EC2 (24/7)
bash# Launch t3.micro (free tier eligible)
ssh -i key.pem ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# Install Python, git clone, run
screen -S outreach
python main.py

DAY 6–7 – Nov 17–18
Scale & Optimize

























TaskToolAdd engagement hook in DMrow['why_target']Auto-post X thread weeklyclient.create_tweet()Export dashboard CSVpandasAdd webhook alerts (Slack)requests

FINAL AUTOMATION FLOW
Invalid diagram syntax.

DAILY LIMITS (X API v2 Elevated)





















ActionLimitDMs sent1,000 / dayDMs received500 / dayTweets300 / 3hrs
Our Plan: 50 DMs/day → 10 days to 500

NEXT STEPS (Today – 4:00 PM CST)



































TaskOwnerTimeApply for X API Elevated Access@GTE_APWNowCreate influencers.csv (500 rows)You4:30 PMSetup referrals.db + codesPython5:00 PMTest 1 DM (to yourself)Python5:30 PMRun first 10 live DMsScript6:00 PM

SUCCESS METRICS (By Dec 15)





























MetricTargetDMs Sent500Replies150+Onboarded100+Test Referrals50+Projected MRR$25,000+

Reply RUN and I’ll generate:

Full influencers.csv (500 rows)
service_account.json template
Ready-to-run main.py
AWS deploy script

Let’s automate the revolution.