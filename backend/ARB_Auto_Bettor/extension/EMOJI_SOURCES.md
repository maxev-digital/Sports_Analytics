# Emoji Sources for Extension

## Current: Microsoft Teams (Fluent Emoji)
**URL Pattern:** `https://em-content.zobj.net/source/microsoft-teams/363/[emoji-name]_[unicode].png`

**Pros:**
- ✅ 3D rendered style - very sharp and modern
- ✅ Free to use via CDN
- ✅ Consistent sizing (all same resolution)
- ✅ Great for professional apps

**Examples:**
- Basketball: `https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png`
- Fire: `https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png`
- Lightning: `https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png`

---

## Alternative Emoji Sources

### 1. Twitter Emoji (Twemoji)
**URL Pattern:** `https://em-content.zobj.net/source/twitter/348/[emoji-name]_[unicode].png`

**Pros:**
- Flat design, colorful
- Very recognizable
- Well-maintained

**Cons:**
- Less 3D/sharp than Fluent
- Slightly cartoonish

### 2. Apple Emoji
**URL Pattern:** `https://em-content.zobj.net/source/apple/354/[emoji-name]_[unicode].png`

**Pros:**
- Glossy 3D style
- High quality
- iOS-like appearance

**Cons:**
- May look out of place on Windows

### 3. Google Noto Emoji
**URL Pattern:** `https://em-content.zobj.net/source/google/350/[emoji-name]_[unicode].png`

**Pros:**
- Clean, modern
- Open source
- Works well on all platforms

**Cons:**
- Less "sharp" than Fluent
- Somewhat generic

### 4. Samsung Emoji
**URL Pattern:** `https://em-content.zobj.net/source/samsung/349/[emoji-name]_[unicode].png`

**Pros:**
- Unique bubbly style
- Colorful and fun

**Cons:**
- Very stylized (may not fit professional app)
- Inconsistent across versions

### 5. Facebook Emoji
**URL Pattern:** `https://em-content.zobj.net/source/facebook/355/[emoji-name]_[unicode].png`

**Pros:**
- Rounded, friendly style
- Widely recognized

**Cons:**
- Less sharp/3D

---

## How to Find Emoji Unicode

1. Go to https://emojipedia.org/
2. Search for your emoji (e.g., "basketball")
3. Look at the URL or page to find the Unicode (e.g., `1f3c0`)
4. Replace `[unicode]` in the pattern above

---

## Sports Emoji Used in Extension

| Sport | Emoji | Unicode | Microsoft Teams URL |
|-------|-------|---------|---------------------|
| NBA | 🏀 Basketball | 1f3c0 | https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png |
| NFL | 🏈 Football | 1f3c8 | https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png |
| NHL | 🏒 Hockey | 1f3d2 | https://em-content.zobj.net/source/microsoft-teams/363/ice-hockey_1f3d2.png |
| MLB | ⚾ Baseball | 26be-fe0f | https://em-content.zobj.net/source/microsoft-teams/363/baseball_26be-fe0f.png |
| NCAAF | 🏈 Football | 1f3c8 | (same as NFL) |
| Soccer | ⚽ Soccer | 26bd | https://em-content.zobj.net/source/microsoft-teams/363/soccer-ball_26bd.png |

---

## UI Emoji Used

| Purpose | Emoji | Unicode | URL |
|---------|-------|---------|-----|
| Search/Empty | 🔍 | 1f50d | https://em-content.zobj.net/source/microsoft-teams/363/magnifying-glass-tilted-left_1f50d.png |
| Fire/Steam | 🔥 | 1f525 | https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png |
| Chart/Lines | 📈 | 1f4c8 | https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png |
| Lightning/Fast | ⚡ | 26a1 | https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png |
| Target/Aim | 🎯 | 1f3af | https://em-content.zobj.net/source/microsoft-teams/363/direct-hit_1f3af.png |

---

## Switching Emoji Sets

To switch from Microsoft Teams to another set (e.g., Apple), find-and-replace in the code:

**From:**
```
https://em-content.zobj.net/source/microsoft-teams/363/
```

**To:**
```
https://em-content.zobj.net/source/apple/354/
```

All emoji will automatically update to the new style!
