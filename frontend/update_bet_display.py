#!/usr/bin/env python3
"""
Update MaxEvEdges.tsx to show Favorite/Underdog for spreads and improve team display
"""
import re

file_path = "src/pages/MaxEvEdges.tsx"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section that displays the Bet column (around line 556-564)
# We need to add logic to convert HOME/AWAY to Favorite/Underdog for spreads

# First, let's add a helper function to compute the bet label
# Find the component function start and add helper function after imports

helper_function = '''
  // Helper function to get bet label for display
  const getBetLabel = (play: any) => {
    const { bet_type, recommendation, market_line } = play;

    // For totals, show OVER/UNDER as-is
    if (bet_type === 'totals') {
      return recommendation;
    }

    // For spreads, convert HOME/AWAY to Favorite/Underdog
    if (bet_type === 'spreads') {
      // Negative spread means home is favored
      const homeIsFavorite = market_line < 0;

      if (recommendation === 'HOME') {
        return homeIsFavorite ? 'Favorite' : 'Underdog';
      } else if (recommendation === 'AWAY') {
        return homeIsFavorite ? 'Underdog' : 'Favorite';
      }
    }

    // For moneyline, return the recommendation as-is
    return recommendation;
  };

'''

# Find where to insert the helper function (after the component starts)
# Look for "export default function MaxEvEdges"
component_start = content.find('export default function MaxEvEdges')
if component_start != -1:
    # Find the opening brace of the function
    brace_pos = content.find('{', component_start)
    if brace_pos != -1:
        # Insert helper function after the opening brace
        content = content[:brace_pos+1] + '\n' + helper_function + content[brace_pos+1:]

# Now update the Bet column display to use getBetLabel
old_bet_display = '''                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className={`font-bold text-base ${
                                play.recommendation === 'OVER' || play.recommendation === 'HOME' ? 'text-green-400' :
                                play.recommendation === 'UNDER' || play.recommendation === 'AWAY' ? 'text-red-400' :
                                'text-yellow-400'
                              }`}>
                                {play.recommendation}
                              </div>
                            </td>'''

new_bet_display = '''                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className={`font-bold text-base ${
                                play.recommendation === 'OVER' || play.recommendation === 'HOME' ? 'text-green-400' :
                                play.recommendation === 'UNDER' || play.recommendation === 'AWAY' ? 'text-red-400' :
                                'text-yellow-400'
                              }`}>
                                {getBetLabel(play)}
                              </div>
                            </td>'''

content = content.replace(old_bet_display, new_bet_display)

# Now update the Game column to show spread info more clearly
old_game_display = '''                            <td className="py-3 px-3 border-r border-slate-600">
                              <div className="text-white font-semibold text-sm">
                                {play.away_team} @ {play.home_team}
                              </div>
                              <div className="text-slate-400 text-xs mt-0.5">
                                {formatGameTime(play.game_time)}
                              </div>
                            </td>'''

new_game_display = '''                            <td className="py-3 px-3 border-r border-slate-600">
                              <div className="text-white font-semibold text-sm">
                                {play.away_team} @ {play.home_team}
                                {play.bet_type === 'spreads' && (
                                  <span className="ml-2 text-xs text-slate-400">
                                    ({play.market_line < 0
                                      ? `${play.home_team} ${play.market_line}`
                                      : `${play.away_team} +${Math.abs(play.market_line)}`})
                                  </span>
                                )}
                              </div>
                              <div className="text-slate-400 text-xs mt-0.5">
                                {formatGameTime(play.game_time)}
                              </div>
                            </td>'''

content = content.replace(old_game_display, new_game_display)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('[SUCCESS] Updated MaxEvEdges.tsx')
print('  - Added getBetLabel helper function')
print('  - Bet column now shows Favorite/Underdog for spreads')
print('  - Game column now shows which team is favored and the spread')
