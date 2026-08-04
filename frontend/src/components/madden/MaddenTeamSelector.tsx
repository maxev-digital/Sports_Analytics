const NFL_TEAMS = [
  { abbr: 'ARI', name: 'Cardinals',    conf: 'NFC' },
  { abbr: 'ATL', name: 'Falcons',      conf: 'NFC' },
  { abbr: 'BAL', name: 'Ravens',       conf: 'AFC' },
  { abbr: 'BUF', name: 'Bills',        conf: 'AFC' },
  { abbr: 'CAR', name: 'Panthers',     conf: 'NFC' },
  { abbr: 'CHI', name: 'Bears',        conf: 'NFC' },
  { abbr: 'CIN', name: 'Bengals',      conf: 'AFC' },
  { abbr: 'CLE', name: 'Browns',       conf: 'AFC' },
  { abbr: 'DAL', name: 'Cowboys',      conf: 'NFC' },
  { abbr: 'DEN', name: 'Broncos',      conf: 'AFC' },
  { abbr: 'DET', name: 'Lions',        conf: 'NFC' },
  { abbr: 'GB',  name: 'Packers',      conf: 'NFC' },
  { abbr: 'HOU', name: 'Texans',       conf: 'AFC' },
  { abbr: 'IND', name: 'Colts',        conf: 'AFC' },
  { abbr: 'JAX', name: 'Jaguars',      conf: 'AFC' },
  { abbr: 'KC',  name: 'Chiefs',       conf: 'AFC' },
  { abbr: 'LAC', name: 'Chargers',     conf: 'AFC' },
  { abbr: 'LAR', name: 'Rams',         conf: 'NFC' },
  { abbr: 'LV',  name: 'Raiders',      conf: 'AFC' },
  { abbr: 'MIA', name: 'Dolphins',     conf: 'AFC' },
  { abbr: 'MIN', name: 'Vikings',      conf: 'NFC' },
  { abbr: 'NE',  name: 'Patriots',     conf: 'AFC' },
  { abbr: 'NO',  name: 'Saints',       conf: 'NFC' },
  { abbr: 'NYG', name: 'Giants',       conf: 'NFC' },
  { abbr: 'NYJ', name: 'Jets',         conf: 'AFC' },
  { abbr: 'PHI', name: 'Eagles',       conf: 'NFC' },
  { abbr: 'PIT', name: 'Steelers',     conf: 'AFC' },
  { abbr: 'SEA', name: 'Seahawks',     conf: 'NFC' },
  { abbr: 'SF',  name: '49ers',        conf: 'NFC' },
  { abbr: 'TB',  name: 'Buccaneers',   conf: 'NFC' },
  { abbr: 'TEN', name: 'Titans',       conf: 'AFC' },
  { abbr: 'WAS', name: 'Commanders',   conf: 'NFC' },
] as const;

interface Props {
  selected: string | null;
  onSelect: (abbr: string | null) => void;
}

export function MaddenTeamSelector({ selected, onSelect }: Props) {
  const afc = NFL_TEAMS.filter(t => t.conf === 'AFC');
  const nfc = NFL_TEAMS.filter(t => t.conf === 'NFC');

  const teamBtn = (abbr: string, name: string) => (
    <button
      key={abbr}
      onClick={() => onSelect(selected === abbr ? null : abbr)}
      className={`px-2 py-1.5 rounded text-xs font-bold transition-all border ${
        selected === abbr
          ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-600/30'
          : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-500 hover:text-white'
      }`}
    >
      <div className="font-mono text-sm">{abbr}</div>
      <div className="text-slate-400 text-[10px] font-normal mt-0.5 truncate w-14">{name}</div>
    </button>
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">AFC</span>
        <div className="flex-1 h-px bg-slate-700" />
      </div>
      <div className="flex flex-wrap gap-2">
        {afc.map(t => teamBtn(t.abbr, t.name))}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">NFC</span>
        <div className="flex-1 h-px bg-slate-700" />
      </div>
      <div className="flex flex-wrap gap-2">
        {nfc.map(t => teamBtn(t.abbr, t.name))}
      </div>
    </div>
  );
}
