/**
 * Sound Effects Preview Page
 * Test all available sound effects for Max EV Sports
 */

import { useState } from 'react';

const SOUND_CATEGORIES = {
  "Dashboard/Home": [
    { file: "cash-register.mp3", name: "Cash Register" },
    { file: "coins.mp3", name: "Coins" },
    { file: "whoosh.mp3", name: "Whoosh" },
    { file: "bull.mp3", name: "Bull" },
  ],
  "Alerts": [
    { file: "alert-bell.mp3", name: "Alert Bell" },
    { file: "notification.mp3", name: "Notification" },
    { file: "siren.mp3", name: "Siren" },
    { file: "whistle.mp3", name: "Whistle" },
  ],
  "Props": [
    { file: "swish.mp3", name: "Basketball Swish" },
    { file: "swoosh.mp3", name: "Swoosh" },
    { file: "success.mp3", name: "Success" },
  ],
  "Analytics": [
    { file: "data-ping.mp3", name: "Data Ping" },
    { file: "calculate.mp3", name: "Calculate" },
    { file: "scan.mp3", name: "Scan" },
  ],
  "Odds": [
    { file: "tick.mp3", name: "Tick" },
    { file: "click.mp3", name: "Click" },
    { file: "line-move.mp3", name: "Line Move" },
    { file: "lock.mp3", name: "Lock" },
  ],
  "Tools": [
    { file: "power-up.mp3", name: "Power Up" },
    { file: "success-chime.mp3", name: "Success Chime" },
    { file: "tool-select.mp3", name: "Tool Select" },
  ],
  "Pricing": [
    { file: "upgrade.mp3", name: "Upgrade" },
    { file: "level-up.mp3", name: "Level Up" },
    { file: "checkout.mp3", name: "Checkout" },
    { file: "unlock.mp3", name: "Unlock" },
  ],
  "Strategy Settings": [
    { file: "toggle-on.mp3", name: "Toggle On" },
    { file: "toggle-off.mp3", name: "Toggle Off" },
    { file: "save.mp3", name: "Save" },
  ],
  "Multi-Sport": [
    { file: "sport-switch.mp3", name: "Sport Switch" },
    { file: "buzzer.mp3", name: "Basketball Buzzer" },
    { file: "horn.mp3", name: "Hockey Horn" },
    { file: "whistle-nfl.mp3", name: "Football Whistle" },
  ],
  "Navigation": [
    { file: "tab-switch.mp3", name: "Tab Switch" },
    { file: "dropdown.mp3", name: "Dropdown" },
    { file: "logout.mp3", name: "Logout" },
  ],
  "Bet Tracking": [
    { file: "bet-placed.mp3", name: "Bet Placed" },
    { file: "win.mp3", name: "Win" },
    { file: "victory.mp3", name: "Victory" },
    { file: "loss.mp3", name: "Loss" },
    { file: "push.mp3", name: "Push" },
  ],
  "Live Games": [
    { file: "game-start.mp3", name: "Game Start" },
    { file: "buzzer-quarter.mp3", name: "Quarter Buzzer" },
    { file: "goal.mp3", name: "Goal" },
    { file: "final-whistle.mp3", name: "Final Whistle" },
  ],
  "Learn/Education": [
    { file: "page-turn.mp3", name: "Page Turn" },
    { file: "lightbulb.mp3", name: "Lightbulb" },
    { file: "graduate.mp3", name: "Graduate" },
  ],
  "Login/Signup": [
    { file: "flame.mp3", name: "Flame" },
  ],
};

export default function SoundPreview() {
  const [volume, setVolume] = useState(0.3);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);

  const playSound = (filename: string) => {
    const audio = new Audio(`/${filename}`);
    audio.volume = volume;
    setCurrentlyPlaying(filename);

    audio.play().catch(err => console.log('Sound play failed:', err));

    audio.onended = () => {
      setCurrentlyPlaying(null);
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Sound Effects Preview</h1>
          <p className="text-slate-400">Test all available sound effects for Max EV Sports</p>
        </div>

        {/* Volume Control */}
        <div className="mb-8 bg-slate-800 rounded-lg p-6 border-4 border-slate-700">
          <label className="block text-lg font-semibold mb-3">
            Volume: {Math.round(volume * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
          />
        </div>

        {/* Sound Categories */}
        <div className="space-y-6">
          {Object.entries(SOUND_CATEGORIES).map(([category, sounds]) => (
            <div
              key={category}
              className="bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 rounded-lg p-6 border-4 border-slate-700"
            >
              <h2 className="text-2xl font-bold mb-4 text-blue-400">{category}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {sounds.map((sound) => (
                  <button
                    key={sound.file}
                    onClick={() => playSound(sound.file)}
                    className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                      currentlyPlaying === sound.file
                        ? 'bg-green-600 text-white shadow-lg shadow-green-600/50'
                        : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                    }`}
                  >
                    {currentlyPlaying === sound.file ? '▶️ Playing...' : sound.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-8 bg-slate-800 rounded-lg p-6 border-4 border-blue-700">
          <h3 className="text-xl font-bold mb-2">Summary</h3>
          <p className="text-slate-300">
            Total Sound Effects: <span className="text-blue-400 font-bold">48</span>
          </p>
          <p className="text-slate-300 mt-2">
            All sounds are stored in <code className="bg-slate-900 px-2 py-1 rounded">frontend/public/</code>
          </p>
          <p className="text-slate-400 text-sm mt-4">
            Tip: Adjust the volume slider above to test at different sound levels. Recommended: 20-40%
          </p>
        </div>
      </div>
    </div>
  );
}
