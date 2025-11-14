#!/usr/bin/env python3
"""
Script to update confidence calculation in edge_scanner.py
"""
import re

file_path = "routes/edge_scanner.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the old confidence calculation in load_edge_lab_predictions_old
old_pattern = r'''            sport = detect_sport\(row\['home_team'\], row\['away_team'\]\)
            edge = float\(row\['edge'\]\)
            confidence_map = \{'HIGH': 0\.75, 'MEDIUM': 0\.65, 'LOW': 0\.55, 'NONE': 0\.50\}
            confidence = confidence_map\.get\(str\(row\['confidence'\]\)\.upper\(\), 0\.65\)'''

# New dynamic confidence calculation
new_code = '''            sport = detect_sport(row['home_team'], row['away_team'])
            edge = float(row['edge'])

            # Calculate dynamic confidence based on edge size
            # Base confidence from category
            confidence_base = {'HIGH': 0.75, 'MEDIUM': 0.65, 'LOW': 0.55, 'NONE': 0.50}
            base = confidence_base.get(str(row['confidence']).upper(), 0.65)

            # Add edge-based adjustment (larger edges = higher confidence)
            # For totals: 2pts edge = +0%, 5pts = +10%, 10pts = +20%
            edge_adjustment = min(abs(edge) / 50.0, 0.20)

            # Also consider edge percentage relative to market
            predicted_total = float(row.get('predicted_total', 220.0))
            market_total = float(row.get('market_total', 220.0))
            edge_pct = abs(edge) / market_total if market_total > 0 else 0
            pct_adjustment = min(edge_pct * 0.5, 0.10)

            # Calculate final confidence (cap at 95%)
            confidence = min(base + edge_adjustment + pct_adjustment, 0.95)'''

# Replace the old pattern
new_content = re.sub(old_pattern, new_code, content, count=1)

if new_content != content:
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("[SUCCESS] Updated confidence calculation in load_edge_lab_predictions_old()")
else:
    print("[INFO] Pattern not found or already updated")
