# NCAA Basketball Model Calibration - URGENT FIX NEEDED

## 🚨 Your Backtest Results Show Major Issues

**Current Performance:**
- MAE: 18.52 points (Should be <7)
- Within ±5 points: 17.1% (Should be >40%)
- Prediction bias: +7.2 points (62.8% over-predictions)

**Root Cause:** Model parameters are set too high, causing systematic over-predictions.

---

## 🔧 IMMEDIATE FIX (5 minutes)

### Step 1: Update Your Config File

1. **Copy the calibrated config file:**
   ```powershell
   copy config_calibrated.py config.py
   copy config_calibrated.py backend\config.py
   ```

2. **Key changes made:**
   - `LEAGUE_AVG_EFFICIENCY`: 105.0 → 98.0 (fixes ~6 points)
   - `HOME_COURT_ADVANTAGE`: 3.5 → 3.0 (fixes ~1 point)

### Step 2: Re-run Backtest

```powershell
cd C:\Users\nashr
python run_ncaab_backtest.py
```

**Expected improvements:**
- MAE should drop to ~12 points
- Within ±5 should improve to ~35%
- Prediction bias should balance to ~50/50

---

## 📊 Expected Results After Calibration

### Before (Current):
```
MAE: 18.52 points          ❌
Within ±5: 17.1%           ❌  
Over-predictions: 62.8%    ❌
```

### After (Expected):
```
MAE: ~12 points            ⚠️ (still need more tuning)
Within ±5: ~35%            ⚠️ (better but not ideal)
Over-predictions: ~50%     ✅ (balanced)
```

---

## 🎯 Next Steps if Still Not Ideal

If after calibration your MAE is still >10 points:

### Further Adjustments:

**If still over-predicting:**
- Reduce `LEAGUE_AVG_EFFICIENCY` to 95.0

**If now under-predicting:**
- Increase `LEAGUE_AVG_EFFICIENCY` to 100.0

**Target Values:**
- MAE: <8 points (ideally <7)
- Within ±5: >35% (ideally >40%)
- Prediction bias: 48-52%

---

## 🔄 Calibration Process

1. **Update config** → Re-run backtest → Check results
2. **If still off** → Adjust parameters → Re-run backtest
3. **Repeat until** → MAE <8 AND Within ±5 >35%

**Rule of thumb:**
- Each 1.0 change in LEAGUE_AVG_EFFICIENCY ≈ 1.4 point change in average total
- Each 0.5 change in HOME_COURT_ADVANTAGE ≈ 0.25 point change in average total

---

## ⚡ Quick Start Commands

```powershell
# 1. Copy calibrated config
copy config_calibrated.py config.py

# 2. Re-run backtest  
python run_ncaab_backtest.py

# 3. Check Google Sheets for new results
```

**Time needed:** 5 minutes to update + 5 minutes to re-run backtest

🎯 **Goal:** Get MAE under 10 points and Within ±5 over 30% before using model for betting!
