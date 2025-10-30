import { useState, useEffect } from 'react';

// Type definitions for Electron API
declare global {
  interface Window {
    electron?: {
      openWindow: (route: string) => Promise<void>;
      getOpenWindows: () => Promise<string[]>;
      platform: string;
      isElectron: boolean;
      version: string;
    };
  }
}

export function ElectronWindowControls() {
  const [isElectron, setIsElectron] = useState(false);
  const [openWindows, setOpenWindows] = useState<string[]>([]);

  useEffect(() => {
    setIsElectron(!!window.electron?.isElectron);

    if (window.electron) {
      // Load open windows list
      window.electron.getOpenWindows().then(setOpenWindows);
    }
  }, []);

  if (!isElectron) {
    return null; // Don't show controls in web version
  }

  const windows = [
    { route: 'live-games', label: '🔥 Live Games', emoji: '🔥' },
    { route: 'alerts', label: '🚨 Alerts', emoji: '🚨' },
    { route: 'analytics', label: '📊 Analytics', emoji: '📊' },
    { route: 'props', label: '🎯 Props', emoji: '🎯' },
    { route: 'tools', label: '🔧 Tools', emoji: '🔧' },
    { route: 'odds', label: '📈 Odds', emoji: '📈' },
  ];

  const handleOpenWindow = async (route: string) => {
    if (window.electron) {
      await window.electron.openWindow(route);
      const updated = await window.electron.getOpenWindows();
      setOpenWindows(updated);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 border-2 border-slate-700 rounded-lg shadow-2xl p-3">
        <div className="text-xs text-slate-400 font-semibold mb-2 flex items-center gap-2">
          <span className="text-blue-400">⚡</span>
          DESKTOP MODE
        </div>
        <div className="text-xs text-slate-500 mb-3">Open in new window:</div>
        <div className="grid grid-cols-2 gap-2">
          {windows.map((win) => (
            <button
              key={win.route}
              onClick={() => handleOpenWindow(win.route)}
              disabled={openWindows.includes(win.route)}
              className={`
                px-3 py-2 rounded-md text-xs font-medium transition-all
                ${openWindows.includes(win.route)
                  ? 'bg-green-900/30 border border-green-700 text-green-400 cursor-not-allowed'
                  : 'bg-slate-700 hover:bg-slate-600 text-white border border-slate-600'
                }
              `}
              title={openWindows.includes(win.route) ? 'Already open' : `Open ${win.label}`}
            >
              <span className="mr-1">{win.emoji}</span>
              {win.label.split(' ').slice(1).join(' ')}
              {openWindows.includes(win.route) && (
                <span className="ml-1 text-green-400">✓</span>
              )}
            </button>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-slate-700 text-center">
          <div className="text-[10px] text-slate-600">
            Right-click system tray for more options
          </div>
        </div>
      </div>
    </div>
  );
}
