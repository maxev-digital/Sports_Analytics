import { useState, useEffect } from 'react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';
const SURFACE    = 'oklch(15.6% 0 0)';

function StatusDot({ status }: { status: string }) {
  const color = status === 'healthy' ? EMERALD : status === 'warning' ? YELLOW : status === 'critical' ? BRAND_RED : MUTED_FG;
  const label = status?.toUpperCase() ?? 'UNKNOWN';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span style={{ position: 'relative', display: 'inline-flex', width: 10, height: 10 }}>
        {status === 'healthy' && (
          <span style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            background: color, opacity: 0.5, animation: 'ping 1.5s cubic-bezier(0,0,.2,1) infinite',
          }} />
        )}
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
      </span>
      <span style={{ color, fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em' }}>{label}</span>
    </span>
  );
}

function AgentCard({ tier, name, description, status, lastRun, tokensSaved }: {
  tier: 'fast' | 'core' | 'deep';
  name: string;
  description: string;
  status: string;
  lastRun?: string;
  tokensSaved?: string;
}) {
  const tierColors: Record<string, string> = { fast: BLUE, core: YELLOW, deep: EMERALD };
  const color = tierColors[tier] ?? MUTED_FG;
  return (
    <div className="data-table-wrap" style={{ padding: '16px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{
              background: color, color: '#000', fontSize: '0.6rem', fontWeight: 900,
              padding: '2px 7px', borderRadius: 4, letterSpacing: '0.06em',
            }}>{tier.toUpperCase()}</span>
            <span style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, fontSize: '0.9rem' }}>{name}</span>
          </div>
          <p style={{ color: MUTED_FG, fontSize: '0.78rem', margin: 0 }}>{description}</p>
        </div>
        <StatusDot status={status} />
      </div>
      <div style={{ display: 'flex', gap: 20, marginTop: 8 }}>
        {lastRun && (
          <div>
            <div style={{ color: MUTED_FG, fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Run</div>
            <div style={{ color: 'oklch(98.5% 0 0)', fontSize: '0.78rem', fontWeight: 600 }}>{lastRun}</div>
          </div>
        )}
        {tokensSaved && (
          <div>
            <div style={{ color: MUTED_FG, fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Cost Tier</div>
            <div style={{ color, fontSize: '0.78rem', fontWeight: 600 }}>{tokensSaved}</div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, subValue, color }: {
  label: string; value: string | number; subValue?: string; color?: string;
}) {
  return (
    <div className="data-table-wrap" style={{ padding: '16px 20px', textAlign: 'center' }}>
      <div style={{ color: MUTED_FG, fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</div>
      <div style={{ color: color ?? 'oklch(98.5% 0 0)', fontSize: '1.6rem', fontWeight: 900, lineHeight: 1 }}>{value}</div>
      {subValue && <div style={{ color: MUTED_FG, fontSize: '0.72rem', marginTop: 4 }}>{subValue}</div>}
    </div>
  );
}

function IngestionRow({ sport, data }: { sport: string; data: any }) {
  const validPct = data?.records_fetched > 0
    ? Math.round((data.records_valid / data.records_fetched) * 100)
    : null;
  const status = data?.status === 'ok' ? 'healthy' : data?.status === 'error' ? 'critical' : 'warning';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16,
      padding: '12px 0', borderBottom: `1px solid ${BORDER}`,
    }}>
      <div style={{ width: 60 }}>
        <span style={{
          background: sport === 'mlb' ? BRAND_RED : BLUE, color: '#fff',
          fontSize: '0.65rem', fontWeight: 800, padding: '2px 8px', borderRadius: 4,
        }}>{sport.toUpperCase()}</span>
      </div>
      <StatusDot status={status} />
      <div style={{ flex: 1 }}>
        <span style={{ color: MUTED_FG, fontSize: '0.78rem' }}>
          {data?.records_fetched ?? 0} fetched
          {validPct !== null && ` · ${validPct}% valid`}
          {data?.records_rejected > 0 && (
            <span style={{ color: YELLOW, marginLeft: 6 }}>
              {data.records_rejected} flagged
            </span>
          )}
        </span>
      </div>
      {data?.haiku_flags?.length > 0 && (
        <div style={{ fontSize: '0.7rem', color: YELLOW, maxWidth: 200, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
          ⚠ {Array.isArray(data.haiku_flags) ? data.haiku_flags[0] : data.haiku_flags}
        </div>
      )}
    </div>
  );
}

export function SystemHealth() {
  const [health, setHealth]           = useState<any>(null);
  const [reflections, setReflections] = useState<any[]>([]);
  const [ingestionLog, setIngestionLog] = useState<any[]>([]);
  const [loading, setLoading]         = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [lastTriggered, setLastTriggered]     = useState<string | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [healthRes, refRes, logRes] = await Promise.all([
        fetch(getApiUrl('v2/edges/health')).then(r => r.json()).catch(() => null),
        fetch(getApiUrl('v2/edges/reflection?days=7')).then(r => r.json()).catch(() => ({ reports: [] })),
        fetch(getApiUrl('v2/edges/ingestion-log?days=3')).then(r => r.json()).catch(() => ({ log: [] })),
      ]);
      setHealth(healthRes);
      setReflections(refRes?.reports ?? []);
      setIngestionLog(logRes?.log ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const triggerPipeline = async () => {
    setPipelineRunning(true);
    setLastTriggered(new Date().toLocaleTimeString('en-US', { timeZone: 'America/Chicago', hour: '2-digit', minute: '2-digit' }));
    try {
      await fetch(getApiUrl('v2/edges/run-pipeline'), { method: 'POST' });
      setTimeout(fetchAll, 5000); // re-fetch after 5s
    } catch (e) {
      console.error('Pipeline trigger failed:', e);
    } finally {
      setTimeout(() => setPipelineRunning(false), 3000);
    }
  };

  const overallStatus = health?.overall_status ?? 'initializing';
  const todayPicks    = health?.predictions?.total ?? 0;
  const mlbPerf  = health?.model_performance?.mlb_30d  ?? {};
  const wnbaPerf = health?.model_performance?.wnba_30d ?? {};

  return (
    <div style={{ padding: '24px 20px', maxWidth: 1200, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: 'oklch(98.5% 0 0)', fontSize: '1.4rem', fontWeight: 900, margin: 0, letterSpacing: '-0.02em' }}>
            SYSTEM HEALTH
          </h1>
          <p style={{ color: MUTED_FG, fontSize: '0.78rem', margin: '4px 0 0' }}>
            Agentic pipeline — 3-tier agent stack
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {!loading && <StatusDot status={overallStatus} />}
          <button
            onClick={triggerPipeline}
            disabled={pipelineRunning}
            style={{
              background: pipelineRunning ? SIDEBAR_BG : BRAND_RED,
              border: `1px solid ${pipelineRunning ? BORDER : BRAND_RED}`,
              color: pipelineRunning ? MUTED_FG : '#fff',
              padding: '8px 16px', borderRadius: 8,
              fontSize: '0.8rem', fontWeight: 700, cursor: pipelineRunning ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {pipelineRunning ? 'Running...' : 'Run Pipeline'}
          </button>
          {lastTriggered && (
            <span style={{ color: MUTED_FG, fontSize: '0.72rem' }}>Last triggered {lastTriggered} CST</span>
          )}
        </div>
      </div>

      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 90, borderRadius: 8 }} />
          ))}
        </div>
      )}

      {!loading && (
        <>
          {/* Summary metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 24 }}>
            <MetricCard label="Today's Picks" value={todayPicks} subValue="above threshold" color={EMERALD} />
            <MetricCard
              label="MLB 30d Win Rate"
              value={mlbPerf.win_rate ? `${(mlbPerf.win_rate * 100).toFixed(1)}%` : '—'}
              subValue={mlbPerf.total_picks ? `${mlbPerf.total_picks} picks` : 'No data yet'}
              color={mlbPerf.win_rate > 0.52 ? EMERALD : YELLOW}
            />
            <MetricCard
              label="WNBA 30d Win Rate"
              value={wnbaPerf.win_rate ? `${(wnbaPerf.win_rate * 100).toFixed(1)}%` : '—'}
              subValue={wnbaPerf.total_picks ? `${wnbaPerf.total_picks} picks` : 'No data yet'}
              color={wnbaPerf.win_rate > 0.52 ? EMERALD : YELLOW}
            />
            <MetricCard
              label="Model Health"
              value={health?.reflection_summary ? 'Active' : 'Init'}
              subValue="Daily reflection"
              color={overallStatus === 'healthy' ? EMERALD : YELLOW}
            />
          </div>

          {/* Agent tier cards */}
          <div className="data-table-wrap" style={{ padding: '16px 20px', marginBottom: 20 }}>
            <p className="section-title" style={{ marginBottom: 12 }}>Agent Layer</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
              <AgentCard
                tier="fast"
                name="Data Validator"
                description="Record-level validation on every ingested row. Flags anomalies in advanced stats and odds data cheaply."
                status={health?.ingestion ? 'healthy' : 'initializing'}
                lastRun={ingestionLog[0] ? new Date(ingestionLog[0].run_at_cst).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                tokensSaved="~200 tok/call"
              />
              <AgentCard
                tier="core"
                name="Pick Reasoner"
                description="Generates data-driven narratives for each edge pick. Explains the statistical signal behind every recommendation."
                status={todayPicks > 0 ? 'healthy' : 'initializing'}
                lastRun={health?.last_updated_cst ? new Date(health.last_updated_cst).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                tokensSaved="~250 tok/call"
              />
              <AgentCard
                tier="deep"
                name="Daily Reflector"
                description="Reviews the full day's predictions holistically. Can halt logging if critical issues detected. Runs once daily."
                status={reflections.length > 0 ? reflections[0]?.model_health ?? 'healthy' : 'initializing'}
                lastRun={reflections[0] ? new Date(reflections[0].run_at_cst).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Never'}
                tokensSaved="~1500 tok/call"
              />
            </div>
          </div>

          {/* Data ingestion status */}
          <div className="data-table-wrap" style={{ padding: '16px 20px', marginBottom: 20 }}>
            <p className="section-title" style={{ marginBottom: 12 }}>Data Ingestion — Last 3 Days</p>
            {ingestionLog.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <p>No ingestion runs yet. Trigger the pipeline to start.</p>
              </div>
            ) : (
              <div>
                {['mlb', 'wnba'].map(sport => {
                  const latest = ingestionLog.find(l => l.sport === sport);
                  return <IngestionRow key={sport} sport={sport} data={latest} />;
                })}
                <div style={{ marginTop: 12 }}>
                  <p className="section-title" style={{ marginBottom: 8 }}>Full Log</p>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Time (CST)</th><th>Sport</th><th>Source</th>
                          <th>Fetched</th><th>Valid</th><th>Rejected</th><th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ingestionLog.slice(0, 10).map((row, i) => (
                          <tr key={i}>
                            <td style={{ fontSize: '0.75rem' }}>
                              {new Date(row.run_at_cst).toLocaleString('en-US', { timeZone: 'America/Chicago', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </td>
                            <td>{row.sport?.toUpperCase()}</td>
                            <td style={{ fontSize: '0.72rem', color: MUTED_FG }}>{row.source}</td>
                            <td>{row.records_fetched}</td>
                            <td style={{ color: EMERALD }}>{row.records_valid}</td>
                            <td style={{ color: row.records_rejected > 0 ? YELLOW : MUTED_FG }}>{row.records_rejected}</td>
                            <td>
                              <StatusDot status={row.status === 'ok' ? 'healthy' : 'critical'} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Daily reflection reports */}
          <div className="data-table-wrap" style={{ padding: '16px 20px', marginBottom: 20 }}>
            <p className="section-title" style={{ marginBottom: 12 }}>Daily Reflection Reports — Last 7 Days</p>
            {reflections.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <p>No reflection reports yet. Runs after the first full pipeline execution.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {reflections.map((r, i) => (
                  <div key={i} style={{
                    background: SURFACE, border: `1px solid ${BORDER}`,
                    borderRadius: 8, padding: '14px 16px',
                    borderLeft: `3px solid ${r.model_health === 'healthy' ? EMERALD : r.model_health === 'warning' ? YELLOW : BRAND_RED}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                        <span style={{ color: MUTED_FG, fontSize: '0.72rem' }}>
                          {new Date(r.report_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                        </span>
                        <StatusDot status={r.model_health ?? 'healthy'} />
                        {r.flags_raised > 0 && (
                          <span style={{ color: YELLOW, fontSize: '0.72rem', fontWeight: 700 }}>
                            {r.flags_raised} flag{r.flags_raised > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                      <span style={{ color: MUTED_FG, fontSize: '0.72rem' }}>
                        {r.total_picks} picks reviewed
                      </span>
                    </div>
                    {r.opus_narrative && (
                      <p style={{ color: 'oklch(85% 0 0)', fontSize: '0.82rem', fontStyle: 'italic', margin: '0 0 8px', lineHeight: 1.5 }}>
                        "{r.opus_narrative}"
                      </p>
                    )}
                    {r.action_items && (() => {
                      try {
                        const items: string[] = JSON.parse(r.action_items);
                        if (!items.length) return null;
                        return (
                          <div>
                            <p style={{ color: MUTED_FG, fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Action Items</p>
                            <ul style={{ margin: 0, paddingLeft: 16 }}>
                              {items.map((item, j) => (
                                <li key={j} style={{ color: YELLOW, fontSize: '0.78rem', marginBottom: 2 }}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        );
                      } catch { return null; }
                    })()}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action items from latest health report */}
          {health?.action_items?.length > 0 && (
            <div className="data-table-wrap" style={{ padding: '16px 20px', borderLeft: `3px solid ${YELLOW}` }}>
              <p className="section-title" style={{ marginBottom: 10, color: YELLOW }}>Pending Action Items</p>
              <ul style={{ margin: 0, paddingLeft: 16 }}>
                {health.action_items.map((item: string, i: number) => (
                  <li key={i} style={{ color: 'oklch(90% 0 0)', fontSize: '0.82rem', marginBottom: 6 }}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
