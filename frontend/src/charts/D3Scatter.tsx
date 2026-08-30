/**
 * D3Scatter — Custom SVG scatter plot with Voronoi hover + d3-zoom.
 * Scroll to zoom, drag to pan, +/- reset buttons. No chart library.
 */
import { useRef, useState, useEffect, useMemo, useCallback } from 'react';
import { scaleLinear } from 'd3-scale';
import { Delaunay } from 'd3-delaunay';
import { zoom as d3zoom, zoomIdentity, ZoomTransform } from 'd3-zoom';
import { select } from 'd3-selection';

const MARGIN = { top: 20, right: 40, bottom: 52, left: 64 };

interface Props<T> {
  data:      T[];
  x:         (d: T) => number;
  y:         (d: T) => number;
  color:     (d: T) => string;
  radius?:   (d: T) => number;
  label?:    (d: T) => string | null;
  tooltip:   (d: T) => React.ReactNode;
  xLabel?:   string;
  yLabel?:   string;
  xFormat?:  (v: number) => string;
  yFormat?:  (v: number) => string;
  refLine?:  [[number, number], [number, number]];
  height?:   number;
}

const BTN: React.CSSProperties = {
  fontSize: '0.7rem', fontWeight: 700, padding: '3px 10px',
  borderRadius: 4, border: 'none', cursor: 'pointer',
  background: 'rgba(255,255,255,0.08)', color: '#9ca3af',
};

export function D3Scatter<T>({
  data, x, y, color, radius, label, tooltip,
  xLabel, yLabel, xFormat, yFormat, refLine, height = 520,
}: Props<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef       = useRef<SVGSVGElement>(null);
  const zoomRef      = useRef<ReturnType<typeof d3zoom> | null>(null);

  const [width,     setWidth]     = useState(700);
  const [transform, setTransform] = useState<ZoomTransform>(zoomIdentity);
  const [hovered,   setHovered]   = useState<T | null>(null);
  const [tipPos,    setTipPos]    = useState({ x: 0, y: 0 });
  const [dragging,  setDragging]  = useState(false);
  const [entered,   setEntered]   = useState(false);

  // Responsive width
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(e => setWidth(e[0].contentRect.width));
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Animate entrance
  useEffect(() => {
    setEntered(false);
    const t = setTimeout(() => setEntered(true), 40);
    return () => clearTimeout(t);
  }, [data]);

  const iW = width  - MARGIN.left - MARGIN.right;
  const iH = height - MARGIN.top  - MARGIN.bottom;

  // Base scales (full-data extent)
  const baseXs = useMemo(() => {
    const vals = data.map(x);
    const [lo, hi] = [Math.min(...vals), Math.max(...vals)];
    const pad = (hi - lo) * 0.06;
    return scaleLinear().domain([lo - pad, hi + pad]).range([0, iW]).nice();
  }, [data, x, iW]);

  const baseYs = useMemo(() => {
    const vals = data.map(y);
    const [lo, hi] = [Math.min(...vals), Math.max(...vals)];
    const pad = (hi - lo) * 0.06;
    return scaleLinear().domain([lo - pad, hi + pad]).range([iH, 0]).nice();
  }, [data, y, iH]);

  // Zoomed scales derived from d3 transform
  const xs = useMemo(() => transform.rescaleX(baseXs), [transform, baseXs]);
  const ys = useMemo(() => transform.rescaleY(baseYs), [transform, baseYs]);

  // Wire d3-zoom onto the SVG
  useEffect(() => {
    if (!svgRef.current) return;
    const z = d3zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 12])
      .translateExtent([[-iW * 0.5, -iH * 0.5], [iW * 1.5, iH * 1.5]])
      .filter(e => {
        // Allow wheel always; allow drag only on non-pointer events or when not hovering
        if (e.type === 'wheel') return true;
        return !e.button; // left-button drag
      })
      .on('start', () => { setDragging(true); setHovered(null); })
      .on('zoom',  ({ transform: t }) => setTransform(t))
      .on('end',   () => setDragging(false));

    zoomRef.current = z;
    select(svgRef.current).call(z as any);

    return () => { select(svgRef.current!).on('.zoom', null); };
  }, [iW, iH]);

  // Voronoi for nearest-point hover
  const delaunay = useMemo(
    () => Delaunay.from(data, d => xs(x(d)), d => ys(y(d))),
    [data, xs, ys, x, y],
  );

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGRectElement>) => {
    if (dragging) return;
    const rect = e.currentTarget.closest('svg')!.getBoundingClientRect();
    const mx = e.clientX - rect.left - MARGIN.left;
    const my = e.clientY - rect.top  - MARGIN.top;
    const idx = delaunay.find(mx, my);
    if (idx >= 0 && idx < data.length) {
      setHovered(data[idx]);
      setTipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    }
  }, [delaunay, data, dragging]);

  // Zoom controls
  const zoomIn  = () => select(svgRef.current!).transition().duration(250).call((zoomRef.current as any).scaleBy, 1.6);
  const zoomOut = () => select(svgRef.current!).transition().duration(250).call((zoomRef.current as any).scaleBy, 1 / 1.6);
  const reset   = () => select(svgRef.current!).transition().duration(350).call((zoomRef.current as any).transform, zoomIdentity);

  const xTicks = xs.ticks(6);
  const yTicks = ys.ticks(6);
  const xFmt   = xFormat ?? ((v: number) => v.toFixed(3));
  const yFmt   = yFormat ?? ((v: number) => v.toFixed(3));
  const isZoomed = transform.k > 1.01;

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {/* Zoom controls */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 5, marginBottom: 6 }}>
        <button onClick={zoomIn}  style={BTN} title="Zoom in">+</button>
        <button onClick={zoomOut} style={BTN} title="Zoom out">−</button>
        {isZoomed && (
          <button onClick={reset} style={{ ...BTN, color: 'oklch(62.3% .214 259.815)' }} title="Reset zoom">
            RESET
          </button>
        )}
        <span style={{ fontSize: '0.65rem', color: '#6b7280', alignSelf: 'center', marginLeft: 4 }}>
          scroll or drag to zoom/pan
        </span>
      </div>

      <svg ref={svgRef} width={width} height={height}
        style={{ display: 'block', overflow: 'hidden', cursor: dragging ? 'grabbing' : 'crosshair' }}>
        <defs>
          <clipPath id="sc-clip">
            <rect x={0} y={0} width={iW} height={iH} />
          </clipPath>
        </defs>

        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>

          {/* Grid */}
          {xTicks.map(t => (
            <line key={`xg-${t}`} x1={xs(t)} y1={0} x2={xs(t)} y2={iH}
              stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />
          ))}
          {yTicks.map(t => (
            <line key={`yg-${t}`} x1={0} y1={ys(t)} x2={iW} y2={ys(t)}
              stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />
          ))}

          {/* X axis */}
          <line x1={0} y1={iH} x2={iW} y2={iH} stroke="rgba(255,255,255,0.08)" />
          {xTicks.map(t => (
            <g key={`xt-${t}`} transform={`translate(${xs(t)},${iH})`}>
              <line y2={4} stroke="rgba(255,255,255,0.08)" />
              <text y={16} textAnchor="middle" fill="#9ca3af" fontSize={10} fontFamily="monospace">
                {xFmt(t)}
              </text>
            </g>
          ))}
          {xLabel && (
            <text x={iW / 2} y={iH + 44} textAnchor="middle" fill="#9ca3af" fontSize={11}>
              {xLabel}
            </text>
          )}

          {/* Y axis */}
          <line x1={0} y1={0} x2={0} y2={iH} stroke="rgba(255,255,255,0.08)" />
          {yTicks.map(t => (
            <g key={`yt-${t}`} transform={`translate(0,${ys(t)})`}>
              <line x2={-4} stroke="rgba(255,255,255,0.08)" />
              <text x={-8} textAnchor="end" dominantBaseline="central" fill="#9ca3af" fontSize={10} fontFamily="monospace">
                {yFmt(t)}
              </text>
            </g>
          ))}
          {yLabel && (
            <text transform={`translate(${-52},${iH / 2}) rotate(-90)`}
              textAnchor="middle" fill="#9ca3af" fontSize={11}>
              {yLabel}
            </text>
          )}

          {/* Reference diagonal line */}
          {refLine && (
            <line
              x1={xs(refLine[0][0])} y1={ys(refLine[0][1])}
              x2={xs(refLine[1][0])} y2={ys(refLine[1][1])}
              stroke="rgba(255,255,255,0.2)" strokeWidth={1.5} strokeDasharray="5 4"
            />
          )}

          {/* Dots */}
          <g clipPath="url(#sc-clip)">
            {data.map((d, i) => {
              const cx = xs(x(d));
              const cy = ys(y(d));
              const r  = radius ? radius(d) : 6;
              const c  = color(d);
              const isHov = d === hovered;
              return (
                <circle key={i} cx={cx} cy={cy}
                  r={entered ? (isHov ? r * 1.6 : r) : 0}
                  fill={c}
                  fillOpacity={isHov ? 1 : 0.75}
                  stroke={isHov ? '#fff' : c}
                  strokeWidth={isHov ? 1.5 : 0.5}
                  strokeOpacity={isHov ? 0.8 : 0.3}
                  style={{ transition: entered ? 'r 0.15s ease, fill-opacity 0.15s' : 'r 0.4s ease' }}
                />
              );
            })}
          </g>

          {/* Labels */}
          {label && data.map((d, i) => {
            const lbl = label(d);
            if (!lbl) return null;
            const cx = xs(x(d));
            const cy = ys(y(d));
            const r  = radius ? radius(d) : 6;
            // Hide labels that are outside the clipped area
            if (cx < 0 || cx > iW || cy < 0 || cy > iH) return null;
            const flip = cx + r + 4 + lbl.length * 5.5 > iW;
            return (
              <text key={`lbl-${i}`}
                x={flip ? cx - r - 3 : cx + r + 3}
                y={cy}
                textAnchor={flip ? 'end' : 'start'}
                dominantBaseline="central"
                fill="#f3f4f6" fontSize={9} fontWeight="700" fontFamily="Nunito, sans-serif"
                style={{ pointerEvents: 'none' }}
                clipPath="url(#sc-clip)"
              >
                {lbl}
              </text>
            );
          })}

          {/* Voronoi overlay */}
          <rect x={0} y={0} width={iW} height={iH}
            fill="transparent"
            style={{ cursor: dragging ? 'grabbing' : 'crosshair' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => { if (!dragging) setHovered(null); }}
          />
        </g>
      </svg>

      {/* Tooltip */}
      {hovered && !dragging && (
        <div style={{
          position: 'absolute',
          left: tipPos.x + 14, top: tipPos.y - 10,
          background: '#111',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 7, padding: '8px 12px',
          fontSize: '0.75rem', color: '#e5e7eb',
          pointerEvents: 'none', zIndex: 50,
          boxShadow: '0 4px 24px rgba(0,0,0,0.5)',
          whiteSpace: 'nowrap', lineHeight: 1.7,
        }}>
          {tooltip(hovered)}
        </div>
      )}
    </div>
  );
}
