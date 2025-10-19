import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix team headers in momentum sections (lines 633, 705)
content = re.sub(
    r'<div className="text-slate-400 font-semibold mb-1">',
    r'<div className={`${textLabel} mb-1`}>',
    content
)

# 2. Fix stat comparison "else" cases - replace 'text-slate-300' with ${textValue}
# These are in ternary operators where the stat isn't winning
content = re.sub(
    r"'text-slate-300'(\s*}\s*>)",
    r'`${textValue}`\1',
    content
)

# 3. Fix possession indicator badges for NHL
content = re.sub(
    r"'bg-slate-700 text-slate-300'",
    r'isNHL ? `bg-gray-200 ${textValue}` : `bg-slate-700 text-slate-300`',
    content
)

# 4. Fix team abbreviations in score section (lines 440, 466, 595, 621)
content = re.sub(
    r'<span className="text-xs text-slate-400 w-12">',
    r'<span className={`text-xs ${textLabel} w-12`}>',
    content
)
content = re.sub(
    r'<span className="text-xs text-slate-400 w-12 text-right">',
    r'<span className={`text-xs ${textLabel} w-12 text-right`}>',
    content
)

# 5. Fix buttons with bg-slate-700 text-slate-300 (lines 789, 799, 809, etc.)
content = re.sub(
    r": 'bg-slate-700 text-slate-300 hover:bg-slate-600'",
    r": isNHL ? 'bg-gray-200 text-black hover:bg-gray-300 font-bold' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'",
    content
)

# 6. Fix buttons with bg-slate-700 text-slate-400 (lines 1076, 1086, 1096)
content = re.sub(
    r": 'bg-slate-700 text-slate-400 hover:bg-slate-600'",
    r": isNHL ? 'bg-gray-200 text-black hover:bg-gray-300 font-bold' : 'bg-slate-700 text-slate-400 hover:bg-slate-600'",
    content
)

# 7. Fix standalone 'text-slate-300' in non-comparison contexts
content = re.sub(
    r": 'text-slate-300'",
    r': `${textSecondary}`',
    content
)

# 8. Fix 'text-slate-200' in comparisons
content = re.sub(
    r"'text-slate-200'",
    r'`${textValue}`',
    content
)

# 9. Fix latency disclaimer text (line 1611)
content = re.sub(
    r'<div className="text-\[10px\] text-slate-500 mt-0.5">',
    r'<div className={`text-[10px] ${textMuted} mt-0.5`}>',
    content
)

# 10. Fix "Live Game Stats" header for NFL (line 2259) - keep this for NFL only, don't change
# Skip this one as it's NFL-specific

# 11. Fix NFL live stats labels (lines 2328-2350) - keep these as is, they're NFL-only

with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed remaining NHL text colors:")
print("  - Team headers in momentum sections")
print("  - Stat comparison 'else' cases")
print("  - Possession indicator badges")
print("  - Team abbreviations")
print("  - Buttons and interactive elements")
print("  - Latency disclaimer text")
print("\nAll NHL cards should now have bold black text throughout!")
