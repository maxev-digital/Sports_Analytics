# ARB Auto Bettor Design System
## Visual Improvements from Chrome Extension → Main Website

---

## 🎨 Color Palette

### Background Gradients
```css
/* Main background */
background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);

/* Card backgrounds - base */
background: linear-gradient(135deg, #1e293b 0%, #2d3748 100%);
```

### Sport-Specific Gradients

**NBA (Blue)**
```css
background: linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%);
border-color: #3b82f6;
```

**NFL (Green)**
```css
background: linear-gradient(135deg, #166534 0%, #1e293b 100%);
border-color: #22c55e;
```

**NHL (Orange)**
```css
background: linear-gradient(135deg, #7c2d12 0%, #1e293b 100%);
border-color: #f97316;
```

**MLB (Purple)**
```css
background: linear-gradient(135deg, #7e22ce 0%, #1e293b 100%);
border-color: #a855f7;
```

**NCAAF (Red)**
```css
background: linear-gradient(135deg, #b91c1c 0%, #1e293b 100%);
border-color: #ef4444;
```

**SOCCER (Cyan)**
```css
background: linear-gradient(135deg, #155e75 0%, #1e293b 100%);
border-color: #06b6d4;
```

### Stat Cards
```css
background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
border: 2px solid #475569;
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
```

### Steam Move Cards (Hot Alert)
```css
background: linear-gradient(135deg, #7f1d1d 0%, #1e293b 100%);
border: 2px solid #ef4444;
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), 0 0 12px rgba(239, 68, 68, 0.2);
```

---

## 🏀 Sport Icons (Microsoft Fluent Emoji)

### CDN URLs
```javascript
const sportEmojis = {
  'NBA': 'https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png',
  'NFL': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
  'NHL': 'https://em-content.zobj.net/source/microsoft-teams/363/ice-hockey_1f3d2.png',
  'MLB': 'https://em-content.zobj.net/source/microsoft-teams/363/baseball_26be-fe0f.png',
  'NCAAF': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
  'SOCCER': 'https://em-content.zobj.net/source/microsoft-teams/363/soccer-ball_26bd.png'
};
```

### Detection Function
```javascript
function detectSport(game) {
  const sport_key = game.sport_key || game.sport || '';
  if (sport_key.includes('basketball_nba')) return 'NBA';
  if (sport_key.includes('americanfootball_nfl')) return 'NFL';
  if (sport_key.includes('americanfootball_ncaaf')) return 'NCAAF';
  if (sport_key.includes('icehockey_nhl')) return 'NHL';
  if (sport_key.includes('baseball_mlb')) return 'MLB';
  if (sport_key.includes('soccer')) return 'SOCCER';
  return 'NBA'; // default
}

function getSportEmoji(sport) {
  const sportEmojis = { /* ... see above ... */ };
  return sportEmojis[sport] || sportEmojis['NBA'];
}
```

---

## 📐 Card Styling

### Base Game Card
```css
.game-card {
  background: linear-gradient(135deg, #1e293b 0%, #2d3748 100%);
  border: 2px solid #475569;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.game-card:hover {
  border-color: #60a5fa;
  box-shadow: 0 0 8px rgba(96, 165, 250, 0.3);
  transform: translateY(-2px);
}
```

### Sport-Specific Cards (React/Tailwind Example)
```jsx
// Get sport from game data
const sport = detectSport(game);
const sportEmoji = getSportEmoji(sport);

// Determine gradient colors
const sportStyles = {
  'NBA': { gradient: 'from-blue-900 to-slate-800', border: 'border-blue-500' },
  'NFL': { gradient: 'from-green-900 to-slate-800', border: 'border-green-500' },
  'NHL': { gradient: 'from-orange-900 to-slate-800', border: 'border-orange-500' },
  'MLB': { gradient: 'from-purple-900 to-slate-800', border: 'border-purple-500' },
  'NCAAF': { gradient: 'from-red-900 to-slate-800', border: 'border-red-500' },
  'SOCCER': { gradient: 'from-cyan-900 to-slate-800', border: 'border-cyan-500' }
};

const style = sportStyles[sport] || sportStyles['NBA'];

return (
  <div
    className={`bg-gradient-to-br ${style.gradient} border-2 ${style.border} rounded-lg p-4`}
    data-sport={sport}
  >
    <div className="flex items-center gap-2">
      <img src={sportEmoji} alt={sport} className="w-6 h-6" />
      <h3>{game.home_team.name} vs {game.away_team.name}</h3>
    </div>
    {/* ... rest of card ... */}
  </div>
);
```

### Pure CSS Version (Non-Tailwind)
```css
/* Add data-sport attribute to cards */
.game-card[data-sport="NBA"] {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%);
  border-color: #3b82f6;
}

.game-card[data-sport="NFL"] {
  background: linear-gradient(135deg, #166534 0%, #1e293b 100%);
  border-color: #22c55e;
}

.game-card[data-sport="NHL"] {
  background: linear-gradient(135deg, #7c2d12 0%, #1e293b 100%);
  border-color: #f97316;
}

.game-card[data-sport="MLB"] {
  background: linear-gradient(135deg, #7e22ce 0%, #1e293b 100%);
  border-color: #a855f7;
}

.game-card[data-sport="NCAAF"] {
  background: linear-gradient(135deg, #b91c1c 0%, #1e293b 100%);
  border-color: #ef4444;
}

.game-card[data-sport="SOCCER"] {
  background: linear-gradient(135deg, #155e75 0%, #1e293b 100%);
  border-color: #06b6d4;
}
```

---

## 🖼️ Emoji Integration

### HTML Usage
```html
<!-- In title -->
<div class="game-title">
  <img src="https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png"
       alt="NBA"
       style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">
  Lakers vs Warriors
</div>

<!-- In tab buttons -->
<button class="tab-btn">
  <img src="https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png"
       alt="Fire"
       style="width: 16px; height: 16px; vertical-align: middle; margin-right: 4px;">
  Steam Moves
</button>
```

### React/JSX Usage
```jsx
<div className="flex items-center gap-2">
  <img
    src={getSportEmoji(sport)}
    alt={sport}
    className="w-5 h-5"
  />
  <span>{game.home_team.name} vs {game.away_team.name}</span>
</div>
```

### Better Rendering CSS
```css
/* Crisp emoji rendering */
img[src*="em-content"] {
  display: inline-block;
  image-rendering: crisp-edges;
  image-rendering: -webkit-optimize-contrast;
}
```

---

## 📊 UI Icons

```javascript
const uiEmojis = {
  target: 'https://em-content.zobj.net/source/microsoft-teams/363/direct-hit_1f3af.png',
  fire: 'https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png',
  chart: 'https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png',
  lightning: 'https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png',
  search: 'https://em-content.zobj.net/source/microsoft-teams/363/magnifying-glass-tilted-left_1f50d.png'
};
```

---

## 🎯 Implementation Checklist

### For Main Website (React + Tailwind)

**Step 1: Add Sport Detection**
- [ ] Add `detectSport()` function to utils
- [ ] Add `getSportEmoji()` function to utils
- [ ] Update GameCard component to detect sport

**Step 2: Apply Gradients**
- [ ] Convert current `bg-slate-800` to gradient classes
- [ ] Add sport-specific gradient variants
- [ ] Update card borders with sport colors

**Step 3: Add Sport Icons**
- [ ] Add emoji images to game titles
- [ ] Add emoji to tab navigation
- [ ] Update empty states with emoji

**Step 4: Add Shadows/Depth**
- [ ] Add `box-shadow` to cards
- [ ] Add hover effects with glow
- [ ] Add subtle transform on hover

**Step 5: Test Across Sports**
- [ ] NBA games show blue gradient + basketball emoji
- [ ] NFL games show green gradient + football emoji
- [ ] NHL games show orange gradient + hockey emoji
- [ ] MLB games show purple gradient + baseball emoji

---

## 📂 Files to Update

### Main Website Files
```
C:\Users\nashr\backend\scrapers\nba\frontend\src\
├── components\
│   ├── GameCard.tsx           ← Apply sport-specific gradients
│   ├── Dashboard.tsx          ← Update background gradient
│   └── Navigation.tsx         ← Add emoji to tabs
├── utils\
│   └── sportDetection.ts      ← NEW: Add detection functions
└── index.css                  ← Add gradient utilities
```

---

## 💬 What to Tell Claude in Another Terminal

**Copy and paste this:**

```
I want to update my sports betting dashboard to match the visual design from my Chrome extension.

Key changes needed:
1. Add sport-specific gradient backgrounds to game cards (NBA=blue, NFL=green, NHL=orange, MLB=purple, NCAAF=red)
2. Add Microsoft Fluent Emoji icons for each sport (basketball, football, hockey, baseball)
3. Apply gradient backgrounds to all cards instead of solid colors
4. Add box shadows for depth
5. Update empty states with emoji icons

Reference file with full design system:
C:\Users\nashr\backend\ARB_Auto_Bettor\DESIGN_SYSTEM.md

Main files to update:
- C:\Users\nashr\backend\scrapers\nba\frontend\src\components\GameCard.tsx
- C:\Users\nashr\backend\scrapers\nba\frontend\src\components\Dashboard.tsx
- C:\Users\nashr\backend\scrapers\nba\frontend\src\index.css

Please read the DESIGN_SYSTEM.md file and apply these visual improvements to the main website, maintaining the existing Tailwind CSS approach.
```

---

## 🔄 Quick Color Reference

| Sport | Primary Color | Gradient Start | Border Color |
|-------|---------------|----------------|--------------|
| NBA | Blue | #1e3a8a | #3b82f6 |
| NFL | Green | #166534 | #22c55e |
| NHL | Orange | #7c2d12 | #f97316 |
| MLB | Purple | #7e22ce | #a855f7 |
| NCAAF | Red | #b91c1c | #ef4444 |
| SOCCER | Cyan | #155e75 | #06b6d4 |

---

## ✨ Before & After Example

**Before (Current):**
```jsx
<div className="bg-slate-800 border-2 border-slate-700 rounded-lg p-4">
  <h3>Lakers vs Warriors</h3>
</div>
```

**After (New):**
```jsx
const sport = detectSport(game); // 'NBA'
const emoji = getSportEmoji(sport); // basketball emoji URL

<div className="bg-gradient-to-br from-blue-900 to-slate-800 border-2 border-blue-500 rounded-lg p-4 shadow-lg">
  <div className="flex items-center gap-2">
    <img src={emoji} alt={sport} className="w-5 h-5" />
    <h3>Lakers vs Warriors</h3>
  </div>
</div>
```
