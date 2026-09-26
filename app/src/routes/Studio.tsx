import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PlanCanvas from "../components/PlanCanvas";
import BriefDrop from "../components/BriefDrop";
import StartPanel from "../components/StartPanel";
import View3D from "../components/View3D";
import { exporters } from "../exports";
import { ask } from "../assistant";
import { useSession } from "../api";
import {
  addRoom, canRedo, canUndo, clamp, compliance, cost, DEFAULT_SIZE, FINISH, finishOf, hasRooms,
  isStarted, LABEL, lakh, measure, readiness, redo, removeRoom, undo, update, useModel, type Room,
} from "../model";

const TYPES = ["bedroom", "bath", "living", "kitchen", "dining", "office", "pooja",
               "utility", "stairs", "balcony", "parking"];

export default function Studio() {
  const m = useModel();
  const { account, role } = useSession();
  const [tab, setTab] = useState<"design" | "cost" | "checks">(
    () => (localStorage.getItem("synapse.side") as any) || "design");
  const [view, setView] = useState<"plan" | "3d">("plan");
  const [furniture, setFurniture] = useState(true);
  const [roof, setRoof] = useState(false);
  const [hour, setHour] = useState(12);
  const [said, setSaid] = useState("");
  const [out, setOut] = useState<{ title: string; lines: string[]; note?: string } | null>(null);

  const t = useMemo(() => measure(m), [m]);
  const c = useMemo(() => cost(m, t), [m, t]);
  const f = useMemo(() => compliance(m, t), [m, t]);
  const rd = useMemo(() => readiness(m, t, c, f), [m, t, c, f]);
  const bad = useMemo(() => new Set<string>([...t.overlaps.flat(), ...t.outside]), [t]);
  const selected = m.rooms.find(r => r.id === m.selected) || null;
  const started = isStarted(m);
  const ready = started && hasRooms(m);        // numbers are unknown until both
  const readOnly = role === "client" || role === "contractor";

  useEffect(() => { localStorage.setItem("synapse.side", tab); }, [tab]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (/input|select|textarea/i.test((e.target as HTMLElement).tagName)) return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault(); e.shiftKey ? redo() : undo();
      }
      if ((e.key === "Delete" || e.key === "Backspace") && m.selected && !readOnly) {
        e.preventDefault(); removeRoom(m.selected);
      }
    };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, [m.selected, readOnly]);

  function run(text: string) {
    if (!text.trim()) return;
    const res = ask(text);
    setSaid("");
    if (res.kind === "answer") setOut({ ...res.answer, note: [res.answer.note, res.aside].filter(Boolean).join(" · ") });
    else if (res.kind === "did") setOut({ title: "Done", lines: res.summary, note: res.aside });
    else setOut({ title: "Not understood",
      lines: ["It handles rooms, sizes, distances, finishes, furnishing, the plot and the budget."],
      note: "Try “add a bedroom 12 by 14”, “keep the bedroom 5 m from the living room”, or ask “what does it cost?”" });
  }

  return (
    <div className="studio">
      <div className="topbar">
        <Link className="brand" to="/"><i /> Synapse Studio</Link>
        <Link className="navlink" to="/dashboard">Projects</Link>
        <Link className="navlink" to="/report">Report</Link>
        <div className="sp" />
        <div className="seg">
          <button aria-pressed={view === "plan"} onClick={() => setView("plan")}>Plan</button>
          <button aria-pressed={view === "3d"} onClick={() => setView("3d")} disabled={!ready}>3D</button>
        </div>
        {view === "3d" && ready && (
          <div className="threeonly">
            <label className="chk"><input type="checkbox" checked={furniture}
              onChange={e => setFurniture(e.target.checked)} /> Furniture</label>
            <label className="chk"><input type="checkbox" checked={roof}
              onChange={e => setRoof(e.target.checked)} /> Roof</label>
            <label className="chk" title="Where the sun is, from the road direction you set">
              <input type="range" min={6} max={18} step={0.5} value={hour}
                     onChange={e => setHour(+e.target.value)} />
              <span className="num">{String(Math.floor(hour)).padStart(2, "0")}:{hour % 1 ? "30" : "00"}</span>
            </label>
          </div>
        )}
        <button className="btn" onClick={undo} disabled={!canUndo()}>Undo</button>
        <button className="btn" onClick={redo} disabled={!canRedo()}>Redo</button>
        {exporters.map(x => (
          <button key={x.id} className="btn" title={x.title} disabled={!ready}
                  onClick={() => x.run(m)}>{x.label}</button>
        ))}
        <a className="btn" href="/legacy/studio.html" title="The original page: walkthrough, drawing sheets and the printable report">
          Legacy
        </a>
        {account
          ? <span className="hint" style={{ margin: 0 }}>{account.email.split("@")[0]}{role ? ` · ${role}` : ""}</span>
          : <Link className="btn primary" to="/login">Sign in</Link>}
      </div>

      <div className="studio-main">
        <aside className="rail">
          <BriefDrop onDone={msg => setOut({ title: "Read the brief", lines: [msg] })} />
          {!started && !readOnly && <StartPanel />}
          {started && !readOnly && <AddRoom />}
          {started && <div className="group">
            <span className="eyebrow">Floors</span>
            {[...new Set([0, ...m.rooms.map(r => r.floor)])].sort().map(fl => (
              <button key={fl} className="btn" aria-pressed={m.floor === fl}
                      onClick={() => update(mm => { mm.floor = fl; }, false)}>
                {fl === 0 ? "Ground" : `Floor ${fl}`}
                <span style={{ marginLeft: "auto", opacity: .6 }}>
                  {m.rooms.filter(r => r.floor === fl).length}
                </span>
              </button>
            ))}
          </div>}
          {started && <div className="group">
            <span className="eyebrow">Plot</span>
            <div className="fields">
              <div className="field"><label htmlFor="pw">Width ft</label>
                <input id="pw" className="num" type="number" min={15} max={300} value={m.plot.w}
                       onChange={e => update(mm => { mm.plot = { ...mm.plot, w: clamp(+e.target.value || 15, 15, 300) }; })} /></div>
              <div className="field"><label htmlFor="ph">Depth ft</label>
                <input id="ph" className="num" type="number" min={15} max={300} value={m.plot.h}
                       onChange={e => update(mm => { mm.plot = { ...mm.plot, h: clamp(+e.target.value || 15, 15, 300) }; })} /></div>
            </div>
          </div>}
        </aside>

        <div className="stage">
          {started
            ? (view === "3d" && ready
                ? <View3D m={m} furniture={furniture} roof={roof} hour={hour} />
                : <PlanCanvas m={m} bad={bad} />)
            : <div className="blank">
                <h2>Nothing here yet</h2>
                <p>
                  Drop the client's brief into the panel on the left and this builds what it
                  describes — or type the plot size and start drawing.
                </p>
                <p className="hint">
                  There is no starter house on purpose. A room this tool invented would look
                  exactly like a room your client asked for, and every number here is supposed
                  to be traceable to something somebody actually said.
                </p>
              </div>}
          {started && !hasRooms(m) && (
            <div className="blank-hint">
              {m.plot.w} × {m.plot.h} ft site. Add a room on the left, or ask for one —
              “add a living room 18 by 12”.
            </div>
          )}
          <div className="promptbar">
            <form className="prompt-in" onSubmit={e => { e.preventDefault(); run(said); }}>
              <input value={said} onChange={e => setSaid(e.target.value)} spellCheck={false}
                     placeholder="Describe a change — “add a bedroom 12 by 14”, “keep the bedroom 5 m from the living room” — or ask a question" />
              <button className="btn primary" type="submit">Design</button>
            </form>
            {out && (
              <div className="prompt-out">
                <div className="who">{out.title}</div>
                <ul>{out.lines.map((l, i) => <li key={i} dangerouslySetInnerHTML={{ __html: l }} />)}</ul>
                {out.note && <div className="note">{out.note}</div>}
              </div>
            )}
          </div>
        </div>

        <aside className="side">
          <div className="glance">
            <div><b>{ready ? Math.round(t.built).toLocaleString("en-IN") + " sf" : "—"}</b><span>built-up</span></div>
            <div><b className={!ready ? "" : rd.over > 0 ? "over" : "ok"}>{ready ? lakh(c.total) : "—"}</b><span>cost</span></div>
            <div><b className={!ready ? "" : rd.composite >= 80 ? "ok" : rd.composite >= 55 ? "" : "over"}>
              {ready ? rd.composite : "—"}</b><span>ready</span></div>
          </div>
          <div className="sidetabs" role="tablist">
            {(["design", "cost", "checks"] as const).map(k => {
              const fails = f.filter((x: any) => x.outcome === "LIKELY_FAIL").length;
              return (
                <button key={k} aria-pressed={tab === k} onClick={() => setTab(k)}
                        style={k === "checks" && fails ? { color: "var(--error)" } : undefined}>
                  {k === "design" ? "Design" : k === "cost" ? "Cost" : fails ? `Checks · ${fails}` : "Checks"}
                </button>
              );
            })}
          </div>

          {tab === "design" && <DesignTab room={selected} readOnly={readOnly} />}
          {tab === "cost" && <CostTab m={m} c={c} rd={rd} />}
          {tab === "checks" && <ChecksTab f={f} rd={rd} />}
        </aside>
      </div>
    </div>
  );
}

/* Sizes are typed, not assumed. The defaults fill the boxes so a quick add is
   still one click, but every one of them can be overwritten before adding —
   which is the whole difference between a tool and a template. */
/* Sizes are typed, never assumed. The usual size for a room is offered as a
   suggestion you can click — which is a different thing from a box that
   arrives filled in and gets accepted without anyone reading it. */
function AddRoom() {
  const [type, setType] = useState("bedroom");
  const [w, setW] = useState("");
  const [h, setH] = useState("");
  const [err, setErr] = useState("");
  const usual = (DEFAULT_SIZE[type] as [number, number]) || [10, 10];
  const size: [number, number] | null = Number(w) && Number(h) ? [Number(w), Number(h)] : null;

  function pick(next: string) { setType(next); setW(""); setH(""); setErr(""); }

  return (
    <div className="group">
      <span className="eyebrow">Add a room</span>
      <div className="field">
        <select value={type} onChange={e => pick(e.target.value)} aria-label="Room type">
          {TYPES.map(k => <option key={k} value={k}>{LABEL[k]}</option>)}
        </select>
      </div>
      <div className="fields">
        <div className="field"><label htmlFor="rw">Width ft</label>
          <input id="rw" className="num" type="number" min={3} max={60} step={0.5} placeholder="—"
                 value={w} onChange={e => setW(e.target.value)} /></div>
        <div className="field"><label htmlFor="rh">Depth ft</label>
          <input id="rh" className="num" type="number" min={3} max={60} step={0.5} placeholder="—"
                 value={h} onChange={e => setH(e.target.value)} /></div>
      </div>
      <button className="btn primary" style={{ justifyContent: "center" }} disabled={!size}
              onClick={() => {
                const id = addRoom(type, size!);
                setErr(id ? "" : "No free space on this floor at that size. Make it smaller, or add a floor.");
                if (id) { setW(""); setH(""); }
              }}>
        {size ? `Add ${LABEL[type].toLowerCase()} · ${size[0]} × ${size[1]} ft` : "Enter a size"}
      </button>
      {err && <div className="bad">{err}</div>}
      <p className="hint">
        {size
          ? `${Math.round(size[0] * size[1])} sq ft. Drag the corners on the plan to adjust it afterwards.`
          : <>No size is filled in for you. A common {LABEL[type].toLowerCase()} is{" "}
              <button className="linkish" onClick={() => { setW(String(usual[0])); setH(String(usual[1])); }}>
                {usual[0]} × {usual[1]} ft
              </button>, if that helps.</>}
      </p>
    </div>
  );
}

function DesignTab({ room, readOnly }: { room: Room | null; readOnly: boolean }) {
  if (!room) return <div className="panel">
    <span className="eyebrow">Selected room</span>
    <p className="empty">Nothing selected. Click a room on the plan.</p>
  </div>;
  const fin = finishOf(room);
  return (
    <>
      <div className="panel">
        <span className="eyebrow">Selected room</span>
        <div className="field" style={{ marginBottom: ".6rem" }}>
          <label htmlFor="nm">Name</label>
          <input id="nm" value={room.name} disabled={readOnly}
                 onChange={e => update(m => { m.rooms.find(r => r.id === room.id)!.name = e.target.value; })} />
        </div>
        <div className="fields">
          <div className="field"><label htmlFor="rww">Width ft</label>
            <input id="rww" className="num" type="number" step={0.5} value={room.w} disabled={readOnly}
                   onChange={e => update(m => { m.rooms.find(r => r.id === room.id)!.w = +e.target.value; })} /></div>
          <div className="field"><label htmlFor="rhh">Depth ft</label>
            <input id="rhh" className="num" type="number" step={0.5} value={room.h} disabled={readOnly}
                   onChange={e => update(m => { m.rooms.find(r => r.id === room.id)!.h = +e.target.value; })} /></div>
        </div>
        <div className="row"><span>Area</span><b>{Math.round(room.w * room.h)} sq ft</b></div>
        {!readOnly && <button className="btn" style={{ marginTop: ".7rem" }}
                onClick={() => removeRoom(room.id)}>Delete room</button>}
      </div>
      <div className="panel">
        <span className="eyebrow">Finishes</span>
        {(["floor", "wall", "ceiling"] as const).map(kind => (
          <div className="field" key={kind} style={{ marginBottom: ".55rem" }}>
            <label htmlFor={"f" + kind}>{kind}</label>
            <select id={"f" + kind} value={fin[kind]} disabled={readOnly}
                    onChange={e => update(m => {
                      const r = m.rooms.find(x => x.id === room.id)!;
                      r.finish = { ...(r.finish || {}), [kind]: e.target.value };
                    })}>
              {(FINISH[kind] as any[]).map(o =>
                <option key={o.id} value={o.id}>{o.name} — ₹{o.rate}/sq ft</option>)}
            </select>
          </div>
        ))}
      </div>
    </>
  );
}

function CostTab({ m, c, rd }: any) {
  return (
    <div className="panel">
      <span className="eyebrow">Cost</span>
      <div className="big">{lakh(c.total)}</div>
      <div className="row"><span>Structure &amp; civil</span><b>{lakh(c.civil)}</b></div>
      <div className="row"><span>Finishes &amp; services</span><b>{lakh(c.finish)}</b></div>
      <div className="row"><span>Furniture &amp; exterior</span><b>{lakh(c.interiors)}</b></div>
      <div className="row"><span>Overheads + contingency</span><b>{lakh(c.oh + c.cont)}</b></div>
      <div className="row"><span>Against budget</span>
        <b className={rd.over > 0 ? "up" : "down"}>
          {rd.over > 0 ? "over by " + lakh(rd.over) : lakh(-rd.over) + " left"}
        </b></div>
      <div className="field" style={{ marginTop: ".8rem" }}>
        <label htmlFor="bud">Budget ₹L</label>
        <input id="bud" className="num" type="number" min={10} max={500} step={0.5} value={m.budget}
               onChange={e => update(mm => { mm.budget = clamp(+e.target.value || 10, 10, 500); })} />
      </div>
      <p className="hint">Tamil Nadu PWD Plinth Area Rates 2025-26. Arithmetic over a published
        rate card, not a prediction of what a contractor will quote.</p>
    </div>
  );
}

function ChecksTab({ f, rd }: any) {
  return (
    <>
      <div className="panel">
        <span className="eyebrow">Readiness</span>
        <div className="big">{rd.composite}</div>
        <div className="hint" style={{ marginTop: 0 }}>{rd.verdict}</div>
        <div className="bars">
          {([["Budget", rd.bFit], ["Compliance", rd.comp], ["Buildability", rd.build],
             ["Sustainability", rd.sus]] as [string, number][]).map(([label, v]) => (
            <div className="barrow" key={label}>
              <span>{label}</span>
              <span className="track">
                <b className={v >= 80 ? "" : v >= 55 ? "mid" : "bad"} style={{ width: v + "%" }} />
              </span>
              <span className="num">{v}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <span className="eyebrow">Preliminary bylaw checks</span>
        {f.map((x: any, i: number) => (
          <div key={i} className={"finding " + (x.outcome === "LIKELY_FAIL" ? "fail"
                                 : x.outcome === "LIKELY_PASS" ? "pass" : "")}>
            <div className="t">{x.title}</div>
            <div className="e">{x.why}</div>
          </div>
        ))}
        <p className="hint">Advisory only. Your municipality approves plans, not this tool.</p>
      </div>
    </>
  );
}
