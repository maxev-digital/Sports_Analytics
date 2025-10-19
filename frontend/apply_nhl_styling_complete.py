import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add imports if they don't exist
if 'detectSport' not in content:
    content = re.sub(
        r"(import \{ LiveGame \} from '../types';)",
        r"\1\nimport { detectSport, getSportEmoji, getSportGradientClasses, getSportBorderClass } from '../utils/sportDetection';",
        content
    )
    print("Added sport detection imports")

# Step 2: Find and replace the sport styling section
old_sport_vars = r'''  const sport = detectSport\(game\);
  const sportGradient = getSportGradientClasses\(sport\);
  const sportBorder = getSportBorderClass\(sport\);
  const sportEmoji = getSportEmoji\(sport\);

  return \(
    <div className=\{`\$\{sportGradient\} rounded-lg p-4 border-2 \$\{sportBorder\} hover:shadow-xl transition-all hover:-translate-y-0\.5`\} style=\{\{ boxShadow: '0 4px 6px rgba\(0, 0, 0, 0\.3\)' \}\}>'''

new_sport_vars = '''  const sport = detectSport(game);
  const sportGradient = getSportGradientClasses(sport);
  const sportBorder = getSportBorderClass(sport);
  const sportEmoji = getSportEmoji(sport);

  // NHL-specific styling: white background, ALL black text, thick red border, hockey rink lines
  const isNHL = sport === 'NHL';
  const cardBackground = isNHL ? 'bg-white' : sportGradient;
  const cardBorder = isNHL ? 'border-red-600 border-4' : `border-2 ${sportBorder}`;
  const cardRounding = isNHL ? 'rounded-3xl' : 'rounded-lg';
  const textPrimary = isNHL ? 'text-black' : 'text-white';
  const textSecondary = isNHL ? 'text-black font-bold' : 'text-slate-300';
  const textTertiary = isNHL ? 'text-black font-bold' : 'text-slate-400';
  const textLabel = isNHL ? 'text-black font-semibold' : 'text-slate-400';
  const textValue = isNHL ? 'text-black font-bold' : 'text-slate-200';
  const textHeader = isNHL ? 'text-black font-bold' : 'text-slate-100';
  const textMuted = isNHL ? 'text-gray-600' : 'text-slate-500';
  const dividerBorder = isNHL ? 'border-gray-300' : 'border-slate-700';

  return (
    <div
      className={`${cardBackground} ${cardRounding} p-4 ${cardBorder} hover:shadow-xl transition-all hover:-translate-y-0.5 relative overflow-hidden`}
      style={{ boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)' }}
    >
      {/* Hockey Rink Lines (NHL only) */}
      {isNHL && (
        <div className="absolute inset-0 pointer-events-none opacity-10">
          {/* Center red line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-red-600 transform -translate-x-1/2"></div>
          {/* Blue lines */}
          <div className="absolute left-1/4 top-0 bottom-0 w-0.5 bg-blue-600"></div>
          <div className="absolute left-3/4 top-0 bottom-0 w-0.5 bg-blue-600"></div>
          {/* Face-off circles */}
          <div className="absolute left-1/4 top-1/2 w-16 h-16 border-2 border-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute left-3/4 top-1/2 w-16 h-16 border-2 border-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
          {/* Center ice circle */}
          <div className="absolute left-1/2 top-1/2 w-20 h-20 border-2 border-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute left-1/2 top-1/2 w-3 h-3 bg-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
        </div>
      )}'''

if 'const sport = detectSport(game);' in content:
    content = re.sub(old_sport_vars, new_sport_vars, content, flags=re.DOTALL)
    print("Added NHL-specific styling variables and hockey rink overlay")

# Step 3: Update header to have z-index for layering above rink lines
content = re.sub(
    r'<div className="flex justify-between items-start mb-3">',
    r'<div className="flex justify-between items-start mb-3 relative z-10">',
    content
)

# Step 4: Update team names to use conditional textPrimary
content = re.sub(
    r'<span className="font-medium text-white">(\{state\.away_team\.name\})</span>',
    r'<span className={`font-medium ${textPrimary}`}>\1</span>',
    content
)
content = re.sub(
    r'<span className="font-medium text-white">(\{state\.home_team\.name\})</span>',
    r'<span className={`font-medium ${textPrimary}`}>\1</span>',
    content
)

# Step 5: Update scores to use conditional textPrimary
content = re.sub(
    r'<span className="text-xl font-bold text-white">(\{state\.away_team\.score\})</span>',
    r'<span className={`text-xl font-bold ${textPrimary}`}>\1</span>',
    content
)
content = re.sub(
    r'<span className="text-xl font-bold text-white">(\{state\.home_team\.score\})</span>',
    r'<span className={`text-xl font-bold ${textPrimary}`}>\1</span>',
    content
)

# Step 6: Change "Spread" to "Puck Line" for NHL
content = re.sub(
    r"<span className=\"text-slate-400\">Spread: </span>",
    r'<span className={textTertiary}>{isNHL ? "Puck Line: " : "Spread: "}</span>',
    content
)

with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nNHL styling applied successfully!")
print("- White background with thick red border (border-4)")
print("- ALL BLACK TEXT (font-bold) for maximum visibility")
print("- Hockey rink lines overlay at 10% opacity")
print("- Bigger rounded corners (rounded-3xl)")
print('- "Puck Line" label instead of "Spread" for NHL')
print("\nReady to test!")
