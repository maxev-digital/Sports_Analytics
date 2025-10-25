# Max EV Sports - Sound Effects Guide

This document lists all available sound effects and their recommended usage throughout the website.

## 📁 Location
All sound files are located in: `frontend/public/`

## 🔊 Available Sound Effects (48 Total)

### Dashboard/Home Page (`/`)
| File | Description | When to Use |
|------|-------------|-------------|
| `cash-register.mp3` | Cash register cha-ching | When showing HIGH confidence plays or positive EV |
| `coins.mp3` | Coins clinking | Alternative to cash register for wins |
| `whoosh.mp3` | Quick air swoosh | When live games refresh/update |
| `bull.mp3` | Bull market sound | Page load (already implemented) |

### Alerts Page (`/alerts`)
| File | Description | When to Use |
|------|-------------|-------------|
| `alert-bell.mp3` | Notification bell | When new betting alert appears |
| `notification.mp3` | Modern app alert | Alternative notification sound |
| `siren.mp3` | Brief alert siren | For URGENT/HIGH value alerts only |
| `whistle.mp3` | Referee whistle | When alert criteria is met |

### Props Page (`/props`)
| File | Description | When to Use |
|------|-------------|-------------|
| `swish.mp3` | Basketball net swish | Loading NBA/basketball props |
| `swoosh.mp3` | Quick air swoosh | Toggling between prop types |
| `success.mp3` | Success chime | Marking or tracking a prop bet |

### Analytics Page (`/analytics`)
| File | Description | When to Use |
|------|-------------|-------------|
| `data-ping.mp3` | Digital ping | When graphs/charts load |
| `calculate.mp3` | Calculation sound | Running calculations or filters |
| `scan.mp3` | Electronic sweep | Analyzing historical data |

### Odds Page (`/odds`)
| File | Description | When to Use |
|------|-------------|-------------|
| `tick.mp3` | Clock tick | When odds update/refresh |
| `click.mp3` | Mouse click | Button press feedback |
| `line-move.mp3` | Rising pitch tone | Sharp money or reverse line movement |
| `lock.mp3` | Mechanical lock | When odds lock before game |

### Tools Page (`/tools`)
| File | Description | When to Use |
|------|-------------|-------------|
| `power-up.mp3` | Power up sound | Activating a tool |
| `success-chime.mp3` | Success chime | Tool calculation completes |
| `tool-select.mp3` | Interface click | Switching between tools |

### Pricing Page (`/pricing`)
| File | Description | When to Use |
|------|-------------|-------------|
| `upgrade.mp3` | Achievement unlock | User selects premium tier |
| `level-up.mp3` | Video game level up | Alternative to upgrade |
| `checkout.mp3` | Purchase complete | "Subscribe" button click |
| `unlock.mp3` | Achievement unlocked | Showing premium features |

### Strategy Settings (`/strategy-settings`)
| File | Description | When to Use |
|------|-------------|-------------|
| `toggle-on.mp3` | Toggle switch on | Enabling a strategy |
| `toggle-off.mp3` | Toggle switch off | Disabling a strategy |
| `save.mp3` | Save confirmation | Saving settings |

### Multi-Sport Page (`/multi-sport`)
| File | Description | When to Use |
|------|-------------|-------------|
| `sport-switch.mp3` | Interface transition | Switching between sports |
| `buzzer.mp3` | Basketball buzzer | Basketball game events |
| `horn.mp3` | Hockey horn | Hockey game events |
| `whistle-nfl.mp3` | Football whistle | Football game events |

### Navigation (All Pages)
| File | Description | When to Use |
|------|-------------|-------------|
| `tab-switch.mp3` | Subtle soft click | Changing tabs/pages (very subtle) |
| `dropdown.mp3` | Swoosh down | Opening Settings or Learn dropdowns |
| `logout.mp3` | Closing sound | Logging out |

### Bet Tracking System
| File | Description | When to Use |
|------|-------------|-------------|
| `bet-placed.mp3` | Positive beep | User logs a bet |
| `win.mp3` | Celebration sound | Bet wins (confetti sound) |
| `victory.mp3` | Triumphant fanfare | Big wins or streaks |
| `loss.mp3` | Gentle descending tone | Bet loses (sympathetic) |
| `push.mp3` | Neutral beep | Bet pushes |

### Live Games (`/live-games`)
| File | Description | When to Use |
|------|-------------|-------------|
| `game-start.mp3` | Game start horn | Live game begins |
| `buzzer-quarter.mp3` | Quarter end buzzer | Quarter/period transitions |
| `goal.mp3` | Goal celebration | When score updates |
| `final-whistle.mp3` | Final whistle | Game ends |

### Learn/Education (`/learn`, `/getting-started`)
| File | Description | When to Use |
|------|-------------|-------------|
| `page-turn.mp3` | Paper flip | Navigating between articles |
| `lightbulb.mp3` | Bright ding | Revealing strategy tips |
| `graduate.mp3` | Ascending scale | Completing a learning module |

### Login/Signup
| File | Description | When to Use |
|------|-------------|-------------|
| `bull.mp3` | Bull market sound | Login page (already implemented) |
| `flame.mp3` | Fire/hot sound | SignUp page (already implemented) |

---

## 🎯 Implementation Priority

### Phase 1 (Essential)
1. `alert-bell.mp3` - Alerts page
2. `cash-register.mp3` - Dashboard/winning plays
3. `toggle-on.mp3` / `toggle-off.mp3` - Strategy Settings

### Phase 2 (Enhanced UX)
4. `win.mp3` - Bet wins
5. `line-move.mp3` - Odds page
6. `sport-switch.mp3` - Multi-Sport page

### Phase 3 (Polish)
7. `tab-switch.mp3` - General navigation
8. `calculate.mp3` - Analytics
9. `upgrade.mp3` - Pricing page

---

## 💡 Usage Tips

### Volume Settings
- Keep all sounds at **20-40% volume** (subtle, not intrusive)
- Let users control master volume in Settings

### Best Practices
1. **Don't overuse** - Sound for important actions only
2. **Respect user preference** - Add mute toggle in Settings
3. **Context matters** - Match sound to action (celebrate wins, gentle on losses)
4. **Loading states** - Use subtle sounds for async operations
5. **Mobile friendly** - Test on mobile devices (some sounds may not play on autoplay)

### React Implementation Example

```typescript
import { useRef } from 'react';

function AlertsPage() {
  const alertSound = useRef<HTMLAudioElement>(null);

  const playAlertSound = () => {
    if (alertSound.current) {
      alertSound.current.volume = 0.3; // 30% volume
      alertSound.current.play().catch(err => console.log('Sound play failed:', err));
    }
  };

  return (
    <>
      <audio ref={alertSound} src="/alert-bell.mp3" preload="auto" />
      <button onClick={playAlertSound}>Test Alert Sound</button>
    </>
  );
}
```

### Global Sound Manager (Recommended)

Create a `useSoundEffect` hook to manage all sounds from one place:

```typescript
// hooks/useSoundEffect.ts
import { useRef, useCallback } from 'react';

export function useSoundEffect(soundFile: string, volume: number = 0.3) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const play = useCallback(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio(`/${soundFile}`);
      audioRef.current.volume = volume;
    }
    audioRef.current.currentTime = 0;
    audioRef.current.play().catch(err => console.log('Sound play failed:', err));
  }, [soundFile, volume]);

  return play;
}

// Usage:
const playWin = useSoundEffect('win.mp3', 0.4);
playWin(); // Play the sound
```

---

## 🛠️ Regenerating Sounds

To regenerate all sound effects or add new ones:

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows

# Run the generator
python backend/utils/generate_sound_effects.py
```

Edit `backend/utils/generate_sound_effects.py` to add new sounds to the `SOUND_EFFECTS` dictionary.

---

## 📦 Files Generated

**Total**: 48 sound files (2 original + 46 generated)

Generated using **Eleven Labs API** for consistent, high-quality sound effects.

All files are in **MP3 format** and ready to use in your React application!
