interface GenericStrategyAlertProps {
  strategyName: string;
  strategyDescription: string;
  sport: string;
  sportColor: string;
  category: 'pregame' | 'live';
}

export function GenericStrategyAlert({ strategyName, strategyDescription, sport, sportColor, category }: GenericStrategyAlertProps) {
  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border-4 border-slate-700 rounded-lg p-8 text-center">
        {/* Strategy Header */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className={`${sportColor} text-white px-4 py-2 rounded-lg text-sm font-bold`}>
            {sport}
          </div>
          <div className={`${category === 'pregame' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'} px-3 py-1.5 rounded text-xs font-bold`}>
            {category === 'pregame' ? '📊 PRE-GAME' : '🔴 LIVE'}
          </div>
        </div>

        {/* Strategy Name */}
        <h2 className="text-3xl font-bold text-white mb-4">{strategyName}</h2>

        {/* Description */}
        <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
          {strategyDescription}
        </p>

        {/* Coming Soon Badge */}
        <div className="inline-block px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xl font-bold rounded-lg shadow-lg mb-6">
          🚀 COMING SOON
        </div>

        {/* Info Text */}
        <div className="text-slate-400 text-sm max-w-xl mx-auto">
          <p className="mb-3">
            This strategy is currently in development. Real-time alerts will be available soon!
          </p>
          <p>
            Enable this strategy in <a href="/strategy-settings" className="text-blue-400 hover:text-blue-300 underline font-semibold">Strategy Settings</a> to receive notifications when it goes live.
          </p>
        </div>

        {/* Stats Preview */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-xs mb-1">Status</div>
            <div className="text-blue-400 font-bold">In Development</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-xs mb-1">Alert Type</div>
            <div className="text-white font-bold">{category === 'pregame' ? 'Pre-Game' : 'Live In-Game'}</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-xs mb-1">Sport</div>
            <div className="text-white font-bold">{sport}</div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-8">
          <a
            href="/learn"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-lg transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Learn More About This Strategy
          </a>
        </div>
      </div>
    </div>
  );
}
