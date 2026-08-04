/**
 * SurvivorStrategy — The "STRATEGY" tab for the Survivor Helper.
 * Presents the conceptual framework (EV, Future Value, Contrarianism,
 * Holiday planning, Multi-entry) derived from survivor pool game theory.
 * All logic is schedule-driven — no hardcoded team rankings.
 */

const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const YELLOW  = 'oklch(79.5% .184 86.047)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const ORANGE  = 'oklch(72% .19 50)';
const MUTED   = 'var(--c-muted)';
const PANEL   = 'var(--c-panel)';
const BORDER  = 'var(--c-border)';
const FG      = 'var(--c-fg)';
const BG      = 'var(--c-bg)';

interface Game {
  home: string; away: string;
  home_name: string; away_name: string;
  date: string;
  home_wp: number; away_wp: number;
  home_label: string; away_label: string;
}

interface TeamFv { team: string; team_name: string; rating: number; fvScore: number; greatWeeks: number; goodWeeks: number; }

function getGameTags(date: string) {
  if (!date) return { isThanksgiving: false, isChristmas: false };
  const d = new Date(date + 'T12:00:00');
  const mm = d.getMonth() + 1;
  const dd = d.getDate();
  return { isThanksgiving: mm === 11 && dd === 26, isChristmas: mm === 12 && dd === 25 };
}

export function computeFutureValue(team: string, afterWeek: number, weeks: Record<number, Game[]>): number {
  let score = 0;
  for (const [wkStr, games] of Object.entries(weeks)) {
    if (Number(wkStr) <= afterWeek) continue;
    for (const g of games) {
      const wp = g.home === team ? g.home_wp : g.away === team ? g.away_wp : null;
      if (wp === null) continue;
      if (wp >= 0.73) score += 2;        // GREAT matchup
      else if (wp >= 0.58) score += 1;   // GOOD matchup
    }
  }
  return Math.min(score, 12);
}

export function findHolidayDoubles(weeks: Record<number, Game[]>): Set<string> {
  const thanksTeams = new Set<string>();
  const xmasTeams   = new Set<string>();
  for (const games of Object.values(weeks)) {
    for (const g of games) {
      const tags = getGameTags(g.date);
      if (tags.isThanksgiving) { thanksTeams.add(g.home); thanksTeams.add(g.away); }
      if (tags.isChristmas)    { xmasTeams.add(g.home);   xmasTeams.add(g.away);   }
    }
  }
  const doubles = new Set<string>();
  for (const t of thanksTeams) { if (xmasTeams.has(t)) doubles.add(t); }
  return doubles;
}

export function getWeekHazard(wk: number, games: Game[]): 'trap' | 'thin' | 'holiday' | null {
  if (wk === 1) return 'trap';
  const hasHoliday = games.some(g => {
    const t = getGameTags(g.date);
    return t.isThanksgiving || t.isChristmas;
  });
  if (hasHoliday) return 'holiday';
  const maxWp = Math.max(0, ...games.flatMap(g => [g.home_wp, g.away_wp]));
  if (maxWp < 0.62) return 'thin';
  return null;
}

function getLogo(abbr: string): string {
  const map: Record<string, string> = {
    ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
    DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
    LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
    NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
  };
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${map[abbr] ?? abbr.toLowerCase()}.png`;
}

// ── Concept card ──────────────────────────────────────────────────────────────
function ConceptCard({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderLeft: `3px solid ${color}`, borderRadius: 8, padding: '14px 16px' }}>
      <div style={{ fontSize: '0.68rem', fontWeight: 800, color, letterSpacing: '0.1em', marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: '0.72rem', color: MUTED, lineHeight: 1.65 }}>{children}</div>
    </div>
  );
}

// ── Hazard badge ──────────────────────────────────────────────────────────────
const HAZARD_META = {
  trap:    { label: '⚠ TRAP',     color: RED    },
  thin:    { label: '⚡ THIN',     color: YELLOW },
  holiday: { label: '🏈 HOLIDAY',  color: ORANGE },
} as const;

// ── Main export ───────────────────────────────────────────────────────────────
interface Props {
  teams: { team: string; team_name: string; rating: number; tier: string; schedule: { week: number; wp: number; label: string }[] }[];
  weeks: Record<number, Game[]>;
  used:  Set<string>;
}

export function SurvivorStrategy({ teams, weeks, used }: Props) {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);
  const holidayDoubles = findHolidayDoubles(weeks);

  // FV rankings for available teams (week 0 = from the start)
  const fvRanked: TeamFv[] = teams
    .filter(t => !used.has(t.team))
    .map(t => {
      let great = 0, good = 0;
      for (const s of t.schedule) {
        if (s.wp >= 0.73) great++;
        else if (s.wp >= 0.58) good++;
      }
      return { team: t.team, team_name: t.team_name, rating: t.rating, fvScore: great * 2 + good, greatWeeks: great, goodWeeks: good };
    })
    .sort((a, b) => b.fvScore - a.fvScore)
    .slice(0, 16);

  // Holiday double-used conflicts
  const holidayConflicts = [...holidayDoubles].filter(t => used.has(t));

  return (
    <div style={{ display: 'grid', gap: 24 }}>

      {/* ── Holiday conflict alert ────────────────────────────── */}
      {holidayConflicts.length > 0 && (
        <div style={{ background: RED + '15', border: `1px solid ${RED}40`, borderRadius: 8, padding: '12px 16px', fontSize: '0.72rem', color: RED }}>
          <strong>Holiday Conflict:</strong>{' '}
          {holidayConflicts.map(t => teams.find(x => x.team === t)?.team_name ?? t).join(', ')}{' '}
          {holidayConflicts.length === 1 ? 'plays' : 'play'} on <em>both</em> Thanksgiving and Christmas.
          You've already used {holidayConflicts.length > 1 ? 'them' : 'this team'} — make sure you have coverage for both holiday slates.
        </div>
      )}

      {/* ── Strategy framework ───────────────────────────────── */}
      <div>
        <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED, letterSpacing: '0.12em', marginBottom: 12 }}>CORE FRAMEWORK</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
          <ConceptCard title="EXPECTED VALUE (EV)" color={EMERALD}>
            EV is not just your team's win odds — it's win odds × the value of surviving when others don't.
            A team that's 70% to win but picked by 60% of the field delivers less leverage than a 65% team at 15% pick share.
            Think of it like pot odds in poker: the payout (field contraction) must justify the risk.
          </ConceptCard>
          <ConceptCard title="FUTURE VALUE (FV)" color={BLUE}>
            Every team can only be used once. High-FV teams have multiple remaining weeks as strong favorites.
            Burning a high-FV team early means losing their best upcoming matchup.
            Rule of thumb: use low-FV teams when they have an above-average EV. Save high-FV teams for when they're hardest to replace.
          </ConceptCard>
          <ConceptCard title="MEASURED CONTRARIANISM" color={ORANGE}>
            Don't fade the chalk just to be clever. 2024 Circa winners took the top-2 most popular pick 65%+ of the time.
            Go contrarian only when: (1) the popular team has real upset risk, (2) you have a comparable alternative,
            and (3) surviving an upset wipes out a large chunk of the field — giving your entry outsized equity.
          </ConceptCard>
          <ConceptCard title="HOLIDAY WEEKS: DIFFERENT ANIMAL" color={YELLOW}>
            Thanksgiving and Christmas restrict you to 6–8 teams. Pick popularity can spike over 50% on a single favorite.
            When chalk exceeds 50%, taking an underdog becomes strategically viable — not because it's +EV in isolation,
            but because surviving wipes out half the remaining field. Plan weeks ahead so you have real options,
            not just the leftovers.
          </ConceptCard>
          <ConceptCard title="POOL SIZE CHANGES EVERYTHING" color={EMERALD}>
            Small office pool (20–50 entries): chaotic, can end in weeks. Future value matters less.
            Circa-scale (10,000+ entries): assume you must go 18–20 correct picks. That makes every high-FV team
            a scarce, one-time asset. Playing safe each week won't separate you — you need smart risk.
          </ConceptCard>
          <ConceptCard title="MULTI-ENTRY PORTFOLIO" color={BLUE}>
            Spreading 2–3 teams per week when you have multiple entries gives the best balance:
            you reduce the chance of a single upset wiping everything, while creating leverage when
            others are eliminated. Don't fully correlate entries (all on the same team) — and don't
            over-diversify with 5+ different picks. 2–3 is the sweet spot for most live weeks.
          </ConceptCard>
        </div>
      </div>

      {/* ── FV rankings ──────────────────────────────────────── */}
      <div>
        <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED, letterSpacing: '0.12em', marginBottom: 12 }}>
          FUTURE VALUE RANKINGS — AVAILABLE TEAMS
        </div>
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                {['#','Team','Rating','FV Score','Great Wks','Good Wks','Holiday Both?'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: h === 'Team' ? 'left' : 'right',
                    fontSize: '0.6rem', fontWeight: 700, color: MUTED, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fvRanked.map((t, i) => {
                const isDouble = holidayDoubles.has(t.team);
                return (
                  <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <td style={{ padding: '7px 12px', textAlign: 'right', color: MUTED, fontSize: '0.68rem' }}>{i + 1}</td>
                    <td style={{ padding: '7px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <img src={getLogo(t.team)} alt={t.team} style={{ width: 20, height: 20 }}
                          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        <div>
                          <div style={{ fontWeight: 700, color: FG }}>{t.team}</div>
                          <div style={{ fontSize: '0.6rem', color: MUTED }}>{t.team_name}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '7px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700,
                      color: t.rating >= 4 ? EMERALD : t.rating >= 0 ? YELLOW : RED }}>
                      {t.rating >= 0 ? '+' : ''}{t.rating.toFixed(1)}
                    </td>
                    <td style={{ padding: '7px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 800,
                      color: t.fvScore >= 8 ? EMERALD : t.fvScore >= 4 ? BLUE : MUTED, fontSize: '0.9rem' }}>
                      {t.fvScore}
                    </td>
                    <td style={{ padding: '7px 12px', textAlign: 'right', color: EMERALD, fontFamily: 'monospace' }}>{t.greatWeeks}</td>
                    <td style={{ padding: '7px 12px', textAlign: 'right', color: BLUE, fontFamily: 'monospace' }}>{t.goodWeeks}</td>
                    <td style={{ padding: '7px 12px', textAlign: 'right' }}>
                      {isDouble && (
                        <span style={{ fontSize: '0.62rem', fontWeight: 700, padding: '2px 7px', borderRadius: 10,
                          background: YELLOW + '20', color: YELLOW, border: `1px solid ${YELLOW}40` }}>
                          🦃🎄 BOTH
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div style={{ padding: '8px 12px', fontSize: '0.62rem', color: MUTED, borderTop: `1px solid ${BORDER}` }}>
            FV Score = (GREAT weeks × 2) + (GOOD weeks × 1) · GREAT = WP ≥ 73% · GOOD = WP ≥ 58% · Max 12
          </div>
        </div>
      </div>

      {/* ── Week hazard map ───────────────────────────────────── */}
      <div>
        <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED, letterSpacing: '0.12em', marginBottom: 12 }}>
          WEEK HAZARD MAP
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {weekNums.map(wk => {
            const games = weeks[wk] ?? [];
            const hazard = getWeekHazard(wk, games);
            const maxWp  = Math.max(0, ...games.flatMap(g => [g.home_wp, g.away_wp]));
            const meta   = hazard ? HAZARD_META[hazard] : null;
            return (
              <div key={wk} style={{
                minWidth: 72, padding: '8px 10px', borderRadius: 8, textAlign: 'center',
                background: meta ? meta.color + '12' : PANEL,
                border: `1px solid ${meta ? meta.color + '40' : BORDER}`,
              }}>
                <div style={{ fontSize: '0.6rem', fontWeight: 700, color: MUTED }}>WK {wk}</div>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, fontFamily: 'monospace',
                  color: maxWp >= 0.73 ? EMERALD : maxWp >= 0.58 ? BLUE : maxWp >= 0.45 ? YELLOW : RED }}>
                  {maxWp > 0 ? `${Math.round(maxWp * 100)}%` : '—'}
                </div>
                {meta && (
                  <div style={{ fontSize: '0.55rem', fontWeight: 700, color: meta.color, marginTop: 2 }}>{meta.label}</div>
                )}
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 8, fontSize: '0.62rem', color: MUTED }}>
          Number shown = best available win probability that week · ⚠ TRAP = Week 1 (limited game film) ·
          ⚡ THIN = best WP &lt; 62% · 🏈 HOLIDAY = restricted slate
        </div>
      </div>

      {/* ── Holiday planner ───────────────────────────────────── */}
      {holidayDoubles.size > 0 && (
        <div>
          <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED, letterSpacing: '0.12em', marginBottom: 12 }}>
            HOLIDAY PLANNER — TEAMS ON BOTH THANKSGIVING & CHRISTMAS
          </div>
          <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, padding: '14px 16px' }}>
            <div style={{ fontSize: '0.72rem', color: MUTED, marginBottom: 12, lineHeight: 1.6 }}>
              These teams play on both holiday slates. You can only use each team once —
              so if you use them on Thanksgiving, they're unavailable for Christmas and vice versa.
              Plan which holiday each entry will use them on <em>before</em> the season starts.
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {[...holidayDoubles].map(abbr => {
                const t = teams.find(x => x.team === abbr);
                const isUsed = used.has(abbr);
                return (
                  <div key={abbr} style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px',
                    borderRadius: 8, border: `1px solid ${isUsed ? RED + '50' : YELLOW + '50'}`,
                    background: isUsed ? RED + '10' : YELLOW + '10',
                    opacity: isUsed ? 0.6 : 1,
                  }}>
                    <img src={getLogo(abbr)} alt={abbr} style={{ width: 24, height: 24, filter: isUsed ? 'grayscale(80%)' : 'none' }}
                      onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                    <div>
                      <div style={{ fontWeight: 700, color: isUsed ? MUTED : FG, fontSize: '0.8rem' }}>
                        {t?.team_name ?? abbr}
                      </div>
                      <div style={{ fontSize: '0.6rem', color: isUsed ? RED : YELLOW }}>
                        {isUsed ? 'ALREADY USED' : '🦃 + 🎄 both slates'}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── EV framing note ──────────────────────────────────── */}
      <div style={{ padding: '12px 16px', background: BG, border: `1px solid ${BORDER}`, borderRadius: 8,
        fontSize: '0.65rem', color: MUTED, lineHeight: 1.7 }}>
        <strong style={{ color: FG }}>The Bottom Line:</strong>{' '}
        Win probability tells you how likely your team is to win. Future Value tells you what you're giving up by using them now.
        EV combines both with field behavior — it's the metric that actually drives long-term survivor contest equity.
        No tool replaces judgment, but the framework above (EV + FV + measured contrarianism + holiday planning) is what
        separates multi-week survivors from first-round exits in large-field contests.
      </div>

    </div>
  );
}
