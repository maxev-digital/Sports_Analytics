import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Remove duplicate isNHL checks in line 363 (status badge)
content = re.sub(
    r": isNHL \? 'bg-gray-200 text-black' : isNHL \? `bg-gray-200 \$\{textValue\}` : `bg-slate-700 text-slate-300`",
    r": isNHL ? 'bg-gray-200 text-black' : `bg-slate-700 text-slate-300`",
    content
)

# Fix 2: Remove duplicate isNHL checks in button styles (lines 789, 799, 809, 1076, 1086, 1096)
content = re.sub(
    r": isNHL \? 'bg-gray-200 text-black hover:bg-gray-300 font-bold' : isNHL \? 'bg-gray-200 text-black hover:bg-gray-300 font-bold' : 'bg-slate-700 text-slate-([34])00 hover:bg-slate-600'",
    r": isNHL ? 'bg-gray-200 text-black hover:bg-gray-300 font-bold' : 'bg-slate-700 text-slate-\100 hover:bg-slate-600'",
    content
)

# Fix 3: Fix nested ternary operators for momentum scores (lines 641, 713)
# These are: > 60 ? green : < 40 ? red : slate-300
# For NHL, we want the slate-300 to be black
content = re.sub(
    r"(momentum_score > 60 \? 'text-green-400' :[\s\n]+\s+\w+_nhl_momentum\.momentum_score < 40 \? 'text-red-400' :[\s\n]+\s+)'text-slate-300'",
    r"\1isNHL ? 'text-black font-bold' : 'text-slate-300'",
    content
)

# Fix 4: For all remaining standalone 'text-slate-300' in ternary expressions within NHL sections
# This targets stat comparisons like: better_stat ? 'text-green-400' : 'text-slate-300'
# We need to check if we're in an NHL section and replace accordingly

# First, let's handle lines within NHL-specific sections (sportBadge === 'NHL')
# These sections start around line 630 (NHL Momentum) and line 778 (NHL Season Stats)

# Actually, a simpler approach: replace remaining 'text-slate-300' that are the last option in ternary
# but only in contexts where it's comparing stats (has 'text-green-400' before it)
content = re.sub(
    r"'text-green-400'(\s+:\s+)'text-slate-300'(\s*})",
    r"'text-green-400'\1isNHL ? 'text-black font-bold' : 'text-slate-300'\2",
    content
)

with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed:")
print("  - Removed duplicate isNHL checks")
print("  - Fixed nested ternary operators for momentum scores")
print("  - Updated stat comparison fallbacks to use black text for NHL")
