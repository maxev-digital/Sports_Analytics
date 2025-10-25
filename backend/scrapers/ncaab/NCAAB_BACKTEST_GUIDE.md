# NCAA Basketball Backtesting - Complete Guide

## 🎯 What Was Built

You now have a **complete backtesting system** that:

1. ✅ Uses historical 2024 season data (if available)
2. ✅ Generates predictions for all historical games
3. ✅ Compares predictions to actual results
4. ✅ Calculates accuracy metrics (MAE, RMSE, etc.)
5. ✅ Uploads results to Google Sheets in a separate "Backtesting" tab

---

## 📁 New Files Created

```
C:\Users\nashr\
├── ncaab_sheets_uploader_enhanced.py    ← Multi-tab Google Sheets uploader
├── run_ncaab_backtest.py                ← Master backtest workflow
└── backend\
    └── data\
        ├── historical\
        │   ├── kenpom_2024_season_*.csv       ← Historical KenPom data
        │   └── game_results_2024_season_*.csv ← Historical game scores
        └── backtesting\
            ├── predictions_*.csv               ← Detailed predictions
            └── metrics_*.csv                   ← Performance metrics
```

---

## 🚀 How to Run the Backtest

### Prerequisites

Make sure you have:
- ✅ Historical KenPom data (2024 season)
- ✅ Historical game results (2024 season)
- ✅ Google Sheets configured
- ✅ Config.py set up

### Step 1: Check if You Have Historical Data

```powershell
cd C:\Users\nashr
dir backend\data\historical\
```

**If you see files like:**
- `kenpom_2024_season_*.csv`
- `game_results_2024_season_*.csv`

**You're ready!** Skip to Step 3.

**If directory is empty**, continue to Step 2.

---

### Step 2: Get Historical Data (if needed)

#### 2A: Get Historical KenPom Data

```powershell
python historical_kenpom_scraper.py
```

**Prompts:**
- Email: gte.apw@gmail.com
- Password: Thewrench1!
- Headless: y
- Year: 2024

**Wait 2-3 minutes** for the scraper to finish.

**Expected Output:**
```
✅ Successfully scraped 364 teams
📈 Tempo range: 59.4 - 75.3
📈 OffEff range: 82.7 - 130.1
💾 Saved: backend/data/historical/kenpom_2024_season_*.csv
```

#### 2B: Get Historical Game Results

```powershell
python game_results_scraper.py
```

**Prompts:**
- Year: 2024

**Wait 5-10 minutes** for the scraper to finish (gets 4,000+ games).

**Expected Output:**
```
✅ Successfully parsed 4,872 complete games
📈 Average total: 141.3
💾 Saved: backend/data/historical/game_results_2024_season_*.csv
```

---

### Step 3: Run the Complete Backtest

```powershell
cd C:\Users\nashr
python run_ncaab_backtest.py
```

**What happens:**

1. **Checks for historical data** (Step 1)
   - Finds KenPom CSV
   - Finds game results CSV

2. **Loads data** (Step 2)
   - Loads 364 teams from KenPom
   - Loads 4,872 games

3. **Runs backtest** (Step 3)
   - Generates prediction for each game
   - Compares to actual result
   - Calculates errors
   - Shows progress: "Progress: 100/4872 predictions..."

4. **Displays metrics** (console output)

5. **Uploads to Google Sheets** (Step 4)
   - Creates "Backtesting" tab
   - Uploads summary metrics
   - Uploads detailed predictions

**Total Time:** 3-5 minutes (depending on number of games)

---

## 📊 Expected Console Output

```
══════════════════════════════════════════════════════════════════════
NCAA BASKETBALL BACKTESTING WORKFLOW
══════════════════════════════════════════════════════════════════════
Started: 2025-10-10 14:23:45

STEP 1: CHECKING HISTORICAL DATA
──────────────────────────────────────────────────────────────────────
✅ Found KenPom data: kenpom_2024_season_20251010_142001.csv
✅ Found game results: game_results_2024_season_20251010_142030.csv

STEP 2: LOADING HISTORICAL DATA
──────────────────────────────────────────────────────────────────────
✅ Loaded 364 teams from KenPom
✅ Loaded 4,872 games

STEP 3: RUNNING BACKTEST
──────────────────────────────────────────────────────────────────────
📊 Loading KenPom data from: backend/data/historical/kenpom_2024_season_*.csv
   ✅ Loaded 364 teams

🔮 Generating predictions for 4,872 games...
   Progress: 100/4872 predictions...
   Progress: 200/4872 predictions...
   ... (continues)
   ✅ Successful predictions: 4,650
   ⚠️  Failed predictions: 222

📈 Calculating metrics for 4,650 games...

══════════════════════════════════════════════════════════════════════
BACKTESTING RESULTS
══════════════════════════════════════════════════════════════════════

📊 Sample Size: 4,650 games
📊 Average Actual Total: 141.3
📊 Average Model Prediction: 142.1

🎯 Accuracy Metrics:
   Mean Absolute Error (MAE): 6.2 points
   Root Mean Squared Error (RMSE): 8.1 points
   Median Absolute Error: 5.1 points

✅ Predictions Within:
   ±3 points: 28.4%
   ±5 points: 46.7%
   ±7 points: 62.3%
   ±10 points: 81.2%

🔄 Prediction Bias:
   Over-predictions: 2,387 (51.3%)
   Under-predictions: 2,263 (48.7%)

══════════════════════════════════════════════════════════════════════

💾 Saved predictions: backend/data/backtesting/predictions_*.csv
💾 Saved metrics: backend/data/backtesting/metrics_*.csv

STEP 4: UPLOADING TO GOOGLE SHEETS
──────────────────────────────────────────────────────────────────────
   ☁️  Connecting to Google Sheets...
   ✅ Connected successfully
   📤 Uploading backtest results to tab: Backtesting
   📝 Creating new tab: Backtesting
   🗑️  Clearing old data...
   📊 Uploading summary...
   📤 Uploading 4,650 prediction details...
      Uploaded rows 25-124
      Uploaded rows 125-224
      ... (continues in batches of 100)
   🎨 Applied backtest formatting
   ✅ Backtest upload complete!

✅ Uploaded to Google Sheets
🔗 View: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID

══════════════════════════════════════════════════════════════════════
✅ BACKTESTING WORKFLOW COMPLETE
Time: 4m 32s
══════════════════════════════════════════════════════════════════════
```

---

## 📋 Google Sheet Structure

After running, your Google Sheet will have **2 tabs**:

### Tab 1: "Predictions" (Your daily predictions)
- Date, Time, Teams
- Tempo, Pace, Efficiency
- Model Total, Market Total, Edge
- Recommendation, Confidence, Bet

### Tab 2: "Backtesting" (NEW - Historical analysis)

**Section 1: Summary Metrics (Rows 1-22)**
```
📊 BACKTESTING RESULTS SUMMARY

Total Games Analyzed:        4,650
Average Actual Total:        141.3
Average Model Prediction:    142.1

🎯 ACCURACY METRICS
Mean Absolute Error (MAE):   6.2 points
Root Mean Squared Error:     8.1 points
Median Absolute Error:       5.1 points

✅ PREDICTIONS WITHIN:
±3 points:                   28.4%
±5 points:                   46.7%
±7 points:                   62.3%
±10 points:                  81.2%

🔄 PREDICTION BIAS
Over-predictions:            2,387 (51.3%)
Under-predictions:           2,263 (48.7%)
```

**Section 2: Detailed Predictions (Rows 24+)**

| Home_Team | Away_Team | Model_Total | Actual_Total | Error | Abs_Error | Home_Tempo | Away_Tempo | Expected_Pace |
|-----------|-----------|-------------|--------------|-------|-----------|------------|------------|---------------|
| Duke      | UNC       | 165.3       | 162.0        | 3.3   | 3.3       | 71.2       | 69.8       | 70.5          |
| Kansas    | Kentucky  | 161.2       | 159.0        | 2.2   | 2.2       | 68.5       | 70.1       | 69.3          |
| ...       | ...       | ...         | ...          | ...   | ...       | ...        | ...        | ...           |

---

## 📈 Interpreting Your Results

### What Good Results Look Like

#### ✅ **Excellent Model (Professional-Level)**
- **MAE:** 4-5 points
- **Within ±5:** 50%+ of games
- **Prediction Bias:** 48-52% (balanced)

#### ✅ **Good Model (Competitive)**
- **MAE:** 5-7 points
- **Within ±5:** 40-50% of games
- **Prediction Bias:** 45-55% (mostly balanced)

#### ⚠️ **Needs Calibration**
- **MAE:** 8+ points
- **Within ±5:** <35% of games
- **Prediction Bias:** <40% or >60% (biased)

---

### Key Metrics Explained

#### **Mean Absolute Error (MAE)**
- **What it is:** Average number of points your predictions are off
- **Industry Standard:** 5-7 points for NCAA Basketball
- **Your Goal:** Under 7 points
- **Example:** MAE of 6.2 = On average, you're 6.2 points off

#### **Root Mean Squared Error (RMSE)**
- **What it is:** Penalizes large errors more than MAE
- **Industry Standard:** 7-9 points
- **Use Case:** Identifies if you have big outliers

#### **Within ±X Points**
- **Within ±3:** Industry benchmark is 25-30%
- **Within ±5:** Industry benchmark is 40-50%
- **Within ±7:** Industry benchmark is 60-70%

If you're hitting these benchmarks, **you have a competitive model!**

#### **Prediction Bias**
- **What it is:** Are you systematically over or under predicting?
- **Ideal:** 50/50 split (no bias)
- **Warning:** If 60%+ are over-predictions, you're consistently predicting too high
- **Fix:** Adjust league average efficiency or home court advantage

---

## 🔧 Troubleshooting

### Issue: "Historical data missing"

**Error:**
```
❌ No historical KenPom data found
💡 Run this command to get 2024 season data:
   python historical_kenpom_scraper.py
```

**Solution:**
1. Run `python historical_kenpom_scraper.py`
2. Enter credentials when prompted
3. Wait for completion
4. Re-run `python run_ncaab_backtest.py`

---

### Issue: "Failed predictions: 222"

**This is normal!** Some games fail because:
- Team names don't match (e.g., "LA Lakers" vs "Los Angeles Lakers")
- Teams not in KenPom database (lower divisions)
- Missing data

**Solutions:**
1. **If <10% failures:** Ignore - not a problem
2. **If >20% failures:** 
   - Check team name matching in predictor
   - Verify KenPom data is complete

---

### Issue: Google Sheets upload fails

**Error:**
```
❌ Error uploading to Google Sheets: Permission denied
```

**Solution:**
1. Open your Google Sheet
2. Click "Share"
3. Verify service account has "Editor" access:
   - Email: nba-model-service@fair-app-459922-n5.iam.gserviceaccount.com
4. Re-run backtest

---

### Issue: MAE is very high (10+ points)

**Possible Causes:**
1. Wrong season data (using current season for historical predictions)
2. Home court advantage too high/low
3. League average efficiency incorrect
4. Tempo calculation off

**Solutions:**
1. Verify you scraped **2024** season data (for 2023-24 games)
2. Try adjusting home court advantage:
   - Current: 3.5 points
   - Try: 2.5-4.5 points
3. Try adjusting league average efficiency:
   - Current: 105.0
   - Try: 103.0-107.0

Edit these in `backend/config.py`:
```python
HOME_COURT_ADVANTAGE = 3.5  # Try 2.5 or 4.5
LEAGUE_AVG_EFFICIENCY = 105.0  # Try 103.0 or 107.0
```

---

## 📊 What's Next?

### If Results Are Good (MAE < 7):

1. **📈 Start Daily Predictions**
   ```powershell
   python run_ncaab_predictions.py
   ```

2. **📝 Track Real Performance**
   - Compare predictions to actual results
   - Log win rate over time
   - Calculate Closing Line Value (CLV)

3. **💰 Paper Trade First**
   - Track bets without real money
   - Verify model works in real-time
   - Build confidence before betting real money

---

### If Results Need Work (MAE > 8):

1. **🔍 Analyze Errors**
   - Which games are you missing badly?
   - High-scoring? Low-scoring?
   - Specific conferences?

2. **⚙️ Calibrate Model**
   - Adjust home court advantage
   - Tune league average efficiency
   - Review tempo calculation

3. **📚 Get More Data**
   - Backtest 2023 season
   - Backtest 2022 season
   - Look for consistent patterns

---

## 🎓 Key Takeaways

1. **Backtesting validates your model** - Without it, you're guessing
2. **MAE of 5-7 is very good** - Professional level
3. **40-50% within ±5 is competitive** - Industry benchmark
4. **Balanced predictions matter** - Don't want systematic bias
5. **Multiple seasons needed** - One season isn't enough validation

---

## 💡 Pro Tips

### Tip 1: Look at Error Distribution

In your detailed predictions (bottom of Backtesting tab), sort by `Abs_Error` (highest first).

**Questions to ask:**
- Are the biggest errors all high-scoring games?
- Are they all low-scoring games?
- Any patterns by conference?

### Tip 2: Check Tempo Predictions

Sort by `Expected_Pace` and compare to actual results.

**If consistently too high/low:**
- Your geometric mean calculation might need adjustment
- Some teams play faster/slower than KenPom suggests

### Tip 3: Conference-Specific Analysis

Create pivot tables by conference (if you add that column):
- ACC might have different average total than Big Ten
- Adjust predictions based on conference patterns

---

## 📞 Need Help?

If you encounter issues:

1. ✅ Check this guide's troubleshooting section
2. ✅ Verify all files are in correct locations
3. ✅ Ensure Google Sheets permissions are correct
4. ✅ Confirm historical data is from correct season

---

## 🎉 Success Checklist

After running the backtest, you should have:

- ✅ Console output showing metrics
- ✅ Local CSV files in `backend/data/backtesting/`
- ✅ Google Sheet with "Backtesting" tab
- ✅ Summary metrics at top of Backtesting tab
- ✅ 4,000+ detailed predictions below summary

**If you have all of these, you're ready to analyze your model's performance!** 🏀📊

Good luck with your backtesting! 🎲📈
