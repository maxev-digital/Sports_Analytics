import re

# Read the file
with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# First, let's add more NHL text color variables after the existing ones (around line 324)
old_vars = r'''  const textPrimary = isNHL \? 'text-black' : 'text-white';
  const textSecondary = isNHL \? 'text-black font-bold' : 'text-slate-300';
  const textTertiary = isNHL \? 'text-black font-bold' : 'text-slate-400';'''

new_vars = '''  const textPrimary = isNHL ? 'text-black' : 'text-white';
  const textSecondary = isNHL ? 'text-black font-bold' : 'text-slate-300';
  const textTertiary = isNHL ? 'text-black font-bold' : 'text-slate-400';
  const textLabel = isNHL ? 'text-black font-semibold' : 'text-slate-400';
  const textValue = isNHL ? 'text-black font-bold' : 'text-slate-200';
  const textHeader = isNHL ? 'text-black font-bold' : 'text-slate-100';
  const textMuted = isNHL ? 'text-gray-600' : 'text-slate-500';'''

content = re.sub(old_vars, new_vars, content)

# Now replace common hardcoded patterns
# Replace text-slate-400 with ${textLabel} in contexts where it's a label
replacements = [
    # Headers and section titles
    (r'className="text-xs text-slate-400"', r'className={`text-xs ${textLabel}`}'),
    (r'className="text-xs text-slate-400 mb-1"', r'className={`text-xs ${textLabel} mb-1`}'),
    (r'className="text-xs text-slate-400 mb-2"', r'className={`text-xs ${textLabel} mb-2`}'),
    (r'className="text-xs text-slate-400 mb-3"', r'className={`text-xs ${textLabel} mb-3`}'),
    (r'className="text-xs text-slate-400 font-semibold mb-1"', r'className={`text-xs ${textLabel} mb-1`}'),

    # Labels in stats
    (r'<span className="text-slate-400">', r'<span className={textLabel}>'),

    # Values in stats
    (r"className='text-slate-200'", r"className={textValue}"),
    (r'className="text-slate-200"', r'className={textValue}'),

    # Headers
    (r'className="text-slate-100 font-bold', r'className={`${textHeader}'),

    # Regular text
    (r'className="text-slate-300"', r'className={textSecondary}'),
    (r"className='text-slate-300'", r'className={textSecondary}'),
    (r'<span className="text-slate-300', r'<span className={`${textSecondary}'),

    # Muted text
    (r'className="text-slate-500', r'className={`${textMuted}'),
    (r'text-[10px] text-slate-500', r'text-[10px] ${textMuted}'),
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back
with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("NHL text colors fixed!")
print("Added new color variables:")
print("  - textLabel: Labels like 'Record:', 'PPG:', etc.")
print("  - textValue: Stat values like record, points, etc.")
print("  - textHeader: Section headers like team names")
print("  - textMuted: Subtle text like timestamps")
print("\nReplaced all hardcoded text-slate-* classes with conditional NHL styling")
