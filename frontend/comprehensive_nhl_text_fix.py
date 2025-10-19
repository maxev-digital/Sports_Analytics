import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track which lines have the variable definitions (skip those)
skip_lines = set()
for i, line in enumerate(lines):
    if 'const text' in line and '= isNHL ?' in line:
        skip_lines.add(i)

# Process each line
for i in range(len(lines)):
    if i in skip_lines:
        continue

    line = lines[i]

    # Replace text-slate-400 (labels) -> ${textLabel}
    if 'text-slate-400' in line:
        # If it's in a regular className="...", convert to template literal
        if 'className="' in line and '${' not in line:
            line = re.sub(r'className="([^"]*?)text-slate-400([^"]*?)"', r'className={`\1${textLabel}\2`}', line)
        else:
            line = line.replace('text-slate-400', '${textLabel}')

    # Replace text-slate-300 (secondary text) -> ${textSecondary}
    if 'text-slate-300' in line:
        if 'className="' in line and '${' not in line:
            line = re.sub(r'className="([^"]*?)text-slate-300([^"]*?)"', r'className={`\1${textSecondary}\2`}', line)
        else:
            line = line.replace('text-slate-300', '${textSecondary}')

    # Replace text-slate-200 (values) -> ${textValue}
    if 'text-slate-200' in line:
        if 'className="' in line and '${' not in line:
            line = re.sub(r'className="([^"]*?)text-slate-200([^"]*?)"', r'className={`\1${textValue}\2`}', line)
        else:
            line = line.replace('text-slate-200', '${textValue}')

    # Replace text-slate-100 (headers) -> ${textHeader}
    if 'text-slate-100' in line:
        if 'className="' in line and '${' not in line:
            line = re.sub(r'className="([^"]*?)text-slate-100([^"]*?)"', r'className={`\1${textHeader}\2`}', line)
        else:
            line = line.replace('text-slate-100', '${textHeader}')

    # Replace text-slate-500 (muted) -> ${textMuted}
    if 'text-slate-500' in line:
        if 'className="' in line and '${' not in line:
            line = re.sub(r'className="([^"]*?)text-slate-500([^"]*?)"', r'className={`\1${textMuted}\2`}', line)
        else:
            line = line.replace('text-slate-500', '${textMuted}')

    lines[i] = line

# Write back
with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Comprehensive NHL text color fix applied!")
print("All text should now be conditional (black for NHL, original colors for other sports)")
