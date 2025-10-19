import re

with open('GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Don't replace these patterns (they're for bookmaker badges, status badges, colored data)
skip_patterns = [
    r"'text-slate-[0-9]+'"  # Skip quoted strings (bookmaker config)
]

def should_skip(line):
    # Skip lines with bookmaker config
    if "short:" in line or "bg:" in line or "text:" in line:
        return True
    # Skip getRankColor function
    if "getRankColor" in line or "rank <= 10" in line or "rank <= 20" in line:
        return True
    # Skip variable definitions
    if "const textPrimary" in line or "const textSecondary" in line or "const textTertiary" in line:
        return True
    # Skip colored values (green, blue, red, yellow for stats)
    if "text-green-" in line or "text-blue-" in line or "text-red-" in line or "text-yellow-" in line:
        return True
    # Skip status badge colors
    if "bg-red-600 text-white" in line or "bg-slate-700 text-slate-300" in line:
        return True
    return False

lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    if should_skip(line):
        fixed_lines.append(line)
        continue

    # Replace text-white with textPrimary (except in specific contexts)
    if 'text-white' in line and 'className=' in line:
        line = re.sub(r'className="([^"]*?)text-white([^"]*?)"', r'className={`\1${textPrimary}\2`}', line)

    # Replace text-slate-100, text-slate-200 with textPrimary
    if ('text-slate-100' in line or 'text-slate-200' in line) and 'className=' in line:
        line = re.sub(r'className="([^"]*?)text-slate-(?:100|200)([^"]*?)"', r'className={`\1${textPrimary}\2`}', line)

    # Replace text-slate-300 with textSecondary
    if 'text-slate-300' in line and 'className=' in line:
        line = re.sub(r'className="([^"]*?)text-slate-300([^"]*?)"', r'className={`\1${textSecondary}\2`}', line)

    # Replace text-slate-400, text-slate-500 with textTertiary
    if ('text-slate-400' in line or 'text-slate-500' in line) and 'className=' in line:
        line = re.sub(r'className="([^"]*?)text-slate-(?:400|500)([^"]*?)"', r'className={`\1${textTertiary}\2`}', line)

    # Replace font-semibold with font-bold
    line = line.replace('font-semibold', 'font-bold')

    fixed_lines.append(line)

with open('GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print('Successfully replaced all text colors with conditional variables')
print('Changed all font-semibold to font-bold')
