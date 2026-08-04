import { useEffect } from 'react';
import { PickCard, useAgentChat } from '../../hooks/useAgentChat';
import { PickReasoningCard } from './PickReasoningCard';

interface ProactivePicksProps {
  picks: PickCard[];
  loading: boolean;
  error: string | null;
  onFetchPicks: () => void;
  picksFetched: boolean;
}

export function ProactivePicks({ picks, loading, error, onFetchPicks, picksFetched }: ProactivePicksProps) {
  useEffect(() => {
    if (!picksFetched) {
      onFetchPicks();
    }
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading today's top picks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3 px-4">
        <p className="text-sm text-red-400 text-center">{error}</p>
        <button
          onClick={onFetchPicks}
          className="text-xs text-blue-400 hover:text-blue-300 underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (picks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-2 px-4">
        <p className="text-slate-400 text-sm text-center">No picks with edge above 3% today.</p>
        <p className="text-slate-500 text-xs text-center">Check back as more games go live.</p>
        <button
          onClick={onFetchPicks}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300 underline"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-3 overflow-y-auto">
      <div className="flex items-center justify-between px-1">
        <p className="text-xs text-slate-500">Today's top {picks.length} model picks</p>
        <button
          onClick={onFetchPicks}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          title="Refresh picks"
        >
          ↻ Refresh
        </button>
      </div>
      {picks.map(pick => (
        <PickReasoningCard key={pick.id} pick={pick} />
      ))}
    </div>
  );
}
