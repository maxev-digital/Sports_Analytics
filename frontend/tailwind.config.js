/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CSS-variable theme tokens (set by the app's dark/light theme system)
        panel:      'var(--c-panel)',
        'ev-border': 'var(--c-border)',
        fg:         'var(--c-fg)',
        muted:      'var(--c-muted)',
        track:      'var(--c-track)',
        rowsel:     'var(--c-rowsel)',
        // Survivor OKLCH semantic palette (matches COLORS in survivorUtils.ts)
        'ev-emerald': 'oklch(69.6% .17 162.48)',
        'ev-red':     'oklch(63.2% .204 25.331)',
        'ev-yellow':  'oklch(79.5% .184 86.047)',
        'ev-blue':    'oklch(62.3% .214 259.815)',
        'ev-orange':  'oklch(72% .19 50)',
        'ev-purple':  'oklch(70% .18 290)',
      },
    },
  },
  plugins: [],
}
