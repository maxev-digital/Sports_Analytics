#!/usr/bin/env python3
"""
Performance Tracker for NBA Totals Model
Track predictions vs actual results to measure model accuracy
"""

import pandas as pd
import os
from datetime import datetime

class PerformanceTracker:
    """Track model performance over time"""
    
    def __init__(self):
        self.predictions_log = 'backend/data/tracking/predictions_log.csv'
        self.results_log = 'backend/data/tracking/results_log.csv'
        self.performance_log = 'backend/data/tracking/performance_summary.csv'
        
        # Create directories
        os.makedirs('backend/data/tracking', exist_ok=True)
        
        # Initialize logs if they don't exist
        self._initialize_logs()
    
    def _initialize_logs(self):
        """Create log files if they don't exist"""
        
        # Predictions log
        if not os.path.exists(self.predictions_log):
            df = pd.DataFrame(columns=[
                'prediction_id', 'date_predicted', 'game_date', 'game_time',
                'away_team', 'home_team', 'predicted_total', 'market_total',
                'edge', 'recommendation', 'confidence', 'bet_placed'
            ])
            df.to_csv(self.predictions_log, index=False)
            print(f"✓ Created predictions log: {self.predictions_log}")
        
        # Results log
        if not os.path.exists(self.results_log):
            df = pd.DataFrame(columns=[
                'prediction_id', 'game_date', 'away_team', 'home_team',
                'away_score', 'home_score', 'actual_total', 'market_total',
                'predicted_total', 'recommendation', 'confidence',
                'result', 'edge_accuracy', 'profit_loss'
            ])
            df.to_csv(self.results_log, index=False)
            print(f"✓ Created results log: {self.results_log}")
        
        # Performance summary
        if not os.path.exists(self.performance_log):
            df = pd.DataFrame(columns=[
                'date', 'total_bets', 'wins', 'losses', 'win_rate',
                'avg_edge', 'roi', 'units_won', 'high_conf_win_rate',
                'medium_conf_win_rate', 'low_conf_win_rate'
            ])
            df.to_csv(self.performance_log, index=False)
            print(f"✓ Created performance log: {self.performance_log}")
    
    def log_predictions(self, predictions_csv='backend/data/predictions/nba_predictions_latest.csv'):
        """Log predictions for tracking"""
        print("\n📝 Logging predictions for tracking...")
        
        if not os.path.exists(predictions_csv):
            print(f"❌ Predictions file not found: {predictions_csv}")
            return
        
        # Load predictions
        new_preds = pd.read_csv(predictions_csv)
        
        # Load existing log
        existing_log = pd.read_csv(self.predictions_log)
        
        # Add metadata
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for _, pred in new_preds.iterrows():
            # Create unique ID
            pred_id = f"{pred['game_date']}_{pred['away_team']}_{pred['home_team']}".replace(' ', '_')
            
            # Check if already logged
            if pred_id in existing_log['prediction_id'].values:
                continue
            
            # Add to log
            new_row = {
                'prediction_id': pred_id,
                'date_predicted': timestamp,
                'game_date': pred['game_date'],
                'game_time': pred['game_time'],
                'away_team': pred['away_team'],
                'home_team': pred['home_team'],
                'predicted_total': pred['predicted_total'],
                'market_total': pred['market_total'],
                'edge': pred['edge'],
                'recommendation': pred['recommendation'],
                'confidence': pred['confidence'],
                'bet_placed': 'YES' if pred['bet'] == 'YES' else 'NO'
            }
            
            existing_log = pd.concat([existing_log, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save updated log
        existing_log.to_csv(self.predictions_log, index=False)
        
        new_count = len(new_preds)
        total_count = len(existing_log)
        
        print(f"✓ Logged {new_count} new predictions")
        print(f"✓ Total predictions tracked: {total_count}")
        
        return existing_log
    
    def record_results(self):
        """Interactive tool to record actual game results"""
        print("\n" + "="*70)
        print("RECORD GAME RESULTS")
        print("="*70)
        
        # Load predictions log
        preds_df = pd.read_csv(self.predictions_log)
        results_df = pd.read_csv(self.results_log)
        
        # Find games that need results
        recorded_ids = results_df['prediction_id'].values
        pending = preds_df[~preds_df['prediction_id'].isin(recorded_ids)]
        
        # Filter to past games only
        today = datetime.now().date()
        pending['game_date_dt'] = pd.to_datetime(pending['game_date']).dt.date
        pending = pending[pending['game_date_dt'] < today]
        
        if len(pending) == 0:
            print("✓ No pending results to record!")
            return
        
        print(f"\n📋 Found {len(pending)} games needing results:\n")
        
        for idx, game in pending.iterrows():
            print(f"\n{'='*70}")
            print(f"Game: {game['away_team']} @ {game['home_team']}")
            print(f"Date: {game['game_date']}")
            print(f"Prediction: {game['recommendation']} {game['market_total']} (Edge: {game['edge']})")
            print(f"Confidence: {game['confidence']}")
            print(f"{'='*70}")
            
            # Ask if user wants to record this game
            record = input("\nRecord results for this game? (y/n/skip all): ").strip().lower()
            
            if record == 'skip all':
                break
            
            if record != 'y':
                continue
            
            # Get scores
            try:
                away_score = int(input(f"  {game['away_team']} score: "))
                home_score = int(input(f"  {game['home_team']} score: "))
                
                actual_total = away_score + home_score
                
                # Determine result
                if game['recommendation'] == 'OVER':
                    result = 'WIN' if actual_total > game['market_total'] else 'LOSS'
                    if actual_total == game['market_total']:
                        result = 'PUSH'
                else:  # UNDER
                    result = 'WIN' if actual_total < game['market_total'] else 'LOSS'
                    if actual_total == game['market_total']:
                        result = 'PUSH'
                
                # Edge accuracy
                edge_accuracy = abs(game['predicted_total'] - actual_total)
                
                # Profit/Loss (assume 1 unit bets, -110 odds)
                if result == 'WIN':
                    profit_loss = 0.91  # Win 0.91 units on -110
                elif result == 'LOSS':
                    profit_loss = -1.0
                else:  # PUSH
                    profit_loss = 0.0
                
                # Record result
                result_row = {
                    'prediction_id': game['prediction_id'],
                    'game_date': game['game_date'],
                    'away_team': game['away_team'],
                    'home_team': game['home_team'],
                    'away_score': away_score,
                    'home_score': home_score,
                    'actual_total': actual_total,
                    'market_total': game['market_total'],
                    'predicted_total': game['predicted_total'],
                    'recommendation': game['recommendation'],
                    'confidence': game['confidence'],
                    'result': result,
                    'edge_accuracy': edge_accuracy,
                    'profit_loss': profit_loss
                }
                
                results_df = pd.concat([results_df, pd.DataFrame([result_row])], ignore_index=True)
                
                print(f"\n  ✓ Recorded: {result}")
                print(f"  Actual Total: {actual_total}")
                print(f"  Predicted: {game['predicted_total']:.1f} | Market: {game['market_total']}")
                print(f"  Edge Accuracy: {edge_accuracy:.1f} points off")
                
            except ValueError:
                print("❌ Invalid input, skipping...")
                continue
        
        # Save results
        results_df.to_csv(self.results_log, index=False)
        print(f"\n✓ Results saved to: {self.results_log}")
        
        # Calculate and display stats
        self.calculate_performance()
    
    def calculate_performance(self):
        """Calculate performance metrics"""
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        
        results_df = pd.read_csv(self.results_log)
        
        if len(results_df) == 0:
            print("⚠️  No results recorded yet")
            return
        
        # Overall stats
        total_bets = len(results_df)
        wins = len(results_df[results_df['result'] == 'WIN'])
        losses = len(results_df[results_df['result'] == 'LOSS'])
        pushes = len(results_df[results_df['result'] == 'PUSH'])
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        # Units won/lost
        units = results_df['profit_loss'].sum()
        
        # ROI (assumes -110 odds, 1 unit per bet)
        roi = (units / total_bets * 100) if total_bets > 0 else 0
        
        # Edge accuracy
        avg_edge_error = results_df['edge_accuracy'].mean()
        
        print(f"\n📊 Overall Performance:")
        print(f"  Total Bets: {total_bets}")
        print(f"  Wins: {wins} | Losses: {losses} | Pushes: {pushes}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Units Won/Lost: {units:+.2f}")
        print(f"  ROI: {roi:+.1f}%")
        print(f"  Avg Edge Error: {avg_edge_error:.1f} points")
        
        # By confidence level
        print(f"\n📈 Performance by Confidence:")
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            conf_df = results_df[results_df['confidence'] == conf]
            if len(conf_df) > 0:
                conf_wins = len(conf_df[conf_df['result'] == 'WIN'])
                conf_losses = len(conf_df[conf_df['result'] == 'LOSS'])
                conf_wr = (conf_wins / (conf_wins + conf_losses) * 100) if (conf_wins + conf_losses) > 0 else 0
                conf_units = conf_df['profit_loss'].sum()
                
                print(f"  {conf}: {conf_wins}-{conf_losses} ({conf_wr:.1f}%) | Units: {conf_units:+.2f}")
        
        # Recent performance (last 10 bets)
        if len(results_df) >= 10:
            recent = results_df.tail(10)
            recent_wins = len(recent[recent['result'] == 'WIN'])
            recent_losses = len(recent[recent['result'] == 'LOSS'])
            recent_wr = (recent_wins / (recent_wins + recent_losses) * 100) if (recent_wins + recent_losses) > 0 else 0
            
            print(f"\n🔥 Last 10 Bets: {recent_wins}-{recent_losses} ({recent_wr:.1f}%)")
        
        # Save performance summary
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 1),
            'avg_edge': round(results_df['edge'].mean(), 1) if 'edge' in results_df.columns else 0,
            'roi': round(roi, 1),
            'units_won': round(units, 2),
            'high_conf_win_rate': round(
                len(results_df[(results_df['confidence']=='HIGH') & (results_df['result']=='WIN')]) / 
                len(results_df[results_df['confidence']=='HIGH']) * 100, 1
            ) if len(results_df[results_df['confidence']=='HIGH']) > 0 else 0,
            'medium_conf_win_rate': round(
                len(results_df[(results_df['confidence']=='MEDIUM') & (results_df['result']=='WIN')]) / 
                len(results_df[results_df['confidence']=='MEDIUM']) * 100, 1
            ) if len(results_df[results_df['confidence']=='MEDIUM']) > 0 else 0,
            'low_conf_win_rate': round(
                len(results_df[(results_df['confidence']=='LOW') & (results_df['result']=='WIN')]) / 
                len(results_df[results_df['confidence']=='LOW']) * 100, 1
            ) if len(results_df[results_df['confidence']=='LOW']) > 0 else 0
        }
        
        perf_df = pd.read_csv(self.performance_log)
        perf_df = pd.concat([perf_df, pd.DataFrame([summary])], ignore_index=True)
        perf_df.to_csv(self.performance_log, index=False)
        
        print(f"\n✓ Performance saved to: {self.performance_log}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if total_bets < 50:
            print(f"  ⚠️  Sample size too small ({total_bets} bets). Need 50+ for validation.")
        elif win_rate >= 54:
            print(f"  ✅ Excellent win rate! Model is performing well.")
        elif win_rate >= 52:
            print(f"  ✅ Good win rate. Continue tracking.")
        elif win_rate >= 50:
            print(f"  ⚠️  Marginal performance. Monitor closely.")
        else:
            print(f"  ❌ Poor performance. Model needs adjustment or more data.")


def main():
    """Interactive performance tracker"""
    tracker = PerformanceTracker()
    
    print("="*70)
    print("NBA TOTALS PERFORMANCE TRACKER")
    print("="*70)
    print("\nOptions:")
    print("1. Log today's predictions")
    print("2. Record game results")
    print("3. View performance summary")
    print("4. Export to CSV")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        tracker.log_predictions()
    elif choice == '2':
        tracker.record_results()
    elif choice == '3':
        tracker.calculate_performance()
    elif choice == '4':
        print("\n📁 Data files:")
        print(f"  Predictions: {tracker.predictions_log}")
        print(f"  Results: {tracker.results_log}")
        print(f"  Performance: {tracker.performance_log}")
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()