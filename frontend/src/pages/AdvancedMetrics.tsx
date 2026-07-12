import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  ReferenceLine, Legend, ScatterChart, Scatter, ZAxis, ComposedChart, Line,
  AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from 'recharts';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

// ── Design tokens ──────────────────────────────────────────────────────────
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';

const AXIS_PROPS = {
  tick:    { fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' },
  axisLine: { stroke: BORDER },
  tickLine: false,
};

// Shared margin + YAxis width used by every zoomable scatter chart.
// YAXIS_W must match the explicit width= set on each YAxis so pixel→data conversion is accurate.
const ZOOM_M   = { top: 10, right: 32, left: 0, bottom: 40 };
const YAXIS_W  = 44;

function useScatterZoom(
  containerRef: React.RefObject<HTMLDivElement | null>,
  data: any[],
  xKey: string,
  yKey: string,
) {
  const [zoomMode, _setZoomMode] = useState(false);
  const [xDomain, setXDomain]   = useState<[number, number] | null>(null);
  const [yDomain, setYDomain]   = useState<[number, number] | null>(null);
  const [selRect, setSelRect]   = useState<{ left: number; top: number; width: number; height: number } | null>(null);
  const [isPanning, setIsPanning] = useState(false);

  const startPx  = useRef<{ x: number; y: number } | null>(null);
  const panStartDomains = useRef<{ cX: [number,number]; cY: [number,number] } | null>(null);

  const dataLen = data.length;
  useEffect(() => { setXDomain(null); setYDomain(null); setSelRect(null); startPx.current = null; }, [dataLen]);

  const setZoomMode = useCallback((v: boolean | ((prev: boolean) => boolean)) => _setZoomMode(v), []);

  const fullX = useMemo(() => {
    const vals = data.map(d => d[xKey]).filter((v): v is number => v != null && isFinite(+v));
    if (!vals.length) return null;
    const mn = Math.min(...vals), mx = Math.max(...vals);
    const pad = (mx - mn) * 0.07 || 0.05;
    return [mn - pad, mx + pad] as [number, number];
  }, [data, xKey]);

  const fullY = useMemo(() => {
    const vals = data.map(d => d[yKey]).filter((v): v is number => v != null && isFinite(+v));
    if (!vals.length) return null;
    const mn = Math.min(...vals), mx = Math.max(...vals);
    const pad = (mx - mn) * 0.07 || 0.05;
    return [mn - pad, mx + pad] as [number, number];
  }, [data, yKey]);

  const curX = xDomain ?? fullX;
  const curY = yDomain ?? fullY;

  const curXRef = useRef(curX);
  const curYRef = useRef(curY);
  curXRef.current = curX;
  curYRef.current = curY;

  const getPlotDims = useCallback(() => {
    const el = containerRef.current;
    if (!el) return null;
    const pLeft = ZOOM_M.left + YAXIS_W;
    const pW    = el.offsetWidth  - pLeft - ZOOM_M.right;
    const pH    = el.offsetHeight - ZOOM_M.top - ZOOM_M.bottom;
    if (pW <= 0 || pH <= 0) return null;
    return { pLeft, pW, pH };
  }, [containerRef]);

  const pxToDataRaw = useCallback((px: { x: number; y: number }, cX: [number,number], cY: [number,number]) => {
    const dims = getPlotDims();
    if (!dims) return null;
    const fx = Math.max(0, Math.min(1, (px.x - dims.pLeft) / dims.pW));
    const fy = Math.max(0, Math.min(1, (px.y - ZOOM_M.top) / dims.pH));
    return {
      x: cX[0] + fx * (cX[1] - cX[0]),
      y: cY[1] - fy * (cY[1] - cY[0]),
    };
  }, [getPlotDims]);

  const pxToData = useCallback((px: { x: number; y: number }) => {
    const cX = curXRef.current;
    const cY = curYRef.current;
    if (!cX || !cY) return null;
    return pxToDataRaw(px, cX, cY);
  }, [pxToDataRaw]);

  // Scroll-wheel zoom centered on cursor — very aggressive factor.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const handleWheel = (e: WheelEvent) => {
      const cX = curXRef.current;
      const cY = curYRef.current;
      if (!cX || !cY) return;
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const px   = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const pt   = pxToDataRaw(px, cX, cY);
      if (!pt) return;
      const factor = e.deltaY > 0 ? 1.7 : 0.35; // zoom out / zoom in — very aggressive
      setXDomain([pt.x - (pt.x - cX[0]) * factor, pt.x + (cX[1] - pt.x) * factor]);
      setYDomain([pt.y - (pt.y - cY[0]) * factor, pt.y + (cY[1] - pt.y) * factor]);
    };
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [containerRef, pxToDataRaw]);

  const onPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    const rect = e.currentTarget.getBoundingClientRect();
    const px = { x: e.clientX - rect.left, y: e.clientY - rect.top };

    if (zoomMode) {
      // Box-select mode
      startPx.current = px;
      setSelRect({ left: px.x, top: px.y, width: 0, height: 0 });
    } else {
      // Pan mode — record start pixel and starting domains
      const cX = curXRef.current;
      const cY = curYRef.current;
      if (!cX || !cY) return;
      startPx.current = { x: e.clientX, y: e.clientY };
      panStartDomains.current = { cX: [...cX] as [number,number], cY: [...cY] as [number,number] };
      setIsPanning(true);
    }
  }, [zoomMode]);

  const onPointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!startPx.current) return;

    if (zoomMode) {
      const rect = e.currentTarget.getBoundingClientRect();
      const cur = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      setSelRect({
        left:   Math.min(startPx.current.x, cur.x),
        top:    Math.min(startPx.current.y, cur.y),
        width:  Math.abs(cur.x - startPx.current.x),
        height: Math.abs(cur.y - startPx.current.y),
      });
    } else if (panStartDomains.current) {
      // Pan: translate domains by pixel delta mapped to data space
      const dims = getPlotDims();
      if (!dims) return;
      const { cX, cY } = panStartDomains.current;
      const dx = e.clientX - startPx.current.x;
      const dy = e.clientY - startPx.current.y;
      const dataXPerPx = (cX[1] - cX[0]) / dims.pW;
      const dataYPerPx = (cY[1] - cY[0]) / dims.pH;
      setXDomain([cX[0] - dx * dataXPerPx, cX[1] - dx * dataXPerPx]);
      setYDomain([cY[0] - dy * dataYPerPx, cY[1] - dy * dataYPerPx]);
    }
  }, [zoomMode, getPlotDims]);

  const onPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!startPx.current) return;
    setIsPanning(false);

    if (zoomMode) {
      const rect = e.currentTarget.getBoundingClientRect();
      const end   = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const start = { x: startPx.current.x, y: startPx.current.y };
      startPx.current = null;
      setSelRect(null);
      if (Math.abs(end.x - start.x) < 10 || Math.abs(end.y - start.y) < 10) return;
      const d0 = pxToData(start);
      const d1 = pxToData(end);
      if (!d0 || !d1) return;
      setXDomain([Math.min(d0.x, d1.x), Math.max(d0.x, d1.x)]);
      setYDomain([Math.min(d0.y, d1.y), Math.max(d0.y, d1.y)]);
    } else {
      startPx.current = null;
      panStartDomains.current = null;
    }
  }, [zoomMode, pxToData]);

  const reset = useCallback(() => {
    setXDomain(null); setYDomain(null); setSelRect(null);
    setIsPanning(false);
    _setZoomMode(false);
    startPx.current = null;
    panStartDomains.current = null;
  }, []);

  const isZoomed = xDomain != null || yDomain != null;

  return {
    xDomainProps: (xDomain ?? fullX ?? ['auto', 'auto']) as [number, number] | ['auto', 'auto'],
    yDomainProps: (yDomain ?? fullY ?? ['auto', 'auto']) as [number, number] | ['auto', 'auto'],
    isZoomed,
    isPanning,
    zoomMode, setZoomMode,
    selRect, onPointerDown, onPointerMove, onPointerUp,
    reset,
  };
}

function ZoomToolbar({ zoom, showLabels, onToggleLabels }: {
  zoom: ReturnType<typeof useScatterZoom>;
  showLabels?: boolean;
  onToggleLabels?: () => void;
}) {
  const hint = zoom.zoomMode
    ? 'Drag a box to zoom into that region'
    : zoom.isZoomed
    ? 'Drag to pan · Scroll to zoom · Drag Zoom for box-select'
    : 'Scroll to zoom in · Drag Zoom to box-select a region';
  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
      <span style={{ color: MUTED_FG, fontSize: '0.7rem', fontFamily: 'Nunito', marginRight: 4 }}>{hint}</span>
      {onToggleLabels && (
        <button
          className={`filter-pill${showLabels ? ' active' : ''}`}
          style={{ fontSize: '0.7rem', padding: '3px 12px' }}
          onClick={onToggleLabels}
        >
          {showLabels ? 'Hide Labels' : 'Show Labels'}
        </button>
      )}
      <button
        className={`filter-pill${zoom.zoomMode ? ' active' : ''}`}
        style={{ fontSize: '0.7rem', padding: '3px 12px' }}
        onClick={() => zoom.setZoomMode((v: boolean) => !v)}
      >
        {zoom.zoomMode ? 'Exit Zoom' : 'Drag Zoom'}
      </button>
      {zoom.isZoomed && (
        <button className="filter-pill" style={{ fontSize: '0.7rem', padding: '3px 12px' }} onClick={zoom.reset}>
          Reset View
        </button>
      )}
    </div>
  );
}

// Overlay: always present when zoomed (for pan) or in zoom mode (for box-select).
// When panning: transparent, grab cursor, no selection rect.
// When in zoom mode: crosshair cursor, draws selection rectangle.
function ZoomOverlay({ zoom }: { zoom: ReturnType<typeof useScatterZoom> }) {
  if (!zoom.zoomMode && !zoom.isZoomed) return null;
  const cursor = zoom.zoomMode ? 'crosshair' : zoom.isPanning ? 'grabbing' : 'grab';
  return (
    <div
      style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, cursor, zIndex: 10, userSelect: 'none' }}
      onPointerDown={zoom.onPointerDown}
      onPointerMove={zoom.onPointerMove}
      onPointerUp={zoom.onPointerUp}
    >
      {zoom.zoomMode && zoom.selRect && zoom.selRect.width > 4 && zoom.selRect.height > 4 && (
        <div style={{
          position: 'absolute',
          left:   zoom.selRect.left,
          top:    zoom.selRect.top,
          width:  zoom.selRect.width,
          height: zoom.selRect.height,
          border: `2px dashed ${EMERALD}`,
          background: `${EMERALD}18`,
          pointerEvents: 'none',
        }} />
      )}
    </div>
  );
}

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

function BettingSignalCard({ title, signals }: {
  title: string;
  signals: { label: string; why: string; action: string; color: string }[];
}) {
  if (!signals.length) return null;
  return (
    <div style={{ background: 'oklch(14% 0.01 265)', border: `1px solid ${YELLOW}50`, borderRadius: 10, padding: '14px 18px' }}>
      <div style={{ fontSize: '0.68rem', fontWeight: 800, color: YELLOW, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>
        {title}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {signals.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: '8px 12px', background: 'oklch(20% 0 0 / .6)', borderRadius: 6 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ color: 'oklch(98% 0 0)', fontWeight: 700, fontSize: '0.82rem' }}>{s.label}</span>
              {s.why && <span style={{ color: MUTED_FG, fontSize: '0.72rem', marginLeft: 8 }}>{s.why}</span>}
            </div>
            <span style={{ color: s.color, fontWeight: 800, fontSize: '0.75rem', whiteSpace: 'nowrap', flexShrink: 0, padding: '2px 8px', borderRadius: 4, background: s.color + '25' }}>
              {s.action}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── MLB scatter sub-components (each owns its own zoom state) ──────────────

function WobaScatter({ data }: { data: any[] }) {
  const cRef = useRef<HTMLDivElement>(null);
  const zoom = useScatterZoom(cRef, data, 'xwOBA', 'woba');
  const [showLabels, setShowLabels] = useState(false);
  const pts  = data.filter(p => (p.xwOBA ?? 0) > 0 && (p.woba ?? 0) > 0);
  return (
    <>
      <ZoomToolbar zoom={zoom} showLabels={showLabels} onToggleLabels={() => setShowLabels(v => !v)} />
      <div ref={cRef} style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={ZOOM_M}>
            <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
            <XAxis dataKey="xwOBA" type="number" name="xwOBA" {...AXIS_PROPS} width={YAXIS_W} domain={zoom.xDomainProps} label={{ value: 'xwOBA', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
            <YAxis dataKey="woba"  type="number" name="wOBA"  {...AXIS_PROPS} width={YAXIS_W} domain={zoom.yDomainProps} label={{ value: 'wOBA', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
            <ZAxis range={[44, 44]} />
            <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const p = payload[0].payload;
              const diff = (p.woba ?? 0) - (p.xwOBA ?? 0);
              return (
                <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                  <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{p.name}</p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>xwOBA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.xwOBA ?? 0).toFixed(3)}</strong></p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>wOBA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.woba ?? 0).toFixed(3)}</strong></p>
                  <p style={{ margin: '4px 0 0', fontSize: '0.72rem', color: diff > 0.010 ? BRAND_RED : diff < -0.010 ? EMERALD : MUTED_FG, fontWeight: 700 }}>
                    {diff > 0.010 ? `+${diff.toFixed(3)} overperforming` : diff < -0.010 ? `${diff.toFixed(3)} buy-low` : 'Near expected'}
                  </p>
                </div>
              );
            }} />
            <ReferenceLine segment={[{ x: 0.2, y: 0.2 }, { x: 0.5, y: 0.5 }]} stroke={MUTED_FG} strokeDasharray="5 5" strokeOpacity={0.5} />
            <Scatter data={pts} shape={(props: any) => {
              const { cx, cy, payload } = props;
              const diff = (payload.woba ?? 0) - (payload.xwOBA ?? 0);
              const fill = diff > 0.010 ? BRAND_RED : diff < -0.010 ? EMERALD : BLUE;
              const isExtreme = Math.abs(diff) > 0.030;
              const lname = payload.name?.split(' ').pop() ?? '';
              return (
                <g>
                  <circle cx={cx} cy={cy} r={isExtreme ? 6 : 4} fill={fill} fillOpacity={isExtreme ? 0.9 : 0.65} />
                  {(showLabels || isExtreme) && (
                    <text x={cx + 7} y={cy + 4} fontSize={9} fill={fill} fontFamily="Nunito"
                      fontWeight={isExtreme ? 'bold' : 'normal'} opacity={isExtreme ? 1 : 0.8}>{lname}</text>
                  )}
                </g>
              );
            }} />
          </ScatterChart>
        </ResponsiveContainer>
        <ZoomOverlay zoom={zoom} />
      </div>
    </>
  );
}

function EraScatter({ data }: { data: any[] }) {
  const cRef = useRef<HTMLDivElement>(null);
  const zoom = useScatterZoom(cRef, data, 'era', 'xERA');
  const [showLabels, setShowLabels] = useState(false);
  const pts  = data.filter(p => (p.era ?? 0) > 0 && (p.xERA ?? 0) > 0);
  return (
    <>
      <ZoomToolbar zoom={zoom} showLabels={showLabels} onToggleLabels={() => setShowLabels(v => !v)} />
      <div ref={cRef} style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={ZOOM_M}>
            <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
            <XAxis dataKey="era"  type="number" name="ERA"  {...AXIS_PROPS} width={YAXIS_W} domain={zoom.xDomainProps} label={{ value: 'ERA', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
            <YAxis dataKey="xERA" type="number" name="xERA" {...AXIS_PROPS} width={YAXIS_W} domain={zoom.yDomainProps} label={{ value: 'xERA', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
            <ZAxis range={[44, 44]} />
            <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const p = payload[0].payload;
              return (
                <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                  <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{p.name}</p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>ERA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.era ?? 0).toFixed(2)}</strong></p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>xERA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.xERA ?? 0).toFixed(2)}</strong></p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>BF: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{p.pa}</strong></p>
                  <p style={{ marginTop: 6, fontSize: '0.72rem', color: (p.xERA ?? 0) < (p.era ?? 0) ? EMERALD : BRAND_RED, fontWeight: 700 }}>
                    {(p.xERA ?? 0) < (p.era ?? 0) ? 'Buy-low (ERA should drop)' : 'Regression risk'}
                  </p>
                </div>
              );
            }} />
            <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 10, y: 10 }]} stroke={MUTED_FG} strokeDasharray="5 5" strokeOpacity={0.5} />
            <Scatter data={pts} shape={(props: any) => {
              const { cx, cy, payload } = props;
              const diff = (payload.xERADiff ?? 0);
              const fill = (payload.xERA ?? 0) < (payload.era ?? 0) ? EMERALD : BRAND_RED;
              const isExtreme = Math.abs(diff) > 0.60;
              const lname = payload.name?.split(' ').pop() ?? '';
              return (
                <g>
                  <circle cx={cx} cy={cy} r={isExtreme ? 6 : 4} fill={fill} fillOpacity={isExtreme ? 0.9 : 0.7} />
                  {(showLabels || isExtreme) && (
                    <text x={cx + 7} y={cy + 4} fontSize={9} fill={fill} fontFamily="Nunito"
                      fontWeight={isExtreme ? 'bold' : 'normal'} opacity={isExtreme ? 1 : 0.8}>{lname}</text>
                  )}
                </g>
              );
            }} />
          </ScatterChart>
        </ResponsiveContainer>
        <ZoomOverlay zoom={zoom} />
      </div>
    </>
  );
}

function HardHitScatter({ data }: { data: any[] }) {
  const cRef = useRef<HTMLDivElement>(null);
  const zoom = useScatterZoom(cRef, data, 'exitVeloAvg', 'barrelPct');
  const [showLabels, setShowLabels] = useState(false);
  const valid = data.filter(p => (p.exitVeloAvg ?? 0) > 0);
  const avgEV  = valid.length ? valid.reduce((s, p) => s + (p.exitVeloAvg ?? 0), 0) / valid.length : 88;
  const avgBrl = valid.length ? valid.reduce((s, p) => s + (p.barrelPct ?? 0), 0) / valid.length : 8;
  return (
    <>
      <ZoomToolbar zoom={zoom} showLabels={showLabels} onToggleLabels={() => setShowLabels(v => !v)} />
      <div ref={cRef} style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={ZOOM_M}>
            <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
            <XAxis dataKey="exitVeloAvg" type="number" name="Exit Velo" {...AXIS_PROPS} width={YAXIS_W} domain={zoom.xDomainProps} unit=" mph" label={{ value: 'Avg Exit Velo (mph)', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
            <YAxis dataKey="barrelPct"   type="number" name="Barrel%"   {...AXIS_PROPS} width={YAXIS_W} domain={zoom.yDomainProps} unit="%" label={{ value: 'Barrel%', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
            <ZAxis range={[44, 44]} />
            <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const p = payload[0].payload;
              return (
                <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                  <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{p.name}</p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>Exit Velo: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.exitVeloAvg ?? 0).toFixed(1)} mph</strong></p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>Barrel%: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.barrelPct ?? 0).toFixed(1)}%</strong></p>
                  <p style={{ color: MUTED_FG, margin: '2px 0' }}>Hard Hit%: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(p.hardHitPct ?? 0).toFixed(1)}%</strong></p>
                </div>
              );
            }} />
            <ReferenceLine x={avgEV}  stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg EV', position: 'top', fill: MUTED_FG, fontSize: 10 }} />
            <ReferenceLine y={avgBrl} stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Brl%', position: 'right', fill: MUTED_FG, fontSize: 10 }} />
            <Scatter data={valid} shape={(props: any) => {
              const { cx, cy, payload } = props;
              const isElite = (payload.exitVeloAvg ?? 0) >= 91 && (payload.barrelPct ?? 0) >= 10;
              const fill = isElite ? BRAND_RED : (payload.exitVeloAvg ?? 0) >= 91 ? YELLOW : BLUE;
              const lname = payload.name?.split(' ').pop() ?? '';
              return (
                <g>
                  <circle cx={cx} cy={cy} r={isElite ? 6 : 4} fill={fill} fillOpacity={0.75} />
                  {(showLabels || isElite) && (
                    <text x={cx + 7} y={cy + 4} fontSize={9} fill={fill} fontFamily="Nunito"
                      fontWeight={isElite ? 'bold' : 'normal'} opacity={isElite ? 1 : 0.8}>{lname}</text>
                  )}
                </g>
              );
            }} />
          </ScatterChart>
        </ResponsiveContainer>
        <ZoomOverlay zoom={zoom} />
      </div>
    </>
  );
}

// ── MLB Statcast view ──────────────────────────────────────────────────────

function MLBStatcast() {
  const [tab, setTab]       = useState<'batting' | 'pitching' | 'hardhit'>('batting');
  const [data, setData]     = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  useEffect(() => {
    setLoading(true); setError(''); setData([]);
    const endpoint = tab === 'batting'
      ? 'analytics-data/statcast/batting?min_pa=50'
      : tab === 'pitching'
      ? 'analytics-data/statcast/pitching?min_pa=50'
      : 'analytics-data/statcast/hard-hit?min_bbe=25';

    fetch(getApiUrl(endpoint))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setData(d.players || d.pitchers || []); setLoading(false); })
      .catch(() => { setError('Advanced stats data unavailable'); setLoading(false); });
  }, [tab]);

  const top15 = data.slice(0, 15);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Sub-tabs */}
      <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none' }}>
        {(['batting', 'pitching', 'hardhit'] as const).map(t => (
          <button key={t} className={`filter-pill${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {t === 'batting' ? 'Expected Batting' : t === 'pitching' ? 'Expected Pitching' : 'Exit Velocity'}
          </button>
        ))}
      </div>

      {loading && <div className="skeleton" style={{ height: 300, borderRadius: 8 }} />}
      {error && <div className="empty-state"><p>{error}</p></div>}

      {!loading && !error && tab === 'batting' && top15.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Betting signals card */}
          {(() => {
            const buyLow = data
              .filter(p => (p.xwOBADiff ?? 0) < -0.020)
              .sort((a, b) => (a.xwOBADiff ?? 0) - (b.xwOBADiff ?? 0))
              .slice(0, 4)
              .map(p => ({
                label: p.name,
                why: `xwOBA ${(p.xwOBA??0).toFixed(3)} vs wOBA ${(p.woba??0).toFixed(3)} — stats should improve`,
                action: 'BUY OVER on hits/bases',
                color: EMERALD,
              }));
            const fade = data
              .filter(p => (p.xwOBADiff ?? 0) > 0.020)
              .sort((a, b) => (b.xwOBADiff ?? 0) - (a.xwOBADiff ?? 0))
              .slice(0, 3)
              .map(p => ({
                label: p.name,
                why: `wOBA ${(p.woba??0).toFixed(3)} exceeds xwOBA — lucky run, expect decline`,
                action: 'FADE in prop bets',
                color: BRAND_RED,
              }));
            return <BettingSignalCard title="Today's Batting Signals — Buy Low / Fade" signals={[...buyLow, ...fade]} />;
          })()}

          {/* Scatter: wOBA vs xwOBA — every qualified batter */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>wOBA vs xwOBA — Every Qualified Hitter</p>
            <p className="data-note" style={{ marginBottom: 8 }}>
              Dots <span style={{ color: EMERALD, fontWeight: 700 }}>above the line</span> = wOBA exceeds xwOBA (overperforming, buy to fade).
              Dots <span style={{ color: BLUE, fontWeight: 700 }}>below the line</span> = underperforming expected (buy-low, positive regression candidate).
              Use <strong>Zoom</strong> to drag-select any region for a closer look.
            </p>
            <WobaScatter data={data} />
          </div>

          {/* xwOBA vs wOBA comparison — Top 15 */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>xwOBA vs wOBA — Top 15 Hitters</p>
            <p className="data-note" style={{ marginBottom: 12 }}>Positive gap = player outperforming expected (potential regression). Negative = underperforming (positive regression candidate).</p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={top15} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis dataKey="name" {...AXIS_PROPS} angle={-40} textAnchor="end" interval={0} />
                <YAxis {...AXIS_PROPS} domain={['auto', 'auto']} />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
                <Bar dataKey="xwOBA" name="xwOBA" fill={EMERALD} radius={[3,3,0,0]} fillOpacity={0.85} />
                <Bar dataKey="woba"  name="wOBA"  fill={BLUE}    radius={[3,3,0,0]} fillOpacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Vertical bar — Biggest Regression Candidates */}
          {(() => {
            const overperf  = [...data].filter(p => (p.xwOBADiff ?? 0) > 0.015).sort((a, b) => (b.xwOBADiff ?? 0) - (a.xwOBADiff ?? 0)).slice(0, 12).map(p => ({ ...p, label: p.name.split(' ').slice(-1)[0], _type: 'over' }));
            const underperf = [...data].filter(p => (p.xwOBADiff ?? 0) < -0.015).sort((a, b) => (a.xwOBADiff ?? 0) - (b.xwOBADiff ?? 0)).slice(0, 12).map(p => ({ ...p, label: p.name.split(' ').slice(-1)[0], _type: 'under' }));
            const allReg = [...overperf.slice(0,8).map(p => ({ name: p.label, diff: +(p.xwOBADiff ?? 0).toFixed(3), type: 'Overperforming' })), ...underperf.slice(0,8).map(p => ({ name: p.label, diff: +(p.xwOBADiff ?? 0).toFixed(3), type: 'Underperforming' }))].sort((a,b) => b.diff - a.diff);
            if (!allReg.length) return null;
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>Regression Candidates — Sorted by wOBA vs xwOBA Gap</p>
                <p className="data-note" style={{ marginBottom: 12 }}>Red = wOBA exceeds xwOBA (overperforming, expect regression). Green = underperforming expectations (buy-low).</p>
                <ResponsiveContainer width="100%" height={380}>
                  <BarChart data={allReg} layout="vertical" margin={{ top: 4, right: 60, left: 80, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={BORDER} horizontal={false} />
                    <XAxis type="number" {...AXIS_PROPS} tickFormatter={v => v > 0 ? `+${v.toFixed(3)}` : v.toFixed(3)} />
                    <YAxis type="category" dataKey="name" width={75} tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 10, fontFamily: 'Nunito', fontWeight: 600 }} axisLine={false} tickLine={false} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null;
                      const v = payload[0].value as number;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>
                        <p style={{ color: v > 0 ? BRAND_RED : EMERALD }}>wOBA - xwOBA: {v > 0 ? '+' : ''}{v.toFixed(3)}</p>
                        <p style={{ color: MUTED_FG, fontSize: '0.72rem', marginTop: 4 }}>{v > 0 ? 'Overperforming — regression risk' : 'Underperforming — buy-low'}</p>
                      </div>;
                    }} />
                    <ReferenceLine x={0} stroke={BORDER} />
                    <Bar dataKey="diff" radius={[0, 3, 3, 0]}>
                      {allReg.map((d, i) => <Cell key={i} fill={d.diff > 0 ? BRAND_RED : EMERALD} fillOpacity={0.8} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* Area chart — xwOBA distribution across all hitters */}
          {(() => {
            const buckets: Record<string, number> = {};
            data.forEach((p: any) => {
              const bucket = (Math.round((p.xwOBA ?? 0) / 0.01) * 0.01).toFixed(2);
              buckets[bucket] = (buckets[bucket] || 0) + 1;
            });
            const distData = Object.entries(buckets).map(([xwoba, count]) => ({ xwoba: +xwoba, count })).sort((a, b) => a.xwoba - b.xwoba).filter(d => d.xwoba > 0.1 && d.xwoba < 0.6);
            if (!distData.length) return null;
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>xwOBA Distribution — All Qualified Hitters</p>
                <p className="data-note" style={{ marginBottom: 12 }}>Bell curve of expected offensive quality. Players far right are elite contact hitters; far left are drag on the lineup.</p>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={distData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <defs>
                      <linearGradient id="xwobaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={EMERALD} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={EMERALD} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                    <XAxis dataKey="xwoba" {...AXIS_PROPS} tickFormatter={v => v.toFixed(2)} />
                    <YAxis {...AXIS_PROPS} />
                    <Tooltip content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        <p style={{ color: MUTED_FG }}>xwOBA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(payload[0].payload.xwoba).toFixed(2)}</strong></p>
                        <p style={{ color: MUTED_FG }}>Players: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{payload[0].value}</strong></p>
                      </div>;
                    }} />
                    <ReferenceLine x={0.32} stroke={YELLOW} strokeDasharray="4 4" strokeOpacity={0.7} label={{ value: 'Avg ~.320', position: 'top', fill: YELLOW, fontSize: 10 }} />
                    <Area type="monotone" dataKey="count" stroke={EMERALD} strokeWidth={2} fill="url(#xwobaGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* Top hitters table */}
          <div className="data-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>PLAYER</th>
                    <th>TEAM</th><th>PA</th>
                    <th>BA</th><th>xBA</th><th>xBA Δ</th>
                    <th>wOBA</th><th>xwOBA</th><th>xwOBA Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 30).map((p, i) => (
                    <tr key={p.name}>
                      <td><div className="team-cell"><span className={`rank-badge${i < 5 ? ' top5' : ''}`}>{i+1}</span><span className="team-name">{p.name}</span></div></td>
                      <td>{p.team}</td>
                      <td>{p.pa}</td>
                      <td>{p.ba.toFixed(3)}</td>
                      <td className={p.xBA > p.ba ? 'val-pos' : 'val-neg'}>{p.xBA.toFixed(3)}</td>
                      <td className={p.xBADiff > 0.010 ? 'val-neg' : p.xBADiff < -0.010 ? 'val-pos' : 'val-neutral'}>
                        {p.xBADiff > 0 ? '+' : ''}{p.xBADiff.toFixed(3)}
                      </td>
                      <td>{p.woba.toFixed(3)}</td>
                      <td className={p.xwOBA > p.woba ? 'val-pos' : 'val-neg'}>{p.xwOBA.toFixed(3)}</td>
                      <td className={p.xwOBADiff > 0.015 ? 'val-neg' : p.xwOBADiff < -0.015 ? 'val-pos' : 'val-neutral'}>
                        {p.xwOBADiff > 0 ? '+' : ''}{p.xwOBADiff.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && tab === 'pitching' && top15.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Pitching betting signals */}
          {(() => {
            const unlucky = data
              .filter(p => (p.xERADiff ?? 0) > 0.40 && (p.era ?? 0) > 0)
              .sort((a, b) => (b.xERADiff ?? 0) - (a.xERADiff ?? 0))
              .slice(0, 3)
              .map(p => ({
                label: p.name,
                why: `ERA ${(p.era??0).toFixed(2)} is ${(p.xERADiff??0).toFixed(2)} higher than expected — ERA should drop`,
                action: 'BACK this pitcher',
                color: EMERALD,
              }));
            const lucky = data
              .filter(p => (p.xERADiff ?? 0) < -0.40 && (p.era ?? 0) > 0)
              .sort((a, b) => (a.xERADiff ?? 0) - (b.xERADiff ?? 0))
              .slice(0, 3)
              .map(p => ({
                label: p.name,
                why: `ERA ${(p.era??0).toFixed(2)} is ${Math.abs(p.xERADiff??0).toFixed(2)} lower than deserved — luck will run out`,
                action: 'TARGET their hitters',
                color: BRAND_RED,
              }));
            return <BettingSignalCard title="Pitcher Luck Indicators — Back or Fade" signals={[...unlucky, ...lucky]} />;
          })()}

          {/* Scatter: ERA vs xERA — full dataset */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>ERA vs xERA — Every Qualified Pitcher</p>
            <p className="data-note" style={{ marginBottom: 8 }}>
              Dots <span style={{ color: EMERALD, fontWeight: 700 }}>below the line</span> = ERA overstates how bad they are (buy-low, ERA should drop).
              Dots <span style={{ color: BRAND_RED, fontWeight: 700 }}>above the line</span> = ERA understates badness (regression incoming, target their hitters).
              Use <strong>Zoom</strong> to drag-select any region for a closer look.
            </p>
            <EraScatter data={data} />
          </div>

          {/* Bar: top 15 side-by-side */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>xERA vs ERA — Top 15 (lowest xERA, min 30 BF)</p>
            <p className="data-note" style={{ marginBottom: 12 }}>Green bar shorter than red = pitcher outperforming expectations (regression risk). Green taller = buy-low candidate.</p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={top15} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis dataKey="name" {...AXIS_PROPS} angle={-40} textAnchor="end" interval={0} />
                <YAxis {...AXIS_PROPS} domain={[0, 'auto']} allowDataOverflow={false} />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
                <Bar dataKey="xERA" name="xERA" fill={EMERALD}    radius={[3,3,0,0]} fillOpacity={0.85} />
                <Bar dataKey="era"  name="ERA"  fill={BRAND_RED}  radius={[3,3,0,0]} fillOpacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="data-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>PITCHER</th>
                    <th>TEAM</th><th>BF</th>
                    <th>ERA</th><th>xERA</th><th>ERA Δ</th>
                    <th>wOBA vs</th><th>xwOBA vs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 30).map((p, i) => (
                    <tr key={p.name}>
                      <td><div className="team-cell"><span className={`rank-badge${i < 5 ? ' top5' : ''}`}>{i+1}</span><span className="team-name">{p.name}</span></div></td>
                      <td>{p.team}</td>
                      <td>{p.pa}</td>
                      <td>{(p.era ?? 0).toFixed(2)}</td>
                      <td className={(p.xERA ?? 0) < (p.era ?? 0) ? 'val-pos' : 'val-neg'}>{(p.xERA ?? 0).toFixed(2)}</td>
                      <td className={(p.xERADiff ?? 0) < -0.20 ? 'val-neg' : (p.xERADiff ?? 0) > 0.20 ? 'val-pos' : 'val-neutral'}>
                        {(p.xERADiff ?? 0) > 0 ? '+' : ''}{(p.xERADiff ?? 0).toFixed(2)}
                      </td>
                      <td>{(p.wobaAgainst ?? 0).toFixed(3)}</td>
                      <td className={(p.xwobaAgainst ?? 0) < (p.wobaAgainst ?? 0) ? 'val-pos' : 'val-neg'}>{(p.xwobaAgainst ?? 0).toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Vertical bar — ERA luck gap (regression candidates) */}
          {(() => {
            const lucky    = [...data].filter(p => (p.xERADiff ?? 0) < -0.3 && (p.era ?? 0) > 0).sort((a, b) => (a.xERADiff ?? 0) - (b.xERADiff ?? 0)).slice(0, 8).map(p => ({ label: p.name.split(' ').slice(-1)[0], gap: +(p.xERADiff ?? 0).toFixed(2), verdict: 'Lucky' }));
            const unlucky  = [...data].filter(p => (p.xERADiff ?? 0) > 0.3  && (p.era ?? 0) > 0).sort((a, b) => (b.xERADiff ?? 0) - (a.xERADiff ?? 0)).slice(0, 8).map(p => ({ label: p.name.split(' ').slice(-1)[0], gap: +(p.xERADiff ?? 0).toFixed(2), verdict: 'Unlucky' }));
            const regData  = [...lucky, ...unlucky].sort((a, b) => a.gap - b.gap);
            if (!regData.length) return null;
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>ERA Luck Gap — Biggest Regression Candidates</p>
                <p className="data-note" style={{ marginBottom: 12 }}>
                  <span style={{ color: BRAND_RED, fontWeight: 700 }}>Negative gap</span> (ERA &lt; xERA) = pitcher has been lucky — ERA should rise.
                  <span style={{ color: EMERALD, fontWeight: 700 }}> Positive gap</span> (ERA &gt; xERA) = unlucky — ERA should drop.
                </p>
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart data={regData} layout="vertical" margin={{ top: 4, right: 60, left: 80, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={BORDER} horizontal={false} />
                    <XAxis type="number" {...AXIS_PROPS} tickFormatter={v => v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)} />
                    <YAxis type="category" dataKey="label" width={75} tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 10, fontFamily: 'Nunito', fontWeight: 600 }} axisLine={false} tickLine={false} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null;
                      const v = payload[0].value as number;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>
                        <p style={{ color: v > 0 ? EMERALD : BRAND_RED }}>ERA - xERA: {v > 0 ? '+' : ''}{v.toFixed(2)}</p>
                        <p style={{ color: MUTED_FG, fontSize: '0.72rem', marginTop: 4 }}>{v > 0 ? 'Unlucky — ERA should drop (back this pitcher)' : 'Lucky — ERA should rise (target their hitters)'}</p>
                      </div>;
                    }} />
                    <ReferenceLine x={0} stroke={BORDER} />
                    <Bar dataKey="gap" radius={[0, 3, 3, 0]}>
                      {regData.map((d, i) => <Cell key={i} fill={d.gap > 0 ? EMERALD : BRAND_RED} fillOpacity={0.8} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* ERA distribution area chart */}
          {(() => {
            const buckets: Record<string, number> = {};
            data.forEach((p: any) => {
              if ((p.era ?? 0) > 0 && (p.era ?? 0) < 10) {
                const b = (Math.round((p.era ?? 0) / 0.25) * 0.25).toFixed(2);
                buckets[b] = (buckets[b] || 0) + 1;
              }
            });
            const distData = Object.entries(buckets).map(([era, count]) => ({ era: +era, count })).sort((a, b) => a.era - b.era);
            if (!distData.length) return null;
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>ERA Distribution — All Qualified Pitchers</p>
                <p className="data-note" style={{ marginBottom: 12 }}>ERA bell curve across the league. Pitchers left of center are elite; combine with xERA to find the ones with unsustainable numbers.</p>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={distData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <defs>
                      <linearGradient id="eraGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={BRAND_RED} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={BRAND_RED} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                    <XAxis dataKey="era" {...AXIS_PROPS} tickFormatter={v => v.toFixed(2)} label={{ value: 'ERA', position: 'insideBottom', offset: -2, fill: MUTED_FG, fontSize: 11 }} />
                    <YAxis {...AXIS_PROPS} />
                    <Tooltip content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        <p style={{ color: MUTED_FG }}>ERA: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{payload[0].payload.era.toFixed(2)}</strong></p>
                        <p style={{ color: MUTED_FG }}>Pitchers: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{payload[0].value}</strong></p>
                      </div>;
                    }} />
                    <ReferenceLine x={4.0} stroke={YELLOW} strokeDasharray="4 4" strokeOpacity={0.7} label={{ value: 'Avg ~4.00', position: 'top', fill: YELLOW, fontSize: 10 }} />
                    <Area type="monotone" dataKey="count" stroke={BRAND_RED} strokeWidth={2} fill="url(#eraGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            );
          })()}
        </div>
      )}

      {!loading && !error && tab === 'hardhit' && top15.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Quality of Contact scatter: EV avg vs Barrel% */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>Quality of Contact — Avg Exit Velo vs Barrel%</p>
            <p className="data-note" style={{ marginBottom: 8 }}>
              Top-right quadrant = elite contact (high EV + high barrel%) = overvalued hitters.
              Bottom-left = weak contact = buy-low targets in favorable matchups.
              Use <strong>Zoom</strong> to drag-select any region for a closer look.
            </p>
            <HardHitScatter data={data} />
          </div>

          {/* Composed: exit velo bars + hard hit% line overlay */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>Exit Velocity + Hard Hit% — Top 15</p>
            <p className="data-note" style={{ marginBottom: 12 }}>Bars = avg exit velo. Line = hard hit% (EV 95+ mph). Divergence = hitter skewing high on laser hits but not consistent contact.</p>
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={top15} margin={{ top: 4, right: 40, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis dataKey="name" {...AXIS_PROPS} angle={-40} textAnchor="end" interval={0} />
                <YAxis yAxisId="left"  {...AXIS_PROPS} domain={[85, 100]} unit=" mph" />
                <YAxis yAxisId="right" orientation="right" {...AXIS_PROPS} unit="%" />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
                <Bar     yAxisId="left"  dataKey="exitVeloAvg" name="Exit Velo (mph)" fill={BRAND_RED} radius={[3,3,0,0]} fillOpacity={0.8} />
                <Line   yAxisId="right" dataKey="hardHitPct"  name="Hard Hit%"       stroke={YELLOW}   strokeWidth={2} dot={{ r: 3, fill: YELLOW }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="data-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>PLAYER</th>
                    <th>TEAM</th><th>PA</th>
                    <th>EV AVG</th><th>LA AVG</th><th>SWEET%</th>
                    <th>BARREL%</th><th>HARD%</th><th>xwOBA</th>
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 30).map((p, i) => (
                    <tr key={p.name}>
                      <td><div className="team-cell"><span className={`rank-badge${i < 5 ? ' top5' : ''}`}>{i+1}</span><span className="team-name">{p.name}</span></div></td>
                      <td>{p.team}</td>
                      <td>{p.pa}</td>
                      <td className={(p.exitVeloAvg ?? 0) > 92 ? 'val-pos' : (p.exitVeloAvg ?? 0) < 88 ? 'val-neg' : 'val-neutral'}>{(p.exitVeloAvg ?? 0).toFixed(1)}</td>
                      <td>{(p.launchAngleAvg ?? 0).toFixed(1)}</td>
                      <td className={(p.sweetSpotPct ?? 0) > 35 ? 'val-pos' : (p.sweetSpotPct ?? 0) < 25 ? 'val-neg' : 'val-neutral'}>{(p.sweetSpotPct ?? 0).toFixed(1)}%</td>
                      <td className={(p.barrelPct ?? 0) > 10 ? 'val-pos' : (p.barrelPct ?? 0) < 5 ? 'val-neg' : 'val-neutral'}>{(p.barrelPct ?? 0).toFixed(1)}%</td>
                      <td className={(p.hardHitPct ?? 0) > 45 ? 'val-pos' : (p.hardHitPct ?? 0) < 35 ? 'val-neg' : 'val-neutral'}>{(p.hardHitPct ?? 0).toFixed(1)}%</td>
                      <td>{(p.xwOBA ?? 0) > 0 ? (p.xwOBA ?? 0).toFixed(3) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Stacked bar — contact quality breakdown */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>Contact Quality Breakdown — Top 15 by Exit Velo</p>
            <p className="data-note" style={{ marginBottom: 12 }}>Each bar shows the three contact-quality metrics stacked. Elite hitters stack high on all three. A hitter high in hard hit% but low in barrel% hits rockets but not in the air.</p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={top15} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis dataKey="name" {...AXIS_PROPS} angle={-40} textAnchor="end" interval={0} />
                <YAxis {...AXIS_PROPS} unit="%" />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
                <Bar dataKey="sweetSpotPct" name="Sweet Spot%"  stackId="a" fill={BLUE}      fillOpacity={0.85} />
                <Bar dataKey="hardHitPct"   name="Hard Hit%"    stackId="a" fill={YELLOW}     fillOpacity={0.85} />
                <Bar dataKey="barrelPct"    name="Barrel%"      stackId="a" fill={BRAND_RED}  fillOpacity={0.85} radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar — top 5 hitters contact profile */}
          {(() => {
            const top5 = data.slice(0, 5);
            if (!top5.length) return null;
            const maxEV  = Math.max(...data.map((p: any) => p.exitVeloAvg ?? 0));
            const maxBrl = Math.max(...data.map((p: any) => p.barrelPct ?? 0));
            const maxHH  = Math.max(...data.map((p: any) => p.hardHitPct ?? 0));
            const maxSS  = Math.max(...data.map((p: any) => p.sweetSpotPct ?? 0));
            const maxXW  = Math.max(...data.map((p: any) => p.xwOBA ?? 0));
            const radarData = [
              { stat: 'Exit Velo' }, { stat: 'Barrel%' }, { stat: 'Hard Hit%' },
              { stat: 'Sweet Spot%' }, { stat: 'xwOBA' },
            ].map((row, idx) => {
              const obj: any = { stat: row.stat };
              top5.forEach((p: any, pi: number) => {
                const vals = [
                  maxEV  ? Math.round(((p.exitVeloAvg ?? 0) / maxEV) * 100)  : 0,
                  maxBrl ? Math.round(((p.barrelPct ?? 0)    / maxBrl) * 100) : 0,
                  maxHH  ? Math.round(((p.hardHitPct ?? 0)   / maxHH)  * 100) : 0,
                  maxSS  ? Math.round(((p.sweetSpotPct ?? 0) / maxSS)  * 100) : 0,
                  maxXW  ? Math.round(((p.xwOBA ?? 0)        / maxXW)  * 100) : 0,
                ];
                obj[`p${pi}`] = vals[idx];
              });
              return obj;
            });
            const RADAR_COLORS = [BRAND_RED, EMERALD, BLUE, YELLOW, 'oklch(69% .18 290)'];
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>Contact Profile Radar — Top 5 by Exit Velo</p>
                <p className="data-note" style={{ marginBottom: 12 }}>Each axis normalized to 100 = best in dataset. Larger area = more complete contact hitter. A spike in one axis but not others = specialist.</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                  {top5.map((p: any, i: number) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
                      <div style={{ width: 10, height: 10, borderRadius: 2, background: RADAR_COLORS[i], flexShrink: 0 }} />
                      <span style={{ color: 'oklch(98.5% 0 0)', fontWeight: 600 }}>{p.name.split(' ').slice(-1)[0]}</span>
                    </div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData} margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                    <PolarGrid stroke={BORDER} />
                    <PolarAngleAxis dataKey="stat" tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }} />
                    {top5.map((_: any, i: number) => (
                      <Radar key={i} name={top5[i].name} dataKey={`p${i}`} stroke={RADAR_COLORS[i]} fill={RADAR_COLORS[i]} fillOpacity={0.12} strokeWidth={2} />
                    ))}
                    <Tooltip content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        {payload.map((p: any) => <p key={p.name} style={{ color: p.color, margin: '2px 0' }}>{top5[p.index]?.name}: <strong>{p.value}</strong>/100</p>)}
                      </div>;
                    }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

// ── Team Scoring Analytics (ESPN — NBA + NCAAB) ────────────────────────────

function TeamScoringAnalytics({ sport, divisionLabel = 'Conference' }: { sport: string; divisionLabel?: string }) {
  const [teams, setTeams]         = useState<any[]>([]);
  const [advTeams, setAdvTeams]   = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [view, setView]           = useState<'scatter' | 'diff' | 'scoring' | 'splits' | 'zscore' | 'pace'>('scatter');
  const [divFilter, setDivFilter] = useState('ALL');

  const ppgRef  = useRef<HTMLDivElement>(null);
  const paceRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoading(true); setError('');
    fetch(getApiUrl(`analytics-data/team-scoring/${sport}`))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setTeams(d.teams || []); setLoading(false); })
      .catch(() => { setError('Team scoring data unavailable'); setLoading(false); });
    if (sport === 'nba') {
      fetch(getApiUrl('analytics-data/nba/advanced'))
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d?.teams) setAdvTeams(d.teams); })
        .catch(() => {});
    }
  }, [sport]);

  const divisions = ['ALL', ...Array.from(new Set(teams.map(t => t.division).filter(Boolean))).sort()];
  const filtered  = divFilter === 'ALL' ? teams : teams.filter(t => t.division === divFilter);
  const top20diff = [...filtered].sort((a, b) => b.diff - a.diff).slice(0, 20);

  // Home vs road win%
  const splitData = filtered.map(t => {
    const parseRecord = (r: string) => {
      const [w, l] = (r || '0-0').split('-').map(Number);
      return (w + l) > 0 ? Math.round((w / (w + l)) * 100) : 0;
    };
    return { abbr: t.abbr, home: parseRecord(t.homeRecord), road: parseRecord(t.roadRecord) };
  }).sort((a, b) => (b.home + b.road) - (a.home + a.road)).slice(0, 20);

  const zoomPpg  = useScatterZoom(ppgRef,  filtered,  'ppg',  'papg');
  const zoomPace = useScatterZoom(paceRef, advTeams,  'pace', 'netRtg');

  if (loading) return <div className="skeleton" style={{ height: 340, borderRadius: 8 }} />;
  if (error)   return <div className="empty-state"><h3>Unavailable</h3><p>{error}</p></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Division filter */}
      {divisions.length > 2 && (
        <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none', flexWrap: 'wrap' }}>
          <span className="filter-label">{divisionLabel}</span>
          {divisions.map(d => (
            <button key={d} className={`filter-pill${divFilter === d ? ' active' : ''}`} onClick={() => setDivFilter(d)}>
              {d}
            </button>
          ))}
        </div>
      )}

      {/* Chart view toggle */}
      <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none' }}>
        <span className="filter-label">View</span>
        {[
          { key: 'scatter', label: 'Efficiency Quadrant'  },
          { key: 'zscore',  label: 'Z-Score Rating'       },
          { key: 'diff',    label: 'Scoring Differential' },
          { key: 'scoring', label: 'PPG vs PAPG'          },
          { key: 'splits',  label: 'Home vs Road'         },
          ...(sport === 'nba' ? [{ key: 'pace', label: 'Pace & Totals' }] : []),
        ].map(v => (
          <button key={v.key} className={`filter-pill${view === v.key ? ' active' : ''}`} onClick={() => setView(v.key as any)}>
            {v.label}
          </button>
        ))}
      </div>

      {/* Efficiency Quadrant Scatter */}
      {view === 'scatter' && (() => {
        const avgPPG  = filtered.length ? filtered.reduce((s, t) => s + (t.ppg ?? 0), 0) / filtered.length : 110;
        const avgPAPG = filtered.length ? filtered.reduce((s, t) => s + (t.papg ?? 0), 0) / filtered.length : 110;
        return (
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>Offensive vs Defensive Efficiency</p>
            <p className="data-note" style={{ marginBottom: 8 }}>
              <span style={{ color: EMERALD, fontWeight: 700 }}>Bottom-right</span> = high offense + low points allowed (elite, cover favorites).
              <span style={{ color: BRAND_RED, fontWeight: 700 }}> Top-left</span> = low offense + high allowed (dogs/under territory).
              Use <strong>Zoom</strong> to separate crowded clusters.
            </p>
            <ZoomToolbar zoom={zoomPpg} />
            <div ref={ppgRef} style={{ position: 'relative' }}>
              <ResponsiveContainer width="100%" height={500}>
                <ScatterChart margin={ZOOM_M}>
                  <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
                  <XAxis dataKey="ppg"  type="number" name="PPG"  {...AXIS_PROPS} width={YAXIS_W} domain={zoomPpg.xDomainProps} label={{ value: 'Points Scored/G', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
                  <YAxis dataKey="papg" type="number" name="PAPG" {...AXIS_PROPS} width={YAXIS_W} domain={zoomPpg.yDomainProps} label={{ value: 'Points Allowed/G', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
                  <ZAxis range={[44, 44]} />
                  <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const t = payload[0].payload;
                    return (
                      <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                        <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{t.team}</p>
                        <p style={{ color: MUTED_FG, margin: '2px 0' }}>PPG: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{t.ppg?.toFixed(1)}</strong></p>
                        <p style={{ color: MUTED_FG, margin: '2px 0' }}>PAPG: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{t.papg?.toFixed(1)}</strong></p>
                        <p style={{ color: MUTED_FG, margin: '2px 0' }}>Diff: <strong style={{ color: t.diff > 0 ? EMERALD : BRAND_RED }}>{t.diff > 0 ? '+' : ''}{t.diff?.toFixed(1)}</strong></p>
                        <p style={{ color: MUTED_FG, margin: '2px 0' }}>{t.wins}–{t.losses} • {t.streak}</p>
                      </div>
                    );
                  }} />
                  <ReferenceLine x={avgPPG}  stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Off', position: 'top', fill: MUTED_FG, fontSize: 10 }} />
                  <ReferenceLine y={avgPAPG} stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Def', position: 'right', fill: MUTED_FG, fontSize: 10 }} />
                  <Scatter data={filtered} shape={(props: any) => {
                    const { cx, cy, payload } = props;
                    const isElite = (payload.ppg ?? 0) > avgPPG && (payload.papg ?? 0) < avgPAPG;
                    const isPoor  = (payload.ppg ?? 0) < avgPPG && (payload.papg ?? 0) > avgPAPG;
                    const fill = isElite ? EMERALD : isPoor ? BRAND_RED : BLUE;
                    return (
                      <g>
                        <circle cx={cx} cy={cy} r={5} fill={fill} fillOpacity={0.8} />
                        <text x={cx + 6} y={cy - 4} fontSize={8} fill={fill} fontFamily="Nunito" fontWeight="bold">{payload.abbr}</text>
                      </g>
                    );
                  }} />
                </ScatterChart>
              </ResponsiveContainer>
              <ZoomOverlay zoom={zoomPpg} />
            </div>
          </div>
        );
      })()}

      {/* Z-Score Composite Rating */}
      {view === 'zscore' && (() => {
        const n = filtered.length;
        if (!n) return null;
        const avgPPG  = filtered.reduce((s: number, t: any) => s + (t.ppg  ?? 0), 0) / n;
        const avgPAPG = filtered.reduce((s: number, t: any) => s + (t.papg ?? 0), 0) / n;
        const stdPPG  = Math.sqrt(filtered.reduce((s: number, t: any) => s + Math.pow((t.ppg  ?? 0) - avgPPG, 2), 0) / n) || 1;
        const stdPAPG = Math.sqrt(filtered.reduce((s: number, t: any) => s + Math.pow((t.papg ?? 0) - avgPAPG, 2), 0) / n) || 1;
        const zData = filtered.map((t: any) => {
          const zOff = ((t.ppg  ?? 0) - avgPPG)  / stdPPG;
          const zDef = (avgPAPG - (t.papg ?? 0)) / stdPAPG;  // inverted: lower allowed = better
          const zNet = +((zOff + zDef) / 2).toFixed(2);
          return { abbr: t.abbr, zOff: +zOff.toFixed(2), zDef: +zDef.toFixed(2), zNet };
        }).sort((a: any, b: any) => b.zNet - a.zNet);
        return (
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>Composite Z-Score Rating — All Teams</p>
            <p className="data-note" style={{ marginBottom: 12 }}>Z-score = standard deviations above/below the league mean. zNet combines offensive (PPG) and defensive (PAPG) efficiency. &gt;+1.0 = elite tier. &lt;-1.0 = bottom tier. Strong signal for point spread and totals.</p>
            <ResponsiveContainer width="100%" height={Math.max(320, zData.length * 20)}>
              <BarChart data={zData} layout="vertical" margin={{ top: 4, right: 60, left: 32, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} horizontal={false} />
                <YAxis dataKey="abbr" type="category" width={36} {...AXIS_PROPS} />
                <XAxis type="number" domain={['auto', 'auto']} {...AXIS_PROPS} />
                <Tooltip content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0]?.payload;
                  return (
                    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                      <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>
                      <p style={{ color: EMERALD,    margin: '2px 0' }}>zOff (PPG): <strong>{d?.zOff}</strong></p>
                      <p style={{ color: BRAND_RED,  margin: '2px 0' }}>zDef (PAPG): <strong>{d?.zDef}</strong></p>
                      <p style={{ color: YELLOW,     margin: '2px 0', marginTop: 4 }}>Net Z: <strong>{d?.zNet}</strong></p>
                    </div>
                  );
                }} />
                <ReferenceLine x={0} stroke={BORDER} strokeWidth={1.5} />
                <ReferenceLine x={1}  stroke={EMERALD}   strokeDasharray="4 4" strokeOpacity={0.4} label={{ value: '+1σ', position: 'top', fill: EMERALD,   fontSize: 9 }} />
                <ReferenceLine x={-1} stroke={BRAND_RED} strokeDasharray="4 4" strokeOpacity={0.4} label={{ value: '-1σ', position: 'top', fill: BRAND_RED, fontSize: 9 }} />
                <Bar dataKey="zNet" name="Z-Score" radius={[0,3,3,0]}>
                  {zData.map((t: any, i: number) => (
                    <Cell key={i} fill={t.zNet >= 1 ? EMERALD : t.zNet <= -1 ? BRAND_RED : t.zNet > 0 ? BLUE : YELLOW} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })()}

      {/* Scoring Differential */}
      {view === 'diff' && (
        <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
          <p className="section-title" style={{ marginBottom: 4 }}>Points Differential Per Game — Sorted Best to Worst</p>
          <p className="data-note" style={{ marginBottom: 12 }}>Green = positive diff (covering favorite territory). Red = negative (underdog territory). Strong proxy for point spread efficiency.</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={top20diff} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
              <XAxis dataKey="abbr" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} />
              <YAxis {...AXIS_PROPS} domain={['auto', 'auto']} unit="" />
              <Tooltip content={<DarkTooltip />} />
              <ReferenceLine y={0} stroke={BORDER} strokeDasharray="4 4" />
              <Bar dataKey="diff" name="Pts Diff/G" radius={[3,3,0,0]}>
                {top20diff.map((t, i) => (
                  <Cell key={t.abbr} fill={t.diff >= 0 ? EMERALD : BRAND_RED} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* PPG vs PAPG */}
      {view === 'scoring' && (
        <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
          <p className="section-title" style={{ marginBottom: 4 }}>Points Scored vs Points Allowed Per Game</p>
          <p className="data-note" style={{ marginBottom: 12 }}>Teams where the green bar clearly exceeds red are consistent covers. High-scoring teams in both bars signal over value.</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={[...filtered].sort((a, b) => b.ppg - a.ppg).slice(0, 20)}
              margin={{ top: 4, right: 16, left: 0, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
              <XAxis dataKey="abbr" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} />
              <YAxis {...AXIS_PROPS} domain={['auto', 'auto']} />
              <Tooltip content={<DarkTooltip />} />
              <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
              <Bar dataKey="ppg"  name="Pts Scored/G"  fill={EMERALD}   radius={[3,3,0,0]} fillOpacity={0.85} />
              <Bar dataKey="papg" name="Pts Allowed/G" fill={BRAND_RED} radius={[3,3,0,0]} fillOpacity={0.6} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Home vs Road */}
      {view === 'splits' && (
        <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
          <p className="section-title" style={{ marginBottom: 4 }}>Home vs Road Win% — Top 20 by Combined Win Rate</p>
          <p className="data-note" style={{ marginBottom: 12 }}>Large gap between home (blue) and road (red) = strong home-field advantage to fade on the road.</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={splitData} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
              <XAxis dataKey="abbr" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} />
              <YAxis {...AXIS_PROPS} domain={[0, 100]} unit="%" />
              <Tooltip content={<DarkTooltip />} />
              <Legend wrapperStyle={{ color: MUTED_FG, fontSize: '0.75rem', paddingTop: 8 }} />
              <Bar dataKey="home" name="Home Win%"  fill={BLUE}      radius={[3,3,0,0]} fillOpacity={0.85} />
              <Bar dataKey="road" name="Road Win%"  fill={BRAND_RED} radius={[3,3,0,0]} fillOpacity={0.65} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* NBA Pace & Totals view */}
      {view === 'pace' && sport === 'nba' && (
        advTeams.length === 0
          ? <div className="empty-state"><p>Loading NBA advanced data...</p></div>
          : <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Betting signals from pace data */}
            {(() => {
              const avgPace = advTeams.reduce((s, t) => s + (t.pace ?? 0), 0) / advTeams.length;
              const avgNet  = advTeams.reduce((s, t) => s + (t.netRtg ?? 0), 0) / advTeams.length;
              const overTeams = advTeams
                .filter(t => (t.pace ?? 0) > avgPace + 1 && (t.netRtg ?? 0) > avgNet)
                .sort((a, b) => (b.pace ?? 0) - (a.pace ?? 0))
                .slice(0, 3)
                .map(t => ({
                  label: t.abbr,
                  why: `Pace ${(t.pace??0).toFixed(1)} + NetRtg ${(t.netRtg??0) > 0 ? '+' : ''}${(t.netRtg??0).toFixed(1)} — fast, good team`,
                  action: 'LEAN OVER in their games',
                  color: EMERALD,
                }));
              const underTeams = advTeams
                .filter(t => (t.pace ?? 0) < avgPace - 1 && (t.netRtg ?? 0) < avgNet)
                .sort((a, b) => (a.pace ?? 0) - (b.pace ?? 0))
                .slice(0, 3)
                .map(t => ({
                  label: t.abbr,
                  why: `Pace ${(t.pace??0).toFixed(1)} + NetRtg ${(t.netRtg??0) > 0 ? '+' : ''}${(t.netRtg??0).toFixed(1)} — slow, weak team`,
                  action: 'LEAN UNDER in their games',
                  color: BLUE,
                }));
              return <BettingSignalCard title="Totals Signals — Pace + Team Quality" signals={[...overTeams, ...underTeams]} />;
            })()}

            {/* Pace vs NetRtg scatter */}
            {(() => {
              const avgPace = advTeams.reduce((s, t) => s + (t.pace??0), 0) / advTeams.length;
              const avgNet  = advTeams.reduce((s, t) => s + (t.netRtg??0), 0) / advTeams.length;
              return (
                <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                  <p className="section-title" style={{ marginBottom: 4 }}>Pace vs Net Rating — All NBA Teams</p>
                  <p className="data-note" style={{ marginBottom: 8 }}>
                    <span style={{ color: EMERALD, fontWeight: 700 }}>Top-right</span> = fast pace + positive net rating — games go OVER more often.
                    <span style={{ color: BLUE, fontWeight: 700 }}> Bottom-left</span> = slow + bad team — grind-it-out games, lean UNDER.
                    Use <strong>Zoom</strong> to isolate clusters.
                  </p>
                  <ZoomToolbar zoom={zoomPace} />
                  <div ref={paceRef} style={{ position: 'relative' }}>
                    <ResponsiveContainer width="100%" height={460}>
                      <ScatterChart margin={ZOOM_M}>
                        <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
                        <XAxis dataKey="pace"   type="number" name="Pace"   {...AXIS_PROPS} width={YAXIS_W} domain={zoomPace.xDomainProps} label={{ value: 'Pace (possessions/48 min)', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
                        <YAxis dataKey="netRtg" type="number" name="NetRtg" {...AXIS_PROPS} width={YAXIS_W} domain={zoomPace.yDomainProps} label={{ value: 'Net Rating', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
                        <ZAxis range={[44, 44]} />
                        <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
                          if (!active || !payload?.length) return null;
                          const t = payload[0].payload;
                          return (
                            <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                              <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{t.abbr}</p>
                              <p style={{ color: MUTED_FG, margin: '2px 0' }}>Pace: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{(t.pace??0).toFixed(1)}</strong></p>
                              <p style={{ color: MUTED_FG, margin: '2px 0' }}>OffRtg: <strong style={{ color: EMERALD }}>{(t.offRtg??0).toFixed(1)}</strong></p>
                              <p style={{ color: MUTED_FG, margin: '2px 0' }}>DefRtg: <strong style={{ color: BRAND_RED }}>{(t.defRtg??0).toFixed(1)}</strong></p>
                              <p style={{ color: MUTED_FG, margin: '2px 0' }}>NetRtg: <strong style={{ color: (t.netRtg??0) > 0 ? EMERALD : BRAND_RED }}>{(t.netRtg??0) > 0 ? '+' : ''}{(t.netRtg??0).toFixed(1)}</strong></p>
                              <p style={{ color: MUTED_FG, margin: '2px 0' }}>TS%: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{((t.tsPct??0)*100).toFixed(1)}%</strong></p>
                            </div>
                          );
                        }} />
                        <ReferenceLine x={avgPace} stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Pace', position: 'top', fill: MUTED_FG, fontSize: 10 }} />
                        <ReferenceLine y={avgNet}  stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Net', position: 'right', fill: MUTED_FG, fontSize: 10 }} />
                        <Scatter data={advTeams} shape={(props: any) => {
                          const { cx, cy, payload } = props;
                          const fastGood = (payload.pace??0) > avgPace && (payload.netRtg??0) > avgNet;
                          const slowBad  = (payload.pace??0) < avgPace && (payload.netRtg??0) < avgNet;
                          const fill = fastGood ? EMERALD : slowBad ? BLUE : YELLOW;
                          return (
                            <g>
                              <circle cx={cx} cy={cy} r={5} fill={fill} fillOpacity={0.85} />
                              <text x={cx + 6} y={cy - 4} fontSize={9} fill={fill} fontFamily="Nunito" fontWeight="bold">{payload.abbr}</text>
                            </g>
                          );
                        }} />
                      </ScatterChart>
                    </ResponsiveContainer>
                    <ZoomOverlay zoom={zoomPace} />
                  </div>
                </div>
              );
            })()}

            {/* Pace ranked bar */}
            <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
              <p className="section-title" style={{ marginBottom: 4 }}>Pace Ranking — Fastest to Slowest</p>
              <p className="data-note" style={{ marginBottom: 12 }}>Higher pace = more possessions = more points = OVER value. Especially strong signal when two fast teams play each other.</p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[...advTeams].sort((a,b) => (b.pace??0)-(a.pace??0))} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                  <XAxis dataKey="abbr" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} />
                  <YAxis {...AXIS_PROPS} domain={['auto','auto']} />
                  <Tooltip content={<DarkTooltip />} />
                  <ReferenceLine y={advTeams.reduce((s,t)=>s+(t.pace??0),0)/advTeams.length} stroke={YELLOW} strokeDasharray="4 4" label={{ value: 'Avg', position: 'right', fill: YELLOW, fontSize: 10 }} />
                  <Bar dataKey="pace" name="Pace" radius={[3,3,0,0]}>
                    {[...advTeams].sort((a,b)=>(b.pace??0)-(a.pace??0)).map((t,i) => (
                      <Cell key={i} fill={i < 8 ? EMERALD : i > advTeams.length - 9 ? BLUE : MUTED_FG} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* NetRtg ranked bar */}
            <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
              <p className="section-title" style={{ marginBottom: 4 }}>Net Rating — Best to Worst Teams</p>
              <p className="data-note" style={{ marginBottom: 12 }}>Net Rating = points scored minus points allowed per 100 possessions. This is the most predictive measure of team quality for spread betting. Positive = cover favorites.</p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[...advTeams].sort((a,b) => (b.netRtg??0)-(a.netRtg??0))} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                  <XAxis dataKey="abbr" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} />
                  <YAxis {...AXIS_PROPS} domain={['auto','auto']} />
                  <Tooltip content={<DarkTooltip />} />
                  <ReferenceLine y={0} stroke={BORDER} strokeDasharray="4 4" />
                  <Bar dataKey="netRtg" name="Net Rtg" radius={[3,3,0,0]}>
                    {[...advTeams].sort((a,b)=>(b.netRtg??0)-(a.netRtg??0)).map((t,i) => (
                      <Cell key={i} fill={(t.netRtg??0) >= 0 ? EMERALD : BRAND_RED} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

          </div>
      )}

      {/* Full table */}
      <div className="data-table-wrap">
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 36 }}>#</th>
                <th style={{ textAlign: 'left' }}>TEAM</th>
                <th>{divisionLabel.toUpperCase()}</th>
                <th>W</th><th>L</th><th>PCT</th>
                <th>PPG</th><th>PAPG</th>
                <th>DIFF</th>
                <th>HOME</th><th>ROAD</th>
                <th>CONF</th><th>L10</th><th>STK</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, i) => (
                <tr key={t.abbr + i}>
                  <td><span className={`rank-badge${i < 5 ? ' top5' : ''}`}>{i+1}</span></td>
                  <td>
                    <div className="team-cell">
                      {t.logo && <img src={t.logo} alt={t.abbr} style={{ width: 18, height: 18, objectFit: 'contain', flexShrink: 0 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />}
                      <span className="team-abbr">{t.abbr}</span>
                      <span className="team-name" style={{ fontSize: '0.78rem' }}>{t.team}</span>
                    </div>
                  </td>
                  <td style={{ fontSize: '0.71rem', maxWidth: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.division}</td>
                  <td>{t.wins}</td>
                  <td>{t.losses}</td>
                  <td>{(t.pct * 100).toFixed(1)}%</td>
                  <td className={t.ppg > 115 ? 'val-pos' : t.ppg < 105 ? 'val-neg' : 'val-neutral'}>{t.ppg?.toFixed(1)}</td>
                  <td className={t.papg < 105 ? 'val-pos' : t.papg > 115 ? 'val-neg' : 'val-neutral'}>{t.papg?.toFixed(1)}</td>
                  <td className={t.diff > 3 ? 'val-pos' : t.diff < -3 ? 'val-neg' : 'val-neutral'}>{t.diff > 0 ? '+' : ''}{t.diff?.toFixed(1)}</td>
                  <td style={{ fontSize: '0.73rem' }}>{t.homeRecord}</td>
                  <td style={{ fontSize: '0.73rem' }}>{t.roadRecord}</td>
                  <td style={{ fontSize: '0.73rem' }}>{t.confRecord}</td>
                  <td style={{ fontSize: '0.73rem' }}>{t.last10}</td>
                  <td style={{ fontSize: '0.73rem', color: t.streak?.startsWith('W') ? EMERALD : BRAND_RED }}>{t.streak}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── NCAAB T-Rank (BartTorvik) ──────────────────────────────────────────────

function NCAABTRank() {
  const [teams, setTeams]     = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const [confFilter, setConfFilter] = useState('ALL');
  const [view, setView]       = useState<'eff' | 'tempo' | 'table'>('eff');

  useEffect(() => {
    fetch(getApiUrl('analytics-data/ncaab/trank'))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setTeams(d.teams || []); setLoading(false); })
      .catch(() => { setError('BartTorvik unavailable (off-season or network)'); setLoading(false); });
  }, []);

  const confs    = ['ALL', ...Array.from(new Set(teams.map(t => t.conf).filter(Boolean))).sort()];
  const filtered = useMemo(
    () => (confFilter === 'ALL' ? teams : teams.filter(t => t.conf === confFilter)).slice(0, 100),
    [confFilter, teams],
  );

  const effRef = useRef<HTMLDivElement>(null);
  const zoomEff = useScatterZoom(effRef, filtered, 'adjOE', 'adjDE');

  if (loading) return <div className="skeleton" style={{ height: 340, borderRadius: 8 }} />;
  if (error)   return <div className="empty-state"><h3>Unavailable</h3><p>{error}</p></div>;

  const avgOE    = filtered.reduce((s,t) => s + (t.adjOE??0), 0) / filtered.length;
  const avgDE    = filtered.reduce((s,t) => s + (t.adjDE??0), 0) / filtered.length;
  const avgTempo = filtered.reduce((s,t) => s + (t.adjTempo??0), 0) / filtered.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Conference filter */}
      {confs.length > 2 && (
        <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none', flexWrap: 'wrap' }}>
          <span className="filter-label">Conference</span>
          {confs.slice(0, 15).map(c => (
            <button key={c} className={`filter-pill${confFilter === c ? ' active' : ''}`} onClick={() => setConfFilter(c)}>{c}</button>
          ))}
        </div>
      )}

      {/* View toggle */}
      <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none' }}>
        <span className="filter-label">View</span>
        {[{ key: 'eff', label: 'Efficiency Quadrant' }, { key: 'tempo', label: 'Tempo / Totals' }, { key: 'table', label: 'Full T-Rank Table' }].map(v => (
          <button key={v.key} className={`filter-pill${view === v.key ? ' active' : ''}`} onClick={() => setView(v.key as any)}>{v.label}</button>
        ))}
      </div>

      {/* Betting signals */}
      {(() => {
        const fastElite = filtered
          .filter(t => (t.adjTempo??0) > avgTempo + 1 && (t.barthag??0) > 0.7)
          .sort((a,b) => (b.barthag??0)-(a.barthag??0)).slice(0, 3)
          .map(t => ({ label: t.team, why: `Tempo ${(t.adjTempo??0).toFixed(1)}, Barthag ${(t.barthag??0).toFixed(3)}`, action: 'LEAN OVER', color: EMERALD }));
        const slowWeak = filtered
          .filter(t => (t.adjTempo??0) < avgTempo - 1 && (t.barthag??0) < 0.3)
          .sort((a,b) => (a.barthag??0)-(b.barthag??0)).slice(0, 2)
          .map(t => ({ label: t.team, why: `Tempo ${(t.adjTempo??0).toFixed(1)}, Barthag ${(t.barthag??0).toFixed(3)}`, action: 'LEAN UNDER', color: BLUE }));
        return <BettingSignalCard title="NCAAB Totals Signals — Tempo + Team Quality" signals={[...fastElite, ...slowWeak]} />;
      })()}

      {/* Efficiency quadrant */}
      {view === 'eff' && (
        <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
          <p className="section-title" style={{ marginBottom: 4 }}>Adjusted Offensive vs Defensive Efficiency</p>
          <p className="data-note" style={{ marginBottom: 8 }}>
            <span style={{ color: EMERALD, fontWeight: 700 }}>Top-right</span> = high offense + stingy defense (elite ATS favorites).
            <span style={{ color: BRAND_RED, fontWeight: 700 }}> Bottom-left</span> = weak offense + porous defense (avoid — unpredictable).
            Hover for team name. Use <strong>Zoom</strong> to separate the mid-major cluster.
          </p>
          <ZoomToolbar zoom={zoomEff} />
          <div ref={effRef} style={{ position: 'relative' }}>
            <ResponsiveContainer width="100%" height={520}>
              <ScatterChart margin={ZOOM_M}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
                <XAxis dataKey="adjOE" type="number" name="AdjOE" {...AXIS_PROPS} width={YAXIS_W} domain={zoomEff.xDomainProps} label={{ value: 'Adj. Off. Efficiency', position: 'insideBottom', offset: -14, fill: MUTED_FG, fontSize: 11 }} />
                <YAxis dataKey="adjDE" type="number" name="AdjDE" {...AXIS_PROPS} width={YAXIS_W} domain={zoomEff.yDomainProps} label={{ value: 'Adj. Def. Efficiency (lower = better)', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
                <ZAxis range={[38, 38]} />
                <Tooltip cursor={{ strokeDasharray: '3 3', stroke: BORDER }} content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const t = payload[0].payload;
                  return (
                    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
                      <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>#{t.rank} {t.team}</p>
                      <p style={{ color: MUTED_FG, margin: '2px 0' }}>Conf: <strong style={{ color: 'oklch(98.5% 0 0)' }}>{t.conf}</strong></p>
                      <p style={{ color: MUTED_FG, margin: '2px 0' }}>AdjOE: <strong style={{ color: EMERALD }}>{(t.adjOE??0).toFixed(1)}</strong></p>
                      <p style={{ color: MUTED_FG, margin: '2px 0' }}>AdjDE: <strong style={{ color: BRAND_RED }}>{(t.adjDE??0).toFixed(1)}</strong></p>
                      <p style={{ color: MUTED_FG, margin: '2px 0' }}>Tempo: <strong>{(t.adjTempo??0).toFixed(1)}</strong></p>
                      <p style={{ color: MUTED_FG, margin: '2px 0' }}>Barthag: <strong style={{ color: (t.barthag??0) > 0.7 ? EMERALD : BRAND_RED }}>{(t.barthag??0).toFixed(3)}</strong></p>
                    </div>
                  );
                }} />
                <ReferenceLine x={avgOE} stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Off', position: 'top', fill: MUTED_FG, fontSize: 10 }} />
                <ReferenceLine y={avgDE} stroke={MUTED_FG} strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: 'Avg Def', position: 'right', fill: MUTED_FG, fontSize: 10 }} />
                <Scatter data={filtered} shape={(props: any) => {
                  const { cx, cy, payload } = props;
                  const elite = (payload.adjOE??0) > avgOE && (payload.adjDE??0) < avgDE;
                  const poor  = (payload.adjOE??0) < avgOE && (payload.adjDE??0) > avgDE;
                  const fill  = elite ? EMERALD : poor ? BRAND_RED : BLUE;
                  const isTop = (payload.rank??999) <= 25;
                  return (
                    <g>
                      <circle cx={cx} cy={cy} r={isTop ? 6 : 4} fill={fill} fillOpacity={isTop ? 0.9 : 0.65} />
                      {isTop && <text x={cx + 6} y={cy - 4} fontSize={8} fill={fill} fontFamily="Nunito" fontWeight="bold">{payload.team?.split(' ').pop()}</text>}
                    </g>
                  );
                }} />
              </ScatterChart>
            </ResponsiveContainer>
            <ZoomOverlay zoom={zoomEff} />
          </div>
        </div>
      )}

      {/* Tempo / totals chart */}
      {view === 'tempo' && (
        <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
          <p className="section-title" style={{ marginBottom: 4 }}>Adjusted Tempo — Fastest 40 Teams</p>
          <p className="data-note" style={{ marginBottom: 12 }}>Higher tempo = more possessions per game = more scoring = OVER value. When two top-tempo teams play, the total is almost always underpriced.</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={[...filtered].sort((a,b) => (b.adjTempo??0)-(a.adjTempo??0)).slice(0,40)} margin={{ top: 4, right: 16, left: 0, bottom: 70 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
              <XAxis dataKey="team" {...AXIS_PROPS} angle={-45} textAnchor="end" interval={0} tick={{ fill: MUTED_FG, fontSize: 9, fontFamily: 'Nunito' }} />
              <YAxis {...AXIS_PROPS} domain={['auto','auto']} />
              <Tooltip content={<DarkTooltip />} />
              <ReferenceLine y={avgTempo} stroke={YELLOW} strokeDasharray="4 4" label={{ value: 'Avg Tempo', position: 'right', fill: YELLOW, fontSize: 10 }} />
              <Bar dataKey="adjTempo" name="Adj Tempo" radius={[3,3,0,0]}>
                {[...filtered].sort((a,b)=>(b.adjTempo??0)-(a.adjTempo??0)).slice(0,40).map((t,i) => (
                  <Cell key={i} fill={i < 10 ? EMERALD : i < 20 ? BLUE : MUTED_FG} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Full T-Rank table */}
      {view === 'table' && (
        <div className="data-table-wrap">
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>RANK</th>
                  <th style={{ textAlign: 'left' }}>TEAM</th>
                  <th>CONF</th>
                  <th>RECORD</th>
                  <th>ADJ OE</th>
                  <th>ADJ DE</th>
                  <th>TEMPO</th>
                  <th>BARTHAG</th>
                  <th>eFG%</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 60).map(t => (
                  <tr key={t.rank}>
                    <td><span className={`rank-badge${(t.rank??99) <= 5 ? ' top5' : ''}`}>{t.rank}</span></td>
                    <td><span className="team-name">{t.team}</span></td>
                    <td style={{ fontSize: '0.72rem' }}>{t.conf}</td>
                    <td style={{ fontSize: '0.72rem' }}>{t.record}</td>
                    <td className={(t.adjOE??0) > avgOE ? 'val-pos' : 'val-neg'}>{(t.adjOE??0).toFixed(1)}</td>
                    <td className={(t.adjDE??0) < avgDE ? 'val-pos' : 'val-neg'}>{(t.adjDE??0).toFixed(1)}</td>
                    <td className={(t.adjTempo??0) > avgTempo ? 'val-pos' : 'val-neutral'}>{(t.adjTempo??0).toFixed(1)}</td>
                    <td className={(t.barthag??0) > 0.7 ? 'val-pos' : (t.barthag??0) < 0.3 ? 'val-neg' : 'val-neutral'}>{(t.barthag??0).toFixed(3)}</td>
                    <td>{((t.efgPct??0)*100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

type AdvancedSport = 'mlb' | 'nba' | 'ncaab';

const SOURCES: { key: AdvancedSport; label: string; sub: string }[] = [
  { key: 'mlb',   label: 'MLB',   sub: 'Expected stats, efficiency ratings, and model-driven metrics' },
  { key: 'nba',   label: 'NBA',   sub: 'Scoring analytics, pace, and efficiency ratings' },
  { key: 'ncaab', label: 'NCAAB', sub: 'Team rankings, efficiency ratings, and scoring breakdown' },
];

export function AdvancedMetrics() {
  const [sport, setSport] = useState<AdvancedSport>('mlb');
  const source = SOURCES.find(s => s.key === sport)!;

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Advanced Metrics</h1>
        <p className="subtitle">{source.sub} — expected stats, efficiency ratings, and model-driven metrics</p>
        <div className="sport-tabs">
          {SOURCES.map(s => (
            <button
              key={s.key}
              className={`sport-tab${sport === s.key ? ' active' : ''}`}
              onClick={() => setSport(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="analytics-content">
        {sport === 'mlb'   && <MLBStatcast />}
        {sport === 'nba'   && <TeamScoringAnalytics sport="nba"   divisionLabel="Conference" />}
        {sport === 'ncaab' && (
          <>
            <NCAABTRank />
            <div style={{ marginTop: 32 }}>
              <p className="section-title" style={{ marginBottom: 16 }}>Conference Scoring Breakdown</p>
              <TeamScoringAnalytics sport="ncaab" divisionLabel="Conference" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
