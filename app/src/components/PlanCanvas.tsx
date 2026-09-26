import { useCallback, useLayoutEffect, useRef, useState } from "react";
import { clamp, commitNow, minFor, rules, update, type Model, type Room } from "../model";

/* The plan: rectangles in feet, drawn in feet. The SVG viewBox does the
   scaling, so nothing in here converts pixels except the pointer, and a room
   that reads 13 × 10 on screen is 13 × 10 in the model. */
const SNAP = 0.5;
const snap = (v: number) => Math.round(v / SNAP) * SNAP;

type Drag =
  | { kind: "move"; id: string; start: { x: number; y: number }; orig: Room }
  | { kind: "resize"; id: string; handle: string; start: { x: number; y: number }; orig: Room }
  | null;

export default function PlanCanvas({ m, bad }: { m: Model; bad: Set<string> }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [box, setBox] = useState({ x: -9, y: -9, w: 58, h: 68 });
  const drag = useRef<Drag>(null);
  const R = rules(m);

  const layout = useCallback(() => {
    const el = svgRef.current;
    if (!el) return;
    const pad = 9;
    const r = el.getBoundingClientRect();
    const aspect = (r.width || 800) / (r.height || 600);
    let w = m.plot.w + pad * 2, h = m.plot.h + pad * 2;
    if (w / h < aspect) w = h * aspect; else h = w / aspect;
    setBox({ x: m.plot.w / 2 - w / 2, y: m.plot.h / 2 - h / 2, w, h });
  }, [m.plot.w, m.plot.h]);

  useLayoutEffect(() => {
    layout();
    const ro = new ResizeObserver(layout);
    if (svgRef.current) ro.observe(svgRef.current);
    return () => ro.disconnect();
  }, [layout]);

  const toFeet = (e: React.PointerEvent) => {
    const r = svgRef.current!.getBoundingClientRect();
    return { x: box.x + ((e.clientX - r.left) / r.width) * box.w,
             y: box.y + ((e.clientY - r.top) / r.height) * box.h };
  };

  function onDown(e: React.PointerEvent) {
    const target = e.target as SVGElement;
    const handle = target.dataset.handle;
    const id = target.dataset.id || target.closest<SVGGElement>("g.room")?.dataset.id;
    if (!id) { update(mm => { mm.selected = null; }, false); return; }
    const room = m.rooms.find(r => r.id === id);
    if (!room || room.floor !== m.floor) return;
    svgRef.current?.setPointerCapture(e.pointerId);
    drag.current = handle
      ? { kind: "resize", id, handle, start: toFeet(e), orig: { ...room } }
      : { kind: "move", id, start: toFeet(e), orig: { ...room } };
    update(mm => { mm.selected = id; }, false);
  }

  function onMove(e: React.PointerEvent) {
    const d = drag.current;
    if (!d) return;
    const p = toFeet(e), o = d.orig;
    const dx = p.x - d.start.x, dy = p.y - d.start.y;
    const [minW, minH] = minFor(o.type);
    // false: one drag is one undo point, pushed when the pointer comes up
    update(mm => {
      const r = mm.rooms.find(x => x.id === d.id);
      if (!r) return;
      if (d.kind === "move") {
        r.x = clamp(snap(o.x + dx), 0, Math.max(mm.plot.w - o.w, 0));
        r.y = clamp(snap(o.y + dy), 0, Math.max(mm.plot.h - o.h, 0));
      } else {
        const k = d.handle;
        if (k.includes("w")) { const nx = clamp(snap(o.x + dx), 0, o.x + o.w - minW); r.w = o.x + o.w - nx; r.x = nx; }
        if (k.includes("e")) r.w = clamp(snap(o.w + dx), minW, mm.plot.w - o.x);
        if (k.includes("n")) { const ny = clamp(snap(o.y + dy), 0, o.y + o.h - minH); r.h = o.y + o.h - ny; r.y = ny; }
        if (k.includes("s")) r.h = clamp(snap(o.h + dy), minH, mm.plot.h - o.y);
      }
    }, false);
  }

  const end = () => { if (drag.current) { drag.current = null; commitNow(); } };

  const gridX = [], gridY = [];
  for (let x = 0; x <= m.plot.w; x += 5) gridX.push(x);
  for (let y = 0; y <= m.plot.h; y += 5) gridY.push(y);

  return (
    <svg ref={svgRef} viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`}
         role="application" aria-label="Floor plan editor"
         onPointerDown={onDown} onPointerMove={onMove} onPointerUp={end} onPointerCancel={end}>
      <rect x={0} y={0} width={m.plot.w} height={m.plot.h} className="plot-fill" />
      {gridX.map(x => <line key={"x" + x} x1={x} y1={0} x2={x} y2={m.plot.h} className="grid-line" />)}
      {gridY.map(y => <line key={"y" + y} x1={0} y1={y} x2={m.plot.w} y2={y} className="grid-line" />)}
      <rect x={0} y={0} width={m.plot.w} height={m.plot.h} className="plot-line" />
      <rect x={R.side} y={R.front} className="setback-line"
            width={Math.max(m.plot.w - R.side * 2, 0)}
            height={Math.max(m.plot.h - R.front - R.rear, 0)} />
      <text x={m.plot.w / 2} y={-2.6} className="dimtext" textAnchor="middle">{m.plot.w} ft</text>
      <text x={-2.6} y={m.plot.h / 2} className="dimtext" textAnchor="middle"
            transform={`rotate(-90 ${-2.6} ${m.plot.h / 2})`}>{m.plot.h} ft</text>

      {/* the other floors, so a room is not placed on top of one you cannot see */}
      {m.rooms.filter(r => r.floor !== m.floor).map(r => (
        <g className="room ghost" key={"g" + r.id}>
          <rect x={r.x} y={r.y} width={r.w} height={r.h} className="body" />
        </g>
      ))}

      {m.rooms.filter(r => r.floor === m.floor).map(r => {
        const sel = r.id === m.selected;
        return (
          <g key={r.id} data-id={r.id}
             className={"room" + (sel ? " sel" : "") + (bad.has(r.id) ? " bad" : "")}>
            <rect x={r.x} y={r.y} width={r.w} height={r.h} className="body" data-id={r.id} />
            {r.w >= 6.5 && r.h >= 4.5 && <>
              <text x={r.x + 1.2} y={r.y + 3} className="nm">{r.name}</text>
              <text x={r.x + 1.2} y={r.y + 5} className="dm">
                {r.w.toFixed(1)} × {r.h.toFixed(1)} · {Math.round(r.w * r.h)} sf
              </text>
            </>}
            {sel && ([
              [r.x, r.y, "nw", "nwse-resize"], [r.x + r.w, r.y, "ne", "nesw-resize"],
              [r.x, r.y + r.h, "sw", "nesw-resize"], [r.x + r.w, r.y + r.h, "se", "nwse-resize"],
              [r.x + r.w / 2, r.y, "n", "ns-resize"], [r.x + r.w / 2, r.y + r.h, "s", "ns-resize"],
              [r.x, r.y + r.h / 2, "w", "ew-resize"], [r.x + r.w, r.y + r.h / 2, "e", "ew-resize"],
            ] as [number, number, string, string][]).map(([hx, hy, kind, cursor]) => (
              <rect key={kind} x={hx - .65} y={hy - .65} width={1.3} height={1.3}
                    className="handle" style={{ cursor }} data-handle={kind} data-id={r.id} />
            ))}
          </g>
        );
      })}
    </svg>
  );
}
