"""
Script to add empty_net and volatility_arb alert endpoints to main.py
"""

import re

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# New endpoints to add
new_endpoints = '''

@app.get("/api/alerts/empty-net")
async def get_empty_net_alerts(user_id: str = 'default'):
    """Get NHL empty net / goalie pull alerts"""
    try:
        # Get empty net alerts from storage (status='pending' means active)
        tracked_alerts = alert_storage.get_alerts_by_type('empty_net', status='pending', limit=50)

        # Convert to response format
        alerts = []
        for tracked_alert in tracked_alerts:
            details = tracked_alert.strategy_details or {}

            alerts.append({
                'id': tracked_alert.id,
                'game_id': tracked_alert.game_id,
                'sport': tracked_alert.sport,
                'home_team': tracked_alert.home_team,
                'away_team': tracked_alert.away_team,
                'commence_time': tracked_alert.commence_time,
                'market_type': tracked_alert.market_type,
                'recommended_side': tracked_alert.recommended_side,
                'recommended_odds': tracked_alert.recommended_odds,
                'recommended_bookmaker': tracked_alert.recommended_bookmaker,
                'confidence': tracked_alert.confidence,
                'edge_percent': tracked_alert.edge_percent,
                'profit_potential': tracked_alert.profit_potential,
                'generated_at': tracked_alert.generated_at,
                'status': tracked_alert.status,
                'strategy_details': details
            })

        return {
            'count': len(alerts),
            'alerts': alerts,
            'alert_type': 'empty_net'
        }

    except Exception as e:
        logger.error(f"Error getting empty net alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/volatility-arb")
async def get_volatility_arb_alerts(user_id: str = 'default'):
    """Get volatility arbitrage hedge alerts"""
    try:
        # Get volatility arb alerts from storage (status='pending' means active hedge opportunity)
        tracked_alerts = alert_storage.get_alerts_by_type('volatility_arb', status='pending', limit=50)

        # Convert to response format
        alerts = []
        for tracked_alert in tracked_alerts:
            details = tracked_alert.strategy_details or {}

            alerts.append({
                'id': tracked_alert.id,
                'game_id': tracked_alert.game_id,
                'sport': tracked_alert.sport,
                'home_team': tracked_alert.home_team,
                'away_team': tracked_alert.away_team,
                'commence_time': tracked_alert.commence_time,
                'market_type': tracked_alert.market_type,
                'recommended_side': tracked_alert.recommended_side,
                'recommended_odds': tracked_alert.recommended_odds,
                'recommended_bookmaker': tracked_alert.recommended_bookmaker,
                'confidence': tracked_alert.confidence,
                'edge_percent': tracked_alert.edge_percent,
                'profit_potential': tracked_alert.profit_potential,
                'generated_at': tracked_alert.generated_at,
                'status': tracked_alert.status,
                'strategy_details': details
            })

        return {
            'count': len(alerts),
            'alerts': alerts,
            'alert_type': 'volatility_arb'
        }

    except Exception as e:
        logger.error(f"Error getting volatility arb alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

'''

# Find where to insert (after the schedule-fatigue endpoint)
pattern = r'(@app\.get\("/api/alerts/schedule-fatigue"\).*?raise HTTPException\(status_code=500, detail=str\(e\)\))'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert after the schedule-fatigue endpoint
    insert_pos = match.end()
    new_content = content[:insert_pos] + new_endpoints + content[insert_pos:]

    # Write back
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Successfully added empty_net and volatility_arb alert endpoints to main.py")
else:
    print("❌ Could not find insertion point in main.py")
