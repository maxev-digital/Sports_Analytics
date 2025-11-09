"""
Quick analysis script to parse injury cascade output and calculate OVER rates
"""

# Sample output data captured from the scraper
output_text = """
[OPPORTUNITY] Scottie Barnes (19.9 PPG) played only 29 min
  Game: Milwaukee Bucks @ Toronto Raptors on 2023-11-01
  Substitute: Jakob Poeltl (29 min)
    PTS: 14 vs 11.1 avg (OVER)
    REB: 11 vs 8.6 avg (OVER)
    AST: 2 vs 2.5 avg (UNDER)
  Substitute: Gradey Dick (21 min)
    PTS: 5 vs 8.5 avg (UNDER)
    REB: 1 vs 2.2 avg (UNDER)
    AST: 0 vs 1.1 avg (UNDER)
  Substitute: Otto Porter Jr. (16 min)
    PTS: 6 vs 2.6 avg (OVER)
    REB: 3 vs 2.0 avg (OVER)
    AST: 1 vs 0.5 avg (OVER)

[OPPORTUNITY] Giannis Antetokounmpo (30.4 PPG) played only 28 min
  Game: Milwaukee Bucks @ Toronto Raptors on 2023-11-01
  Substitute: Gary Trent Jr. (23 min)
    PTS: 8 vs 13.7 avg (UNDER)
    REB: 3 vs 2.6 avg (OVER)
    AST: 1 vs 1.7 avg (UNDER)
  Substitute: Bobby Portis (19 min)
    PTS: 10 vs 13.8 avg (UNDER)
    REB: 6 vs 7.4 avg (UNDER)
    AST: 1 vs 1.3 avg (UNDER)

[OPPORTUNITY] Jayson Tatum (26.8 PPG) played only 27 min
  Game: Indiana Pacers @ Boston Celtics on 2023-11-01
  Substitute: Jaylen Brown (25 min)
    PTS: 16 vs 23.0 avg (UNDER)
    REB: 7 vs 5.5 avg (OVER)
    AST: 1 vs 3.6 avg (UNDER)
  Substitute: Derrick White (27 min)
    PTS: 18 vs 15.2 avg (OVER)
    REB: 3 vs 4.2 avg (UNDER)
    AST: 4 vs 5.2 avg (UNDER)
  Substitute: Sam Hauser (20 min)
    PTS: 17 vs 9.0 avg (OVER)
    REB: 3 vs 3.5 avg (UNDER)
    AST: 0 vs 1.0 avg (UNDER)
  Substitute: Payton Pritchard (26 min)
    PTS: 15 vs 9.6 avg (OVER)
    REB: 4 vs 3.2 avg (OVER)
    AST: 9 vs 3.4 avg (OVER)

[OPPORTUNITY] Tyrese Haliburton (20.1 PPG) played only 0 min
  Game: Indiana Pacers @ Boston Celtics on 2023-11-01
  Substitute: T.J. McConnell (28 min)
    PTS: 18 vs 10.2 avg (OVER)
    REB: 7 vs 2.7 avg (OVER)
    AST: 5 vs 5.5 avg (UNDER)

[OPPORTUNITY] Shai Gilgeous-Alexander (30.1 PPG) played only 0 min
  Game: Golden State Warriors @ Oklahoma City Thunder on 2023-11-03
  Substitute: Luguentz Dort (30 min)
    PTS: 29 vs 10.9 avg (OVER)
    REB: 5 vs 3.6 avg (OVER)
    AST: 0 vs 1.4 avg (UNDER)
  Substitute: Chet Holmgren (32 min)
    PTS: 24 vs 16.5 avg (OVER)
    REB: 8 vs 7.9 avg (OVER)
    AST: 5 vs 2.4 avg (OVER)
  Substitute: Cason Wallace (36 min)
    PTS: 13 vs 6.8 avg (OVER)
    REB: 2 vs 2.3 avg (UNDER)
    AST: 1 vs 1.5 avg (UNDER)

[OPPORTUNITY] LeBron James (25.6 PPG) played only 0 min
  Game: Portland Trail Blazers @ Los Angeles Lakers on 2023-11-12
  Substitute: Cameron Reddish (38 min)
    PTS: 18 vs 5.5 avg (OVER)
    REB: 7 vs 2.1 avg (OVER)
    AST: 2 vs 1.0 avg (OVER)
  Substitute: Rui Hachimura (33 min)
    PTS: 19 vs 13.4 avg (OVER)
    REB: 5 vs 4.3 avg (OVER)
    AST: 2 vs 1.2 avg (OVER)
  Substitute: Skylar Mays (33 min)
    PTS: 15 vs 4.1 avg (OVER)
    REB: 4 vs 1.1 avg (OVER)
    AST: 12 vs 2.2 avg (OVER)

[OPPORTUNITY] Stephen Curry (26.4 PPG) played only 0 min
  Game: Minnesota Timberwolves @ Golden State Warriors on 2023-11-14
  Substitute: Brandin Podziemski (39 min)
    PTS: 23 vs 9.2 avg (OVER)
    REB: 7 vs 5.8 avg (OVER)
    AST: 5 vs 3.6 avg (OVER)

[OPPORTUNITY] Devin Booker (27.1 PPG) played only 0 min
  Game: Phoenix Suns @ Chicago Bulls on 2023-11-08
  Substitute: Grayson Allen (37 min)
    PTS: 26 vs 13.5 avg (OVER)
    REB: 9 vs 3.9 avg (OVER)
    AST: 4 vs 3.0 avg (OVER)

[OPPORTUNITY] Tyler Herro (21.0 PPG) played only 0 min
  Game: Miami Heat @ Atlanta Hawks on 2023-11-11
  Substitute: Bam Adebayo (39 min)
    PTS: 26 vs 19.0 avg (OVER)
    REB: 16 vs 10.3 avg (OVER)
    AST: 4 vs 3.9 avg (OVER)
  Substitute: Josh Richardson (23 min)
    PTS: 16 vs 9.9 avg (OVER)
    REB: 2 vs 2.8 avg (UNDER)
    AST: 0 vs 2.4 avg (UNDER)
"""

import re

# Parse the output
pts_over = 0
pts_under = 0
reb_over = 0
reb_under = 0
ast_over = 0
ast_under = 0

# Split by lines and process
lines = output_text.strip().split('\n')

for line in lines:
    if 'PTS:' in line and '(OVER)' in line:
        pts_over += 1
    elif 'PTS:' in line and '(UNDER)' in line:
        pts_under += 1

    if 'REB:' in line and '(OVER)' in line:
        reb_over += 1
    elif 'REB:' in line and '(UNDER)' in line:
        reb_under += 1

    if 'AST:' in line and '(OVER)' in line:
        ast_over += 1
    elif 'AST:' in line and '(UNDER)' in line:
        ast_under += 1

# Calculate rates
total_pts = pts_over + pts_under
total_reb = reb_over + reb_under
total_ast = ast_over + ast_under

pts_rate = (pts_over / total_pts * 100) if total_pts > 0 else 0
reb_rate = (reb_over / total_reb * 100) if total_reb > 0 else 0
ast_rate = (ast_over / total_ast * 100) if total_ast > 0 else 0

print("="*80)
print("INJURY CASCADE - PROP TYPE ANALYSIS (Sample Data)")
print("="*80)
print()
print("POINTS (PTS):")
print(f"  OVER: {pts_over}")
print(f"  UNDER: {pts_under}")
print(f"  Total: {total_pts}")
print(f"  OVER Rate: {pts_rate:.1f}%")
print()
print("REBOUNDS (REB):")
print(f"  OVER: {reb_over}")
print(f"  UNDER: {reb_under}")
print(f"  Total: {total_reb}")
print(f"  OVER Rate: {reb_rate:.1f}%")
print()
print("ASSISTS (AST):")
print(f"  OVER: {ast_over}")
print(f"  UNDER: {ast_under}")
print(f"  Total: {total_ast}")
print(f"  OVER Rate: {ast_rate:.1f}%")
print()
print("="*80)
print("STRATEGY RECOMMENDATIONS:")
print("="*80)

if pts_rate >= 58:
    print(f"✅ PTS props: STRONG EDGE ({pts_rate:.1f}% OVER rate)")
else:
    print(f"⚠️  PTS props: {pts_rate:.1f}% OVER rate - needs more data")

if reb_rate >= 58:
    print(f"✅ REB props: STRONG EDGE ({reb_rate:.1f}% OVER rate)")
elif reb_rate >= 52:
    print(f"🟡 REB props: MODERATE EDGE ({reb_rate:.1f}% OVER rate)")
else:
    print(f"❌ REB props: NO EDGE ({reb_rate:.1f}% OVER rate)")

if ast_rate >= 58:
    print(f"✅ AST props: STRONG EDGE ({ast_rate:.1f}% OVER rate)")
elif ast_rate >= 52:
    print(f"🟡 AST props: MODERATE EDGE ({ast_rate:.1f}% OVER rate)")
else:
    print(f"❌ AST props: NO EDGE ({ast_rate:.1f}% OVER rate)")

print()
print("NOTE: This is a small sample from the failed run. Full November data needed for definitive results.")
