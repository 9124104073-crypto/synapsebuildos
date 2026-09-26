import { useRef, useState } from "react";
import { parseBrief, readDocument, type FoundBrief } from "../brief";
import { addRoom, clamp, getModel, layoutFromBrief, update, type Model } from "../model";

/* Reading a client's brief is the first thing most people will want to do, so
   it is a target you can drop a file onto, in the rail, above everything else
   — not a button hidden behind a menu. */
export default function BriefDrop({ onDone }: { onDone: (message: string) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [step, setStep] = useState("");
  const [err, setErr] = useState("");
  const [found, setFound] = useState<{ b: FoundBrief; notes: string[]; how: string; name: string } | null>(null);

  async function take(file: File | undefined) {
    if (!file) return;
    setErr(""); setFound(null);
    if (file.size > 25 * 1024 * 1024) {
      setErr(`${file.name} is ${(file.size / 1048576).toFixed(1)} MB. Keep it under 25 MB.`);
      return;
    }
    setStep("Opening the file…");
    try {
      const doc = await readDocument(file, setStep);
      const { found: b, notes } = parseBrief(doc.text);
      setStep("");
      if (!notes.length) {
        setErr(`Read it as ${doc.how}, but found no plot size, bedroom count or budget. `
             + (doc.text.trim().length < 30
                ? "Almost no text came out — if it is a photo, a sharper one reads better."
                : "It should say something like “40 × 60 ft plot, 3 BHK, ₹65 lakhs”."));
        return;
      }
      setFound({ b, notes, how: doc.how, name: file.name });
    } catch (e) {
      setStep("");
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  function apply(rebuild: boolean) {
    if (!found) return;
    const b = found.b;
    update(mm => {
      if (b.region) mm.brief = { ...mm.brief, region: b.region };
      if (b.coastal) mm.brief = { ...mm.brief, coastal: b.coastal };
      if (b.budget) mm.budget = clamp(b.budget, 10, 500);
      if (b.family) mm.brief = { ...mm.brief, family_members: b.family };
      if (b.elderly) mm.brief = { ...mm.brief, elderly_residents: b.elderly };
      if (b.children) mm.brief = { ...mm.brief, children: b.children };

      if (rebuild) {
        const built = layoutFromBrief({
          plot_w: b.plot_w || mm.plot.w, plot_h: b.plot_h || mm.plot.h,
          facing: b.facing, region: b.region || mm.brief.region,
          bedrooms: b.bedrooms || 3, bathrooms: b.bathrooms || 2,
          floors: b.floors || 1, budget: b.budget || mm.budget,
          parking: b.extras.includes("parking"),
          // sizes the brief actually stated, rather than the standard ones
          bed_w: b.rooms.find(r => r.type === "bedroom")?.w,
          bed_h: b.rooms.find(r => r.type === "bedroom")?.h,
          living_w: b.rooms.find(r => r.type === "living")?.w,
          living_h: b.rooms.find(r => r.type === "living")?.h,
        } as any) as Partial<Model>;
        Object.assign(mm, { rooms: built.rooms, plot: built.plot, interiors: {},
                            selected: null, floor: 0 });
      } else {
        if (b.plot_w) mm.plot = { ...mm.plot, w: clamp(b.plot_w, 15, 300) };
        if (b.plot_h) mm.plot = { ...mm.plot, h: clamp(b.plot_h, 15, 300) };
        if (b.facing !== undefined) mm.plot = { ...mm.plot, facing: b.facing };
      }
    });
    if (rebuild) {
      // rooms the brief asked for that a standard layout does not include,
      // at the size it stated where it stated one
      for (const type of b.extras.filter(x => x !== "parking")) {
        const said = b.rooms.find(r => r.type === type);
        addRoom(type, said ? [said.w, said.h] : undefined);
      }
    }
    const now = getModel();
    onDone(rebuild
      ? `Built ${now.rooms.length} rooms on a ${now.plot.w} × ${now.plot.h} ft plot from ${found.name}.`
      : `Took the numbers from ${found.name}; the plan is untouched.`);
    setFound(null);
  }

  return (
    <div className="group">
      <span className="eyebrow">Client brief</span>
      <div className={"dropzone" + (over ? " over" : "")}
           onClick={() => input.current?.click()}
           onDragOver={e => { e.preventDefault(); setOver(true); }}
           onDragLeave={() => setOver(false)}
           onDrop={e => { e.preventDefault(); setOver(false); take(e.dataTransfer.files?.[0]); }}>
        <b>{step || "Drop a brief here"}</b>
        <span>{step
          ? "Reading…"
          : "PDF, Word, text or a photo of a page. Scans go through OCR. Nothing leaves this machine."}</span>
      </div>
      <input ref={input} type="file" hidden
             accept=".pdf,.docx,.txt,.md,.csv,.png,.jpg,.jpeg,.webp"
             onChange={e => { take(e.target.files?.[0]); e.target.value = ""; }} />

      {err && <div className="bad">{err}</div>}

      {found && (
        <div className="finding">
          <div className="t">{found.name}</div>
          <div className="e">{found.how}</div>
          <ul style={{ margin: ".5rem 0 0", paddingLeft: "1.1rem", display: "grid", gap: ".15rem" }}>
            {found.notes.map((n, i) => <li key={i} style={{ fontSize: "var(--s--2)" }}>{n}</li>)}
          </ul>
          <p className="hint">Building replaces the rooms on the plan. Undo puts them back.</p>
          <div style={{ display: "flex", gap: ".4rem", marginTop: ".5rem" }}>
            <button className="btn primary" onClick={() => apply(true)}>Build this</button>
            <button className="btn" onClick={() => apply(false)}>Numbers only</button>
          </div>
        </div>
      )}
    </div>
  );
}
