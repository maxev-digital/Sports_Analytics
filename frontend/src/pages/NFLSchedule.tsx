/**
 * NFL Schedule — lists upcoming NFL games from ESPN (no Odds API needed)
 * Each game card links to the Matchup Center.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Tv } from 'lucide-react';

const MUTED   = 'oklch(70.8% 0 0)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const BORDER  = 'oklch(100% 0 0 / .1)';
const CARD_BG = 'oklch(24% 0 0)';

const ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard';

interface NFLGame {
  id: string;
  name: string;
  shortName: string;
  date: string;
  status: string;
  homeTeam: { name: string; abbr: string; logo: string; score?: string };
  awayTeam: { name: string; abbr: string; logo: string; score?: string };
  tv: string;
  venue: string;
  week: number;
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric',
      hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago',
    }) + ' CT';
  } catch { return iso; }
}

function TeamBlock({ team, isHome }: { team: NFLGame['homeTeam']; isHome: boolean }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      flexDirection: isHome ? 'row-reverse' : 'row',
      flex: 1,
    }}>
      <img src={team.logo} alt={team.abbr} style={{ width: 40, height: 40, objectFit: 'contain' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
      <div style={{ textAlign: isHome ? 'right' : 'left' }}>
        <div style={{ fontSize: '0.65rem', color: MUTED, fontWeight: 700, letterSpacing: '0.06em' }}>
          {isHome ? 'HOME' : 'AWAY'}
        </div>
        <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--foreground)' }}>{team.abbr}</div>
        <div style={{ fontSize: '0.72rem', color: MUTED }}>{team.name}</div>
        {team.score != null && (
          <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--foreground)' }}>{team.score}</div>
        )}
      </div>
    </div>
  );
}

function GameCard({ game }: { game: NFLGame }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const isLive = game.status === 'in';
  const isFinal = game.status === 'post';

  return (
    <div style={{
      background: CARD_BG,
      border: `1px solid ${isLive ? BLUE + '66' : BORDER}`,
      borderRadius: 10,
      padding: '16px 20px',
    }}>
      {/* Status badge */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
        {isLive && (
          <span style={{ fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.08em', color: '#ef4444', border: '1px solid #ef444444', padding: '2px 8px', borderRadius: 4 }}>
            ● LIVE
          </span>
        )}
        {isFinal && (
          <span style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.06em', color: MUTED, border: `1px solid ${BORDER}`, padding: '2px 8px', borderRadius: 4 }}>
            FINAL
          </span>
        )}
        <span style={{ fontSize: '0.65rem', color: MUTED, display: 'flex', alignItems: 'center', gap: 4 }}>
          <Calendar size={10} /> {fmtDate(game.date)}
        </span>
        {game.tv && (
          <span style={{ fontSize: '0.65rem', color: MUTED, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Tv size={10} /> {game.tv}
          </span>
        )}
        {game.venue && (
          <span style={{ fontSize: '0.65rem', color: MUTED, display: 'flex', alignItems: 'center', gap: 4 }}>
            <MapPin size={10} /> {game.venue}
          </span>
        )}
      </div>

      {/* Teams */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <TeamBlock team={game.awayTeam} isHome={false} />
        <div style={{ fontSize: '0.9rem', fontWeight: 800, color: MUTED, flexShrink: 0 }}>@</div>
        <TeamBlock team={game.homeTeam} isHome={true} />
      </div>

      {/* CTA */}
      {!isFinal && (
        <button
          disabled={loading}
          onClick={async () => {
            setLoading(true);
            navigate(`/matchup/${game.id}`);
          }}
          style={{
            width: '100%',
            background: `${BLUE}18`,
            border: `1px solid ${BLUE}55`,
            color: BLUE,
            borderRadius: 6,
            padding: '8px 0',
            cursor: loading ? 'wait' : 'pointer',
            fontSize: '0.72rem',
            fontWeight: 800,
            letterSpacing: '0.08em',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'LOADING…' : 'MATCHUP CENTER →'}
        </button>
      )}
    </div>
  );
}

export function NFLSchedule() {
  const [games, setGames] = useState<NFLGame[]>([]);
  const [week, setWeek] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(ESPN_SCOREBOARD)
      .then(r => r.json())
      .then(data => {
        const weekNum = data.week?.number ?? null;
        setWeek(weekNum);

        const events: NFLGame[] = (data.events ?? []).map((ev: any) => {
          const comp = ev.competitions?.[0] ?? {};
          const competitors: any[] = comp.competitors ?? [];
          const home = competitors.find((c: any) => c.homeAway === 'home') ?? {};
          const away = competitors.find((c: any) => c.homeAway === 'away') ?? {};

          const tv = (comp.broadcasts ?? [])
            .flatMap((b: any) => b.names ?? [b.name ?? ''])
            .filter(Boolean)
            .join(', ');

          const venue = comp.venue?.fullName ?? comp.venue?.name ?? '';
          const status = ev.status?.type?.state ?? 'pre'; // pre, in, post

          return {
            id: ev.id,
            name: ev.name,
            shortName: ev.shortName,
            date: ev.date,
            status,
            week: weekNum ?? 0,
            tv,
            venue,
            homeTeam: {
              name:  home.team?.shortDisplayName ?? home.team?.name ?? '',
              abbr:  home.team?.abbreviation ?? '',
              logo:  home.team?.logo ?? `https://a.espncdn.com/i/teamlogos/nfl/500-dark/${(home.team?.abbreviation ?? '').toLowerCase()}.png`,
              score: home.score,
            },
            awayTeam: {
              name:  away.team?.shortDisplayName ?? away.team?.name ?? '',
              abbr:  away.team?.abbreviation ?? '',
              logo:  away.team?.logo ?? `https://a.espncdn.com/i/teamlogos/nfl/500-dark/${(away.team?.abbreviation ?? '').toLowerCase()}.png`,
              score: away.score,
            },
          };
        });

        setGames(events);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load schedule.');
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>
          NFL SCHEDULE {week != null ? `— WEEK ${week}` : ''}
        </h1>
        <p style={{ fontSize: '0.8rem', color: MUTED, margin: '6px 0 0' }}>
          Click any game to open the full Matchup Center — odds, power ratings, injuries, and AI angle analysis.
        </p>
      </div>

      {loading && (
        <div style={{ color: MUTED, fontSize: '0.9rem', textAlign: 'center', padding: 40 }}>
          Loading schedule…
        </div>
      )}

      {error && (
        <div style={{ color: '#ef4444', fontSize: '0.9rem', textAlign: 'center', padding: 40 }}>
          {error}
        </div>
      )}

      {!loading && !error && games.length === 0 && (
        <div style={{ color: MUTED, fontSize: '0.9rem', textAlign: 'center', padding: 40 }}>
          No games scheduled this week.
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 14 }}>
        {games.map(g => <GameCard key={g.id} game={g} />)}
      </div>
    </div>
  );
}
