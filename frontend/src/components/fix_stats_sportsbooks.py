import re

with open('GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix text-slate-200 (should be textPrimary for visibility)
# But skip green-400, red-400, yellow-400, blue-400 comparisons
content = re.sub(
    r"'text-slate-200'",
    r"textPrimary",
    content
)

# Also fix quoted text-slate-300 in inline conditionals
content = re.sub(
    r"'text-slate-300'",
    r"textSecondary",
    content
)

# Fix text-slate-400 in inline conditionals
content = re.sub(
    r"'text-slate-400'",
    r"textTertiary",
    content
)

# Now save
with open('GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully replaced all remaining text-slate colors in stats and sportsbook sections')
print('Replaced text-slate-200 with textPrimary')
print('Replaced text-slate-300 with textSecondary')
print('Replaced text-slate-400 with textTertiary')
