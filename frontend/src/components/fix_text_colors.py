import re

with open('GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ALL remaining hardcoded text colors with conditional ones
# text-white -> textPrimary
content = re.sub(
    r'className="([^"]*?)text-white([^"]*?)"',
    r'className={`\1${textPrimary}\2`}',
    content
)

# text-slate-100 -> textPrimary
content = re.sub(
    r'className="([^"]*?)text-slate-100([^"]*?)"',
    r'className={`\1${textPrimary}\2`}',
    content
)

# text-slate-200 -> textPrimary
content = re.sub(
    r'className="([^"]*?)text-slate-200([^"]*?)"',
    r'className={`\1${textPrimary}\2`}',
    content
)

# text-slate-300 -> textSecondary
content = re.sub(
    r'className="([^"]*?)text-slate-300([^"]*?)"',
    r'className={`\1${textSecondary}\2`}',
    content
)

# text-slate-400 -> textTertiary
content = re.sub(
    r'className="([^"]*?)text-slate-400([^"]*?)"',
    r'className={`\1${textTertiary}\2`}',
    content
)

# text-slate-500 -> textTertiary
content = re.sub(
    r'className="([^"]*?)text-slate-500([^"]*?)"',
    r'className={`\1${textTertiary}\2`}',
    content
)

# Make all font-semibold into font-bold
content = re.sub(r'\bfont-semibold\b', 'font-bold', content)

with open('GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully replaced all hardcoded text colors with conditional colors')
print('Changed all font-semibold to font-bold')
