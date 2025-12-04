"""
DEMO: Test grading system with mock data
This demonstrates how the grading engine works
"""
import sqlite3
from pathlib import Path
from grading_engine import GradingEngine
import json

DB_PATH = Path(__file__).parent.parent.parent / "ml" / "predictions.db"

def insert_mock_results():
    """Insert mock game results for testing"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    mock_results = [
        # LeBron James - Lakers vs Celtics (Dec 2, 2025)
        ("2025-12-02", "game_001", "LeBron James", "LAL", "BOS", "nba", "points", 28.0),
        ("2025-12-02", "game_001", "LeBron James", "LAL", "BOS", "nba", "rebounds", 9.0),
        ("2025-12-02", "game_001", "LeBron James", "LAL", "BOS", "nba", "assists", 7.0),

        # Jayson Tatum - Celtics vs Lakers
        ("2025-12-02", "game_001", "Jayson Tatum", "BOS", "LAL", "nba", "points", 32.0),
        ("2025-12-02", "game_001", "Jayson Tatum", "BOS", "LAL", "nba", "rebounds", 8.0),
        ("2025-12-02", "game_001", "Jayson Tatum", "BOS", "LAL", "nba", "assists", 6.0),
    ]

    for result in mock_results:
        cursor.execute("""
            INSERT OR REPLACE INTO props_results
            (game_date, game_id, player_name, team, opponent, sport, prop_type, actual_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, result)

    conn.commit()
    conn.close()
    print("Inserted mock results for testing")

def check_predictions_exist():
    """Check if we have predictions for Dec 2"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count FROM player_props_predictions
        WHERE prediction_date = '2025-12-02'
    """)
    count = cursor.fetchone()[0]

    conn.close()
    return count

def show_sample_predictions():
    """Show sample predictions"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT player_name, prop_type, market_line, predicted_value,
               recommendation, confidence, edge_pct
        FROM player_props_predictions
        WHERE prediction_date = '2025-12-02'
        LIMIT 5
    """)

    print("\nSample Predictions for Dec 2:")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"  {row['player_name']} - {row['prop_type']}")
        print(f"    Line: {row['market_line']} | Predicted: {row['predicted_value']}")
        conf = f"{row['confidence']:.0%}" if row['confidence'] else "N/A"
        edge = f"{row['edge_pct']:.1f}%" if row['edge_pct'] else "N/A"
        print(f"    Rec: {row['recommendation']} | Confidence: {conf} | Edge: {edge}")

    conn.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GRADING ENGINE DEMO")
    print("="*80)

    # Check if predictions exist
    pred_count = check_predictions_exist()
    print(f"\nPredictions for Dec 2: {pred_count}")

    if pred_count > 0:
        show_sample_predictions()

        # Insert mock results
        print("\nInserting mock game results...")
        insert_mock_results()

        # Run grading
        print("\nGrading predictions and combos...")
        grader = GradingEngine()
        results = grader.grade_date("2025-12-02", sport="nba", fetch_results=False)

        # Display results
        print("\n" + "="*80)
        print("GRADING RESULTS")
        print("="*80)

        pred_results = results['predictions']
        print(f"\nPredictions:")
        print(f"  Total: {pred_results['total_predictions']}")
        print(f"  Graded: {pred_results['graded']}")
        print(f"  Correct: {pred_results['correct']}")
        print(f"  Incorrect: {pred_results['incorrect']}")
        print(f"  No Result: {pred_results['no_result']}")

        if pred_results['graded'] > 0:
            win_rate = (pred_results['correct'] / pred_results['graded']) * 100
            print(f"  Win Rate: {win_rate:.1f}%")

            # Show some examples
            print(f"\n  Examples:")
            for pred in pred_results['predictions'][:3]:
                print(f"    {pred['player_name']} {pred['prop_type']}: {pred['result']}")
                print(f"      Line: {pred['market_line']} | Actual: {pred['actual_value']} | Rec: {pred['recommendation']}")

        combo_results = results['combos']
        print(f"\nCombos:")
        print(f"  Total: {combo_results['total_combos']}")
        print(f"  Graded: {combo_results['graded']}")
        print(f"  Won: {combo_results['won']}")
        print(f"  Lost: {combo_results['lost']}")
        print(f"  No Result: {combo_results['no_result']}")

        if combo_results['graded'] > 0:
            win_rate = (combo_results['won'] / combo_results['graded']) * 100
            print(f"  Win Rate: {win_rate:.1f}%")

            # Show combo examples
            print(f"\n  Examples:")
            for combo in combo_results['combos'][:2]:
                print(f"    {combo['num_legs']}-leg combo: {combo['result']}")
                for leg in combo['legs']:
                    status = "[WIN]" if leg['hit'] else "[LOSS]"
                    print(f"      {status} {leg['player']} {leg['prop']} {leg['direction']} {leg['line']} (actual: {leg['actual']})")

    else:
        print("\nNo predictions found for Dec 2. Run predictor first:")
        print("    python backend/ml/props/predictor.py --sport nba")
