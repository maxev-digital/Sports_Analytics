import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Count before
before_count = len(re.findall(r'text-slate-[0-9]{3}', content))
print(f"Found {before_count} instances of hardcoded text-slate-* classes")

# Replace all standalone text-slate-400 with textLabel
content = re.sub(r'text-slate-400', r'textLabel', content)

# Replace all standalone text-slate-300 with textSecondary
content = re.sub(r'text-slate-300', r'textSecondary', content)

# Replace all standalone text-slate-200 with textValue
content = re.sub(r'text-slate-200', r'textValue', content)

# Replace all standalone text-slate-500 with textMuted
content = re.sub(r'text-slate-500', r'textMuted', content)

# Replace all standalone text-slate-100 with textHeader
content = re.sub(r'text-slate-100', r'textHeader', content)

# Now we need to wrap these in template literals where they're used in className strings
# Pattern: className="... textLabel ..." needs to become className={`... ${textLabel} ...`}

# Fix className="text-xs textLabel" -> className={`text-xs ${textLabel}`}
content = re.sub(
    r'className="([^"{}]*)(textLabel|textSecondary|textValue|textMuted|textHeader)([^"{}]*)"',
    lambda m: f'className={{`{m.group(1)}${{{m.group(2)}}}{m.group(3)}`}}',
    content
)

# Fix className='...' variant
content = re.sub(
    r"className='([^'{}]*)(textLabel|textSecondary|textValue|textMuted|textHeader)([^'{}]*)'",
    lambda m: f'className={{`{m.group(1)}${{{m.group(2)}}}{m.group(3)}`}}',
    content
)

# Count after
after_count = len(re.findall(r'text-slate-[0-9]{3}', content))
print(f"Remaining {after_count} instances (should be in variable definitions only)")

with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nReplaced all hardcoded text colors with conditional variables!")
print("All NHL cards should now have black text throughout.")
