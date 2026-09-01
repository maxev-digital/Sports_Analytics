/**
 * SurvivorSimulator — "SIMULATOR" tab orchestrator.
 * Delegates rendering to OptimalCard, SimPanel, and ComparisonTable.
 * Monte Carlo runs off the main thread via useSurvivorWorker.
 */
import { useState, useMemo } from 'react';
import {
  beamSearch,
  type AlgoPath,
  type SurvivorGame,
  type SurvivorPick,
  type CustomPath,
  type SimResult,
} from './survivorAlgo';
import { COLORS } from './survivorUtils';
import { useSurvivorWorker } from './useSurvivorWorker';
import { SurvivorOptimalCard } from './SurvivorOptimalCard';
import { SurvivorSimPanel } from './SurvivorSimPanel';
import { SurvivorComparisonTable } from './SurvivorComparisonTable';

interface Props {
  weeks: Record<number, SurvivorGame[]>;
  userPicks: Record<number, string>;
  algorithmicPaths: AlgoPath[];
  customPaths: CustomPath[];
}

export function SurvivorSimulator({ weeks, userPicks, algorithmicPaths, customPaths }: Props) {
  const [iters, setIters]           = useState(50_000);
  const [simResults, setSimResults] = useState<Record<string, SimResult>>({});
  const [ran, setRan]               = useState(false);
  const [running, setRunning]       = useState(false);
  const dispatch = useSurvivorWorker();

  const weekNums = useMemo(
    () => Object.keys(weeks).map(Number).sort((a, b) => a - b),
    [weeks],
  );

  const optimalPicks = useMemo(() => beamSearch(weeks), [weeks]);
  const optimalSurvivalProb = Object.values(optimalPicks).reduce((acc, p) => acc * p.wp, 1);

  const optimalPath: AlgoPath = {
    id: 'optimal', name: 'OPTIMAL (BEAM)', color: COLORS.PURPLE, picks: optimalPicks,
  };

  const userPickPath = useMemo((): AlgoPath | null => {
    const pickMap: Record<number, SurvivorPick> = {};
    for (const wk of weekNums) {
      const team = userPicks[wk];
      if (!team) continue;
      const game = (weeks[wk] ?? []).find(g => g.home === team || g.away === team);
      if (!game) continue;
      const isHome = game.home === team;
      pickMap[wk] = {
        week: wk, team, wp: isHome ? game.home_wp : game.away_wp,
        label: isHome ? game.home_label : game.away_label,
        opp: isHome ? game.away : game.home, home: isHome,
      };
    }
    return Object.keys(pickMap).length > 0
      ? { id: 'mypicks', name: 'MY PICKS', color: COLORS.EMERALD, picks: pickMap }
      : null;
  }, [userPicks, weeks, weekNums]);

  const allPaths: AlgoPath[] = [
    optimalPath, ...algorithmicPaths, ...customPaths,
    ...(userPickPath ? [userPickPath] : []),
  ];

  const runSim = () => {
    setRunning(true);
    dispatch(
      { type: 'monteCarlo', paths: allPaths.map(p => ({ id: p.id, picks: p.picks })), iters },
      data => {
        if (data.type !== 'monteCarlo') return;
        setSimResults(data.results);
        setRan(true);
        setRunning(false);
      },
    );
  };

  const comparisonPaths = [optimalPath, ...algorithmicPaths, ...(userPickPath ? [userPickPath] : [])];

  return (
    <div className="grid gap-6">
      <SurvivorOptimalCard weekNums={weekNums} optimalPicks={optimalPicks} survivalProb={optimalSurvivalProb} />
      <SurvivorSimPanel
        allPaths={allPaths} iters={iters} setIters={setIters}
        running={running} ran={ran} simResults={simResults} onRun={runSim}
      />
      <SurvivorComparisonTable paths={comparisonPaths} weekNums={weekNums} optimalPicks={optimalPicks} />
    </div>
  );
}
