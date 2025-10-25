# NCAA Basketball Model - Testing & Backtesting Guide

## 📋 Table of Contents

1. [Test Google Sheets Upload](#test-google-sheets-upload)
2. [Get Historical Data](#get-historical-data)
3. [Run Backtests](#run-backtests)
4. [Interpret Results](#interpret-results)
5. [Troubleshooting](#troubleshooting)

---

## 🧪 Test Google Sheets Upload

Since it's the off-season, test that your Google Sheets integration works with fake data:

### Step 1: Run Test Upload
```powershell
cd C:\Users\nashr
python test_sheets_upload.py
```

### Expected Output:
```
══════════════════════════════════════════════════════════════════════
NCAA BASKETBALL - GOOGLE SHEETS UPLOAD TEST
══════════════════════════════════════════════════════════════════════

📊 Step 1: Generating fake predictions...
   ✅ Generated 20 fake predictions
   HIGH confidence: 3
   MEDIUM confidence: 5
   LOW confidence: 7

🏆 Top 5 Predictions (by edge):
#1 - HIGH CONFIDENCE (6.8 point edge)
   Duke @ North Carolina
   Model: 162.3 | Market: 155.5
   Bet: OVER 155.5

☁️ Step 2: Uploading to Google Sheets...
   ✅ Successfully uploaded 20 predictions!
   🔗 View: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID

══════════════════════════════════════════════════════════════════════
TEST COMPLETE - Check your Google Sheet!
══════════════════════════════════════════════════════════════════════
```

### Step 2: Verify Google Sheet
1. Open the link shown in the output
2. You should see 20 rows of fake predictions
3. Verify color coding (if applied):
   - 🟢 GREEN rows = HIGH confidence
   - 🟡 YELLOW rows = MEDIUM confidence
   - ⚪ WHITE rows = LOW confidence

✅ **If this works, your Google Sheets integration is perfect!**

---

## 📚 Get Historical Data

To backtest the model, you need historical data from last season (2023-24).

### Step 1: Get Historical KenPom Data

```powershell
cd C:\Users\nashr
python historical_kenpom_scraper.py
```

**Prompts:**
- Email: gte.apw@gmail.com
- Password: Thewrench1!
- Headless: y
- Year: 2024 (for 2023-24 season)

**Output:**
```
✅ Successfully scraped 364 teams
📈 Tempo range: 59.4 - 75.3
📈 OffEff range: 82.7 - 130.1
📈 DefEff range: 86.8 - 124.9
💾 Saved: backend/data/historical/kenpom_2024_season_YYYYMMDD_HHMMSS.csv

TOP 10 TEAMS (2023-24 SEASON):
 Rank           Team Conference  AdjTempo  AdjOffEff  AdjDefEff
    1     Connecticut    Big East      68.2      129.4       87.9
    2         Purdue     Big Ten      67.8      127.8       89.2
```

### Step 2: Get Historical Game Results

```powershell
python game_results_scraper.py
```

**Prompts:**
- Year: 2024

**Output:**
```
🏀 Scraping game results for 2023-24 season...
   ✅ Found 5,000+ games

✅ Successfully parsed 4,872 complete games
📈 Total points range: 95 - 198
📈 Average total: 141.3

💾 Saved: backend/data/historical/game_results_2024_season_YYYYMMDD_HHMMSS.csv
```

**Files Created:**
- `backend/data/historical/kenpom_2024_season_*.csv` - Historical KenPom ratings
- `backend/data/historical/game_results_2024_season_*.csv` - Historical game scores

---

## 🔬 Run Backtests

Now test your model against last season's actual results!

### Option 1: Quick Test (Sample Games)

```powershell
cd C:\Users\nashr
python ncaab_backtester.py
```

This runs with 10 sample games to verify the backtester works.

### Option 2: Full Season Backtest

Edit `ncaab_backtester.py` to load your historical data:

```python
# At the bottom of ncaab_backtester.py, replace main() function:

def main():
    # Load historical KenPom data
    kenpom_path = "backend/data/historical/kenpom_2024_season_YYYYMMDD_HHMMSS.csv"
    
    # Load historical game results
    games_path = "backend/data/historical/game_results_2024_season_YYYYMMDD_HHMMSS.csv"
    games_df = pd.read_csv(games_path)
    
    # Run backtester
    backtester = NCAABBacktester(kenpom_data_path=kenpom_path)
    results = backtester.run(games_df=games_df)
```

Then run:
```powershell
python ncaab_backtester.py
```

---

## 📊 Interpret Results

### Backtest Metrics Explained

#### **Mean Absolute Error (MAE)**
- **What it is**: Average points your predictions are off
- **Good**: 5-7 points
- **Excellent**: <5 points
- **Example**: MAE of 6.2 means on average, you're 6.2 points off actual total

#### **Root Mean Squared Error (RMSE)**
- **What it is**: Penalizes large errors more than MAE
- **Good**: 7-9 points
- **Excellent**: <7 points
- **Use**: Identifies if you have systematic issues with certain types of games

#### **Within X Points Accuracy**
- **Within ±3 points**: Industry standard is ~25-30%
- **Within ±5 points**: Industry standard is ~40-50%
- **Within ±7 points**: Industry standard is ~60-70%

**Example Output:**
```
════════════════════════════════════════════════════════════════════
BACKTESTING RESULTS
════════════════════════════════════════════════════════════════════

📊 Sample Size: 4,872 games
📊 Average Actual Total: 141.3
📊 Average Model Prediction: 142.1

🎯 Accuracy Metrics:
   Mean Absolute Error (MAE): 6.2 points
   Root Mean Squared Error (RMSE): 8.1 points
   Median Absolute Error: 5.1 points

✅ Predictions Within:
   ±3 points: 28.4%  ← If >25%, you're doing well!
   ±5 points: 46.7%  ← If >40%, you're doing well!
   ±7 points: 62.3%  ← If >55%, you're doing well!
   ±10 points: 81.2%

🔄 Prediction Bias:
   Over-predictions: 2,387 (49.0%)  ← Should be ~50%
   Under-predictions: 2,485 (51.0%) ← Should be ~50%
```

### What Good Results Look Like

✅ **Excellent Model:**
- MAE: 4-5 points
- Within ±5: 50%+
- Balanced over/under (48-52%)

✅ **Good Model:**
- MAE: 5-7 points
- Within ±5: 40-50%
- Balanced over/under (45-55%)

⚠️ **Needs Work:**
- MAE: 8+ points
- Within ±5: <35%
- Biased over/under (<40% or >60%)

### Common Issues

**Issue: High MAE (8+ points)**
- Problem: Model is consistently off
- Solutions:
  - Check if using correct season's KenPom data
  - Verify home court advantage (3.5 points)
  - Check pace calculation formula

**Issue: Biased Predictions (60%+ over or under)**
- Problem: Systematic over/under prediction
- Solutions:
  - Adjust league average efficiency (currently 105.0)
  - Recalibrate home court advantage
  - Check tempo adjustments

**Issue: Good MAE but low "Within ±3" percentage**
- Problem: Model is accurate on average but has high variance
- This is actually okay! It means you're close on most games but occasionally way off
- NBA model has this same pattern

---

## 🔧 Troubleshooting

### Test Upload Fails

**Error:** "Authentication failed" or "Permission denied"
```
❌ Error uploading to Google Sheets: Permission denied
```

**Solution:**
1. Open your Google Sheet
2. Click "Share"
3. Verify service account email has "Editor" access:
   - Email: nba-model-service@fair-app-459922-n5.iam.gserviceaccount.com
4. Re-run test

### Historical Scraper Fails

**Error:** "Login status unclear"
```
⚠️ Login status unclear - attempting to proceed...
❌ No tables found on page
```

**Solution:**
1. KenPom changed their page structure
2. Try manually navigating to: https://kenpom.com/index.php?y=2024
3. Verify you can see the ratings table
4. If table visible but scraper fails, page structure changed (contact for updated scraper)

### Game Results Scraper Returns Empty

**Error:** "Could not find schedule table"
```
❌ Could not find schedule table
```

**Solution:**
1. Sports-Reference may have changed their URL format
2. Try manually: https://www.sports-reference.com/cbb/seasons/2024-schedule.html
3. If page exists, their table ID changed (contact for updated scraper)

### Backtester Can't Find Teams

**Error:** "Could not predict: Duke vs North Carolina"

**Possible causes:**
1. **Team name mismatch**: 
   - KenPom: "Duke 1" (with seed)
   - Game results: "Duke" (no seed)
   
   **Solution**: Update team name matching in predictor

2. **Missing teams in KenPom data**:
   - Some teams not in D1
   
   **Solution**: Filter game results to only D1 teams

---

## 🎯 Next Steps After Backtesting

### If Results Are Good (MAE < 7 points):

1. **Monitor During Season**
   - Run predictions daily when season starts
   - Compare model lines to actual market lines
   - Track Closing Line Value (CLV)

2. **Start Small**
   - Begin with paper trading (track bets without money)
   - Only bet HIGH confidence games initially
   - Use strict bankroll management (1-2% units)

3. **Continuous Improvement**
   - Update KenPom data weekly
   - Track actual performance vs predictions
   - Recalibrate if needed

### If Results Need Work (MAE > 8 points):

1. **Analyze Errors**
   - Which types of games are you missing?
   - High-scoring games? Low-scoring games?
   - Certain conferences?

2. **Adjust Model**
   - Fine-tune home court advantage
   - Adjust league average efficiency
   - Consider tempo adjustments

3. **More Data**
   - Backtest multiple seasons (2023, 2022, 2021)
   - Look for consistent patterns
   - Verify model isn't overfitted to one season

---

## 📁 File Reference

```
C:\Users\nashr\
├── test_sheets_upload.py              ← Test Sheets integration
├── historical_kenpom_scraper.py       ← Get historical ratings
├── game_results_scraper.py            ← Get historical scores
├── ncaab_backtester.py                ← Run backtests
│
└── backend\
    └── data\
        ├── historical\
        │   ├── kenpom_2024_season_*.csv       ← Historical KenPom
        │   └── game_results_2024_season_*.csv ← Historical games
        │
        └── backtesting\
            ├── predictions_*.csv               ← Backtest predictions
            └── metrics_*.csv                   ← Backtest metrics
```

---

## 🎓 Key Takeaways

1. **Test First**: Always verify Sheets upload works before season
2. **Historical Data**: Need both KenPom ratings AND game results
3. **Realistic Expectations**: 
   - MAE of 5-7 points is very good
   - 40-50% within ±5 points is professional-level
4. **Continuous Validation**: Backtest multiple seasons
5. **Start Small**: Paper trade first, then small bets

---

## 📞 Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Verify all files are in correct locations
3. Ensure KenPom subscription is active
4. Confirm Google Sheets permissions are correct

Good luck with your backtesting! 🏀📊
