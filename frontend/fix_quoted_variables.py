import re

with open('src/components/GameCard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix quoted template literal variables: '${textValue}' -> ${textValue}
# This happens in ternary expressions where the replacement was too literal

# Pattern: : '${textVariable}' or ? '${textVariable}'
content = re.sub(r":\s*'\$\{(text\w+)\}'", r': `${\1}`', content)
content = re.sub(r"\?\s*'\$\{(text\w+)\}'", r'? `${\1}`', content)

with open('src/components/GameCard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed quoted template literal variables!")
print("Changed '${textValue}' -> `${textValue}` etc.")
