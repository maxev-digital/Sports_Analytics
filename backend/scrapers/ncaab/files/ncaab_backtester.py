#!/usr/bin/env python3
"""
NCAA Basketball Model Backtesting Framework
Tests model predictions against historical results
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from models.ncaab.totals_predictor import NCAABTotalsPredictor
except ImportError:
    print("⚠️ Could not import predictor - will create minimal version")
    NCAABTotalsPredictor = None


class NCAABBacktester:
    def __init__(self, kenpom_data_path, historical_games_path=None):
        """
        Initialize backtester
        
        Args:
            kenpom_data_path: Path to historical KenPom CSV
            historical_games_path: Path to historical game results CSV
        """
        self.kenpom_path = kenpom_data_path
        self.games_path = historical_games_path
        
        # Load KenPom data
        print(f"📊 Loading KenPom data from: {kenpom_data_path}")
        self.kenpom_data = pd.read_csv(kenpom_data_path)
        print(f"   ✅ Loaded {len(self.kenpom_data)} teams")
        
        # Load historical games if provided
        self.historical_games = None
        if historical_games_path and os.path.exists(historical_games_path):
            print(f"🏀 Loading historical games from: {historical_games_path}")
            self.historical_games = pd.read_csv(historical_games_path)
            print(f"   ✅ Loaded {len(self.historical_games)} games")
        
        # Initialize predictor
        if NCAABTotalsPredictor:
            self.predictor = NCAABTotalsPredictor(
                kenpom_data=self.kenpom_data,
                home_court_advantage=3.5,
                league_avg_eff=105.0
            )
        else:
            self.predictor = None
        
        self.results = []
    
    def generate_predictions(self, games_df):
        """
        Generate predictions for historical games
        
        Args:
            games_df: DataFrame with columns: Home_Team, Away_Team, Actual_Total
        
        Returns:
            DataFrame with predictions and actual results
        """
        print(f"\n🔮 Generating predictions for {len(games_df)} games...")
        
        predictions = []
        successful = 0
        failed = 0
        
        for idx, game in games_df.iterrows():
            home_team = game['Home_Team']
            away_team = game['Away_Team']
            actual_total = game.get('Actual_Total', None)
            
            # Generate prediction
            pred = self.predictor.predict_game(home_team, away_team)
            
            if pred:
                model_total = pred['Model_Total']
                
                # Calculate error if we have actual result
                error = None
                abs_error = None
                if actual_total is not None:
                    error = model_total - actual_total
                    abs_error = abs(error)
                
                predictions.append({
                    'Home_Team': home_team,
                    'Away_Team': away_team,
                    'Model_Total': round(model_total, 1),
                    'Actual_Total': actual_total,
                    'Error': round(error, 1) if error is not None else None,
                    'Abs_Error': round(abs_error, 1) if abs_error is not None else None,
                    'Home_Tempo': pred['Home_Tempo'],
                    'Away_Tempo': pred['Away_Tempo'],
                    'Expected_Pace': pred['Expected_Pace']
                })
                successful += 1
            else:
                print(f"   ⚠️ Could not predict: {home_team} vs {away_team}")
                failed += 1
        
        print(f"   ✅ Successful predictions: {successful}")
        if failed > 0:
            print(f"   ⚠️ Failed predictions: {failed}")
        
        return pd.DataFrame(predictions)
    
    def calculate_metrics(self, predictions_df):
        """Calculate performance metrics"""
        
        # Filter to games with actual results
        df = predictions_df.dropna(subset=['Actual_Total'])
        
        if len(df) == 0:
            print("⚠️ No games with actual results to analyze")
            return {}
        
        print(f"\n📈 Calculating metrics for {len(df)} games...")
        
        # Mean Absolute Error (MAE)
        mae = df['Abs_Error'].mean()
        
        # Root Mean Squared Error (RMSE)
        rmse = np.sqrt((df['Error'] ** 2).mean())
        
        # Median Absolute Error
        median_ae = df['Abs_Error'].median()
        
        # Percentage within X points
        within_3 = (df['Abs_Error'] <= 3).sum() / len(df) * 100
        within_5 = (df['Abs_Error'] <= 5).sum() / len(df) * 100
        within_7 = (df['Abs_Error'] <= 7).sum() / len(df) * 100
        within_10 = (df['Abs_Error'] <= 10).sum() / len(df) * 100
        
        # Over/Under prediction
        over_predictions = (df['Error'] > 0).sum()
        under_predictions = (df['Error'] < 0).sum()
        
        metrics = {
            'total_games': len(df),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'median_ae': round(median_ae, 2),
            'within_3_pct': round(within_3, 1),
            'within_5_pct': round(within_5, 1),
            'within_7_pct': round(within_7, 1),
            'within_10_pct': round(within_10, 1),
            'over_predictions': over_predictions,
            'under_predictions': under_predictions,
            'avg_total': round(df['Actual_Total'].mean(), 1),
            'avg_prediction': round(df['Model_Total'].mean(), 1)
        }
        
        return metrics
    
    def display_metrics(self, metrics):
        """Display metrics in a readable format"""
        print("\n" + "="*70)
        print("BACKTESTING RESULTS")
        print("="*70)
        
        print(f"\n📊 Sample Size: {metrics['total_games']} games")
        print(f"📊 Average Actual Total: {metrics['avg_total']}")
        print(f"📊 Average Model Prediction: {metrics['avg_prediction']}")
        
        print("\n🎯 Accuracy Metrics:")
        print(f"   Mean Absolute Error (MAE): {metrics['mae']} points")
        print(f"   Root Mean Squared Error (RMSE): {metrics['rmse']} points")
        print(f"   Median Absolute Error: {metrics['median_ae']} points")
        
        print("\n✅ Predictions Within:")
        print(f"   ±3 points: {metrics['within_3_pct']}%")
        print(f"   ±5 points: {metrics['within_5_pct']}%")
        print(f"   ±7 points: {metrics['within_7_pct']}%")
        print(f"   ±10 points: {metrics['within_10_pct']}%")
        
        print("\n🔄 Prediction Bias:")
        print(f"   Over-predictions: {metrics['over_predictions']} ({metrics['over_predictions']/metrics['total_games']*100:.1f}%)")
        print(f"   Under-predictions: {metrics['under_predictions']} ({metrics['under_predictions']/metrics['total_games']*100:.1f}%)")
        
        print("\n" + "="*70)
    
    def save_results(self, predictions_df, metrics, output_dir='backend/data/backtesting'):
        """Save backtest results"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save predictions
        predictions_file = f"{output_dir}/predictions_{timestamp}.csv"
        predictions_df.to_csv(predictions_file, index=False)
        print(f"\n💾 Saved predictions: {predictions_file}")
        
        # Save metrics
        metrics_file = f"{output_dir}/metrics_{timestamp}.csv"
        metrics_df = pd.DataFrame([metrics])
        metrics_df.to_csv(metrics_file, index=False)
        print(f"💾 Saved metrics: {metrics_file}")
        
        return predictions_file, metrics_file
    
    def run(self, games_df=None):
        """
        Run complete backtesting workflow
        
        Args:
            games_df: Optional DataFrame with historical games
                     If not provided, will use self.historical_games
        """
        print("="*70)
        print("NCAA BASKETBALL MODEL - BACKTESTING")
        print("="*70)
        
        if games_df is None:
            games_df = self.historical_games
        
        if games_df is None or len(games_df) == 0:
            print("❌ No games to backtest")
            print("   Provide a CSV with: Home_Team, Away_Team, Actual_Total")
            return None
        
        # Generate predictions
        predictions = self.generate_predictions(games_df)
        
        # Calculate metrics
        metrics = self.calculate_metrics(predictions)
        
        # Display results
        if metrics:
            self.display_metrics(metrics)
        
        # Save results
        self.save_results(predictions, metrics)
        
        return predictions, metrics


def create_sample_games():
    """Create sample historical games for testing"""
    games = [
        # High-scoring teams
        {'Home_Team': 'Duke', 'Away_Team': 'North Carolina', 'Actual_Total': 165},
        {'Home_Team': 'Gonzaga', 'Away_Team': 'Baylor', 'Actual_Total': 158},
        {'Home_Team': 'Alabama', 'Away_Team': 'Auburn', 'Actual_Total': 172},
        
        # Medium-scoring teams
        {'Home_Team': 'Villanova', 'Away_Team': 'Connecticut', 'Actual_Total': 145},
        {'Home_Team': 'Kansas', 'Away_Team': 'Kentucky', 'Actual_Total': 152},
        {'Home_Team': 'Texas', 'Away_Team': 'Houston', 'Actual_Total': 138},
        
        # Lower-scoring teams
        {'Home_Team': 'Wisconsin', 'Away_Team': 'Michigan St.', 'Actual_Total': 128},
        {'Home_Team': 'Tennessee', 'Away_Team': 'Florida', 'Actual_Total': 134},
        {'Home_Team': 'Texas Tech', 'Away_Team': 'Maryland', 'Actual_Total': 125},
        
        # Mixed matchups
        {'Home_Team': 'Arizona', 'Away_Team': 'UCLA', 'Actual_Total': 149},
    ]
    
    return pd.DataFrame(games)


def main():
    """Test backtesting framework"""
    
    # Find most recent KenPom data
    kenpom_dir = "backend/data/raw/ncaab"
    
    if os.path.exists(kenpom_dir):
        csv_files = [f for f in os.listdir(kenpom_dir) if f.endswith('.csv')]
        if csv_files:
            latest_csv = max(csv_files)
            kenpom_path = os.path.join(kenpom_dir, latest_csv)
            
            print(f"Using KenPom data: {latest_csv}\n")
            
            # Create sample games (in production, would load from CSV)
            print("⚠️ Using sample games (10 games)")
            print("   In production, load historical games from CSV\n")
            sample_games = create_sample_games()
            
            # Run backtester
            backtester = NCAABBacktester(kenpom_data_path=kenpom_path)
            results = backtester.run(games_df=sample_games)
            
            if results:
                predictions, metrics = results
                
                print("\n🔍 Sample Predictions:")
                print("-"*70)
                print(predictions.head(10).to_string(index=False))
        else:
            print("❌ No KenPom CSV files found")
    else:
        print(f"❌ Directory not found: {kenpom_dir}")


if __name__ == "__main__":
    main()
