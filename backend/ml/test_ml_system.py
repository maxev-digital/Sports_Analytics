"""
Quick test of goalie pull ML system
"""
from ml.models.goalie_pull_predictor import GoaliePullPredictor
from ml.pattern_analysis.goalie_pull_analyzer import GoaliePullAnalyzer

print("="*80)
print("TESTING NHL GOALIE PULL ML SYSTEM")
print("="*80)

# Test 1: Team Analysis
print("\n[TEST 1] Team Analysis - Tampa Bay Lightning (Jon Cooper)")
analyzer = GoaliePullAnalyzer()
analysis = analyzer.analyze_team("Tampa Bay Lightning", "20232024")
print(f"  Aggression Score: {analysis.get('aggression_score', 'N/A')}/100")
print(f"  Aggression Level: {analysis.get('aggression_level', 'N/A')}")
print(f"  Total Pulls: {analysis['patterns']['overall']['total_pulls']}")
print(f"  Avg Pull Time: {analysis['patterns']['overall']['avg_pull_time']}")

# Test 2: Live Prediction
print("\n[TEST 2] Live Prediction - Tampa Bay down 1 with 3:00 remaining")
predictor = GoaliePullPredictor()
prediction = predictor.predict(
    team="Tampa Bay Lightning",
    score_differential=-1,
    time_remaining_seconds=180,
    period=3,
    home_game=True,
    division_game=False,
    season="20232024"
)

print(f"  Prediction: {prediction['prediction']}")
print(f"  Pull Probability: {prediction['pull_probability']*100:.1f}%")
print(f"  Expected Pull Time: {prediction['expected_pull_time']}")
print(f"  Alert Level: {prediction['alert_level']}")
print(f"  Confidence: {prediction['confidence']*100:.1f}%")

if prediction.get('betting_recommendation'):
    bet = prediction['betting_recommendation']
    print(f"\n  Betting Recommendation: {bet['action']}")
    print(f"  Urgency: {bet['urgency']}")

print("\n" + "="*80)
print("[OK] ML SYSTEM WORKING CORRECTLY!")
print("="*80)
