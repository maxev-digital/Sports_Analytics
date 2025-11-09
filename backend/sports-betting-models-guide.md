# Sports Betting Models - Complete Reference Guide

## Table of Contents
1. [Glossary of Terms](#glossary-of-terms)
2. [Model Types Overview](#model-types-overview)
3. [Sport-Specific Recommendations](#sport-specific-recommendations)
4. [Implementation Guide](#implementation-guide)
5. [Quick Comparison Scripts](#quick-comparison-scripts)

---

## Glossary of Terms

### Statistical & Model Performance Metrics

**MAE (Mean Absolute Error)** - Average of absolute differences between predicted and actual values. Lower is better. Example: If you predict a team to score 24 points and they score 21, that's an MAE contribution of 3.

**RMSE (Root Mean Square Error)** - Square root of average squared errors. Penalizes large errors more heavily than MAE. Standard metric for evaluating prediction models.

**R-squared (R²)** - Measures how well your model explains variance in outcomes (0-1 scale). 0.3-0.5 is actually good in sports betting due to inherent randomness.

**Bias** - Systematic tendency to over or under-predict. A model might consistently predict totals 2 points too high.

**Variance** - How much predictions fluctuate. High variance means inconsistent predictions.

**Regression to the Mean** - Extreme performances tend to move toward average over time. Important for not overreacting to outliers.

### Expected Value & ROI Concepts

**EV (Expected Value)** - Average expected return per bet over the long run. Formula: (Win% × Win Amount) - (Loss% × Loss Amount). Positive EV = profitable long-term.

**ROI (Return on Investment)** - (Net Profit / Total Amount Wagered) × 100. A 5% ROI is excellent in sports betting.

**CLV (Closing Line Value)** - Difference between the odds when you bet and closing odds. Consistently beating the closing line indicates sharp betting.

**True Probability** - Actual likelihood of an outcome occurring, not the implied probability from odds.

**Implied Probability** - What the odds suggest the likelihood is. American odds -110 = 52.38% implied probability.

**Hold/Vig/Juice** - The bookmaker's commission. Standard is -110 both sides (4.5% hold). Lower hold = better for bettors.

### Betting Market Terms

**Spread/Line** - Point handicap. Favorites give points (-7), underdogs get points (+7).

**Total/Over-Under** - Combined score of both teams. Bet over or under that number.

**Moneyline** - Straight up winner, no spread. Displayed as American odds (+150, -180).

**Parlay** - Multiple bets combined. All must win. Higher payout but much lower win probability.

**Teaser** - Adjusted spreads/totals in your favor (typically 6-7 points) for reduced payout.

**Sharp Money** - Bets from professional/respected bettors that often move lines.

**Public Money** - Recreational bettor money, often on favorites/overs.

**Steam Move** - Sudden, significant line movement across multiple books simultaneously.

**Reverse Line Movement (RLM)** - Line moves against public betting percentage, suggesting sharp action.

### Bankroll Management

**Kelly Criterion** - Formula for optimal bet sizing: (Edge / Odds). Most use fractional Kelly (25-50%) to reduce variance.

**Unit** - Standard bet size, typically 1-2% of bankroll. Allows consistent sizing regardless of bankroll changes.

**Bankroll** - Total funds allocated for betting. Should be separate from living expenses.

**Drawdown** - Peak-to-trough decline in bankroll. Important metric for risk assessment.

### Market Efficiency & Edge

**Market Efficiency** - How accurately odds reflect true probabilities. NFL/NBA are most efficient; niche markets less so.

**Edge** - Your advantage over the market. 2-3% edge is significant in major sports.

**Arbitrage (Arb)** - Betting all outcomes across different books to guarantee profit. Rare and requires speed.

**Positive EV (+EV)** - Bet where expected value exceeds the cost. Core principle of profitable betting.

**Overround** - Sum of implied probabilities exceeds 100%. Represents book's margin.

### Live Betting Specific

**In-Game/Live Betting** - Wagering during the game with dynamic odds.

**Pace** - Speed of game measured in possessions per minute. Critical for totals betting.

**Game Script** - Expected flow based on score/situation. Trailing teams pass more, affecting pace.

**Middle** - Betting both sides at different numbers, trying to win both if result lands between.

### Model-Specific Terms

**Feature** - Input variable in your model (team stats, rest days, weather, etc.).

**Training Data** - Historical data used to build the model.

**Backtesting** - Testing model on historical data to evaluate performance.

**Overfitting** - Model too tailored to past data, performs poorly on new data.

**Sample Size** - Amount of data/bets. Need sufficient size for statistical significance (typically 200+ bets).

**Correlation** - Relationship between variables. High correlation can indicate predictive power.

**Weights/Coefficients** - How much each factor influences the prediction.

---

## Model Types Overview

### Regression Models

#### Linear Regression
Predicts outcomes based on weighted combination of variables

**Best for:** 
- NFL spreads
- NBA totals
- Any bet where relationships are relatively linear

**Pros:** Simple, interpretable, fast, works with limited data

**Cons:** Can't capture complex interactions, assumes linear relationships

#### Logistic Regression
Predicts probability of binary outcomes (win/loss)

**Best for:**
- Moneyline bets
- NFL/NBA win probability

**Pros:** Outputs clean probabilities, handles classification well

**Cons:** Still limited on non-linear relationships

#### Polynomial/Non-Linear Regression
Captures curved relationships

**Best for:**
- Player props with thresholds
- Pace-dependent totals

**Pros:** More flexible than linear

**Cons:** Easy to overfit

### Machine Learning Models

#### Random Forest
Ensemble of decision trees

**Best for:**
- Player props
- MLB outcomes (lots of variables)
- NBA/NFL when you have deep stats

**Pros:** Handles non-linear relationships, resistant to overfitting, captures interactions

**Cons:** Black box, computationally heavy, needs large datasets

#### Gradient Boosting (XGBoost, LightGBM)
Sequential tree building focusing on errors

**Best for:**
- MLB game outcomes
- Player props
- Complex markets with many features

**Pros:** Often highest accuracy, handles missing data well

**Cons:** Very black box, can overfit, requires extensive tuning

#### Neural Networks/Deep Learning
Layered nodes learning patterns

**Best for:**
- Live betting (time series)
- Image-based analysis (shot charts)
- Extremely large datasets

**Pros:** Can find any pattern if data exists

**Cons:** Needs massive data, complete black box, overkill for most betting

#### K-Nearest Neighbors (KNN)
Predicts based on similar historical situations

**Best for:**
- Situational betting (weather games, rest scenarios)
- Small sample props

**Pros:** Simple concept, good for unique situations

**Cons:** Poor with high dimensions, slow, needs lots of relevant comps

### Simulation Models

#### Monte Carlo Simulation
Runs thousands of game simulations

**Best for:**
- Game totals (all sports)
- Player props
- Parlays/SGPs

**Pros:** Captures variance, provides probability distributions

**Cons:** Requires good input distributions, computationally expensive

#### Possession-Based Simulation
Simulates each possession/play

**Best for:**
- NBA totals (pace-based)
- NFL drive modeling

**Pros:** Very granular, matches actual game flow

**Cons:** Complex to build, needs detailed possession data

#### Markov Chain Models
State-to-state transition probabilities

**Best for:**
- Tennis
- Baseball (batter-pitcher matchups)
- In-game win probability

**Pros:** Good for sequential events

**Cons:** Assumes independence between states

### Market-Based Models

#### Market Consensus/Aggregation
Combining odds from multiple books

**Best for:**
- Finding +EV across all sports
- Arbitrage opportunities

**Pros:** Market is hard to beat, identifies inefficiencies

**Cons:** You need an edge on why market is wrong

#### Implied Probability Modeling
Converting odds to probabilities, finding discrepancies

**Best for:**
- All bet types
- Comparing your model to market

**Pros:** Simple, focuses on edge

**Cons:** Not predictive itself, just comparative

#### Steam/Line Movement Models
Following sharp money movement

**Best for:**
- Major sports (NFL/NBA/MLB)
- Closing line value

**Pros:** Leverages sharp bettor info

**Cons:** Need fast data, lines adjust quickly

### Hybrid/Ensemble Models

#### Weighted Model Average
Combining multiple model predictions

**Best for:**
- All sports
- Reduces single-model bias

**Pros:** More robust, smooths out individual model errors

**Cons:** Adds complexity, need to determine weights

#### Bayesian Models
Updates predictions with new information

**Best for:**
- In-season adjustments
- Live betting
- Incorporating injury news

**Pros:** Naturally incorporates uncertainty, updates logically

**Cons:** Complex to implement properly

---

## Sport-Specific Recommendations

### NFL

#### Spreads
- **Primary:** Linear/Polynomial Regression (clear power ratings work well)
- **Secondary:** Random Forest (captures matchup-specific factors)
- **Approach:** TeamRankings stats → point impact values works perfectly for regression

#### Totals
- **Primary:** Regression Models with game script factors
- **Alternative:** Simulation for weather/pace variance
- **Key factors:** Pace, efficiency, weather, game script

#### Moneylines
- **Primary:** Logistic Regression or Win Probability Models
- **Note:** Market usually sharp enough that you need specific edges

#### Player Props
- **Primary:** Random Forest or XGBoost (many variables)
- **Alternative:** KNN for specific situations (weather, opponent)
- **Note:** Volume props easier to model than efficiency props

### NBA

#### Spreads
- **Primary:** Regression with rest, travel, motivation factors
- **Alternative:** Possession-based simulation

#### Totals
- **Primary:** Pace-based simulation models (optimal approach)
- **Secondary:** Regression with pace + efficiency stats
- **Live betting:** Real-time pace adjustment models shine here

#### Moneylines
- Similar to spreads, regression-based power ratings

#### Player Props
- **Primary:** XGBoost (usage rate, pace, matchup all matter)
- **Alternative:** Monte Carlo for point totals
- **Critical variable:** Minutes played

#### Live/In-Game
- Real-time regression updating with current pace/efficiency
- Win probability models based on score, time, possessions remaining

### MLB

#### Game Outcomes (ML/Spread)
- **Primary:** Random Forest or XGBoost (pitcher matchups, bullpen, weather, lineup construction)
- **Alternative:** Logistic Regression for simpler approach
- **Note:** Pitcher-heavy models work well

#### Totals
- **Primary:** Regression with park factors, weather, pitcher/lineup
- **Alternative:** Simulation accounting for variance
- **Note:** Most predictable total market in sports

#### Player Props
- **Primary:** XGBoost for hitters (splits, pitcher matchup, ballpark)
- **Pitcher props:** Regression with opponent stats
- **Note:** Batter vs pitcher historical is overweighted by public

#### First 5 Innings (F5)
- Starting pitcher focused regression
- Removes bullpen variance

### NHL

#### All Bets
- **Primary:** Regression with goalie/shot quality adjustment
- **Alternative:** Expected Goals (xG) based models
- **Note:** Highly random sport, small edges only

#### Puck Lines
- Similar to spreads but account for empty net variance
- Simulation helps with 1-goal margin probability

#### Totals
- Regression with pace of play, goalie quality
- Lower-scoring makes this tougher than other sports

### Soccer

#### Match Result (1X2)
- **Primary:** Poisson Regression (goal-based modeling)
- **Alternative:** Expected Goals (xG) models with shot quality
- Random Forest for leagues with lots of data

#### Totals/Goal Lines
- Poisson distribution models work exceptionally well
- Simulate goal scoring as independent events

#### Both Teams to Score, Exact Score
- Poisson-based simulation
- Works better in soccer than any other sport due to low scoring

#### Asian Handicaps
- Similar to spreads, Poisson regression

### Tennis

#### Match Winner
- **Primary:** Logistic Regression with Elo ratings
- **Alternative:** Markov Chain for set/game modeling

#### Set Betting
- Simulation based on service game win probability
- Surface matchups are critical

### Golf

#### Tournament Winner
- Monte Carlo simulation with round scoring distributions
- Regression for cut predictions

#### Matchups/Top 5-10-20
- Historical performance regression on course
- XGBoost with strokes gained data

---

## Bet Type Recommendations

### Spreads/Handicaps
- Regression models dominate across all sports
- Power ratings + adjustments approach

### Totals
- **NBA:** Pace simulation
- **MLB:** Regression with park/weather
- **NFL:** Regression with game script
- **Soccer:** Poisson distribution

### Moneylines
- Logistic regression or convert spread models
- Market usually efficient, need specific edges

### Player Props
- Machine learning (Random Forest/XGBoost) when data is available
- Regression for simpler props
- Pace/usage-based for volume props

### Parlays/SGP
- Monte Carlo simulation for correlation
- Most are sucker bets but can find +EV in SGP with correlated outcomes

### Live Betting
- Real-time updating regression models
- Win probability models
- Pace-based approaches

### Derivatives (1H, Q1, team totals)
- Scaled versions of full game models
- NBA quarters: divide by 4 with pace adjustments
- NFL halves: game script more important

---

## Implementation Guide

### Super Easy - Same Syntax as XGBoost

These all use scikit-learn's standard API. If you know XGBoost, you know these:

#### Random Forest
```python
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# Literally same usage as XGBoost
model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

#### Linear/Logistic Regression
```python
from sklearn.linear_model import LinearRegression, LogisticRegression

# Even simpler than XGBoost
model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# Logistic for win/loss probabilities
log_model = LogisticRegression()
log_model.fit(X_train, y_train)
win_probabilities = log_model.predict_proba(X_test)
```

#### Polynomial Regression
```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

# Just wraps linear regression
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X_train)
model = LinearRegression()
model.fit(X_poly, y_train)
```

#### Gradient Boosting (scikit-learn version)
```python
from sklearn.ensemble import GradientBoostingRegressor

# Identical API to XGBoost
model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

#### K-Nearest Neighbors
```python
from sklearn.neighbors import KNeighborsRegressor

model = KNeighborsRegressor(n_neighbors=5)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

### Easy - Requires One Additional Library

#### LightGBM (Microsoft's faster version of XGBoost)
```python
import lightgbm as lgb

# Almost identical to XGBoost
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```
**Install:** `pip install lightgbm`

#### CatBoost (Handles categorical data automatically)
```python
from catboost import CatBoostRegressor

model = CatBoostRegressor(iterations=100, learning_rate=0.1, verbose=False)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```
**Install:** `pip install catboost`

### Moderate - Simulation Models

#### Monte Carlo Simulation
```python
import numpy as np

# Custom but straightforward
def simulate_game_total(avg_possessions, avg_points_per_possession, n_simulations=10000):
    possessions = np.random.poisson(avg_possessions, n_simulations)
    points_per_poss = np.random.normal(avg_points_per_possession, 0.05, n_simulations)
    total_points = possessions * points_per_poss
    
    return {
        'mean': np.mean(total_points),
        'over_probability': np.mean(total_points > line),
        'distribution': total_points
    }

# Usage
result = simulate_game_total(avg_possessions=100, avg_points_per_possession=2.2)
```
**No install needed, just numpy**

#### Poisson Regression (for soccer/baseball)
```python
import statsmodels.api as sm

# Statsmodels has this built-in
model = sm.GLM(y_train, X_train, family=sm.families.Poisson())
results = model.fit()
predictions = results.predict(X_test)
```
**Install:** `pip install statsmodels`

### More Complex - But Still Doable

#### Neural Networks (Keras/TensorFlow)
```python
from tensorflow import keras
from tensorflow.keras import layers

# More setup than XGBoost
model = keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    layers.Dense(32, activation='relu'),
    layers.Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)
predictions = model.predict(X_test)
```
**Install:** `pip install tensorflow`

#### Bayesian Models (PyMC)
```python
import pymc as pm

# More statistical programming
with pm.Model() as model:
    # Define priors
    alpha = pm.Normal('alpha', mu=0, sigma=10)
    beta = pm.Normal('beta', mu=0, sigma=10)
    sigma = pm.HalfNormal('sigma', sigma=1)
    
    # Expected value
    mu = alpha + beta * X_train
    
    # Likelihood
    y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y_train)
    
    # Inference
    trace = pm.sample(2000, return_inferencedata=False)
```
**Install:** `pip install pymc`

---

## Quick Comparison Scripts

### Multi-Model Testing Framework
```python
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

# All models have same API
models = {
    'Linear': LinearRegression(),
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
    'Gradient Boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
    'XGBoost': XGBRegressor(n_estimators=100, random_state=42),
    'LightGBM': lgb.LGBMRegressor(n_estimators=100, random_state=42)
}

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    results[name] = mae
    print(f"{name}: MAE = {mae:.3f}")

# Find best model
best_model = min(results, key=results.get)
print(f"\nBest model: {best_model}")
```

### Ensemble Model (Combining Multiple Models)
```python
# Train multiple models
linear_model = LinearRegression()
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
xgb_model = XGBRegressor(n_estimators=100, random_state=42)

# Fit all models
linear_model.fit(X_train, y_train)
rf_model.fit(X_train, y_train)
xgb_model.fit(X_train, y_train)

# Get predictions from each
linear_pred = linear_model.predict(X_test)
rf_pred = rf_model.predict(X_test)
xgb_pred = xgb_model.predict(X_test)

# Simple average ensemble
ensemble_pred = (linear_pred + rf_pred + xgb_pred) / 3

# Weighted ensemble (if you know which performs better)
ensemble_pred_weighted = (0.2 * linear_pred + 0.3 * rf_pred + 0.5 * xgb_pred)

# Evaluate
from sklearn.metrics import mean_absolute_error
print(f"Linear MAE: {mean_absolute_error(y_test, linear_pred):.3f}")
print(f"RF MAE: {mean_absolute_error(y_test, rf_pred):.3f}")
print(f"XGBoost MAE: {mean_absolute_error(y_test, xgb_pred):.3f}")
print(f"Ensemble MAE: {mean_absolute_error(y_test, ensemble_pred):.3f}")
print(f"Weighted Ensemble MAE: {mean_absolute_error(y_test, ensemble_pred_weighted):.3f}")
```

---

## Immediate Recommendations

### For Your Current Setup (Already Using XGBoost)

Add these to your toolkit immediately:

1. **Linear/Logistic Regression** (already installed with scikit-learn)
   - Quick baseline model
   - Interpretable coefficients
   - Use for power ratings

2. **Random Forest** (already installed)
   - Compare against XGBoost
   - Often less prone to overfitting
   - Good for understanding feature importance

3. **LightGBM** (`pip install lightgbm`)
   - Faster than XGBoost, especially for large datasets
   - Often slightly better accuracy
   - Drop-in replacement syntax

4. **Simple Monte Carlo** (just numpy)
   - Add variance/probability distributions to your point predictions
   - Perfect for NBA totals dashboard

### Project-Specific Recommendations

#### NBA Pace Dashboard
- Keep XGBoost for possession prediction
- Add Monte Carlo simulation for probability distributions
- Add Linear Regression as fast backup for live betting

#### NFL Model
- Test Linear Regression vs your current XGBoost
- NFL is linear enough that regression often beats ML
- Much faster for live updates

#### Future Projects
For your skill level and data available, focus on **hybrid regression + simulation** approaches. They're:
- Interpretable (you understand WHY)
- Fast (real-time betting capable)
- Don't need massive datasets
- Work across multiple sports

---

## Installation Commands Summary

```bash
# Already have with scikit-learn (comes with most Python installations)
# - Linear Regression
# - Logistic Regression
# - Random Forest
# - Gradient Boosting
# - K-Nearest Neighbors

# Additional installs for expanded functionality
pip install lightgbm      # Faster gradient boosting
pip install catboost      # Handles categorical data well
pip install statsmodels   # For Poisson regression (soccer/baseball)
pip install tensorflow    # For neural networks (if needed)
pip install pymc          # For Bayesian models (advanced)
```

---

*Last Updated: November 2025*
*For use with Claude CLI and sports betting model development*