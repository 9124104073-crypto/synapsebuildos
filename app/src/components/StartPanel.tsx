import { useState } from "react";
import { clamp, update } from "../model";

/* Before anything exists.

   The two honest ways to begin: the client's brief, or the plot they bought.
   There is no third option where the tool guesses, because a plot size it
   invented would be indistinguishable — three screens and a cost estimate
   later — from one somebody actually measured. */
export default function StartPanel() {
  const [w, setW] = useState("");
  const [h, setH] = useState("");
  const [facing, setFacing] = useState("");
  const [err, setErr] = useState("");

  function begin(e: React.FormEvent) {
    e.preventDefault();
    const width = Number(w), depth = Number(h);
    if (!width || !depth) { setErr("Both the width and the depth are needed."); return; }
    if (width < 15 || depth < 15) { setErr("A plot under 15 ft either way is too small to lay out."); return; }
    update(m => {
      m.plot = { w: clamp(width, 15, 300), h: clamp(depth, 15, 300),
                 facing: facing === "" ? null : Number(facing) };
    });
  }

  return (
    <div className="group">
      <span className="eyebrow">Start here</span>
      <form onSubmit={begin} style={{ display: "grid", gap: ".55rem" }}>
        <div className="fields">
          <div className="field"><label htmlFor="sw">Plot width ft</label>
            <input id="sw" className="num" type="number" min={15} max={300} placeholder="—"
                   value={w} onChange={e => setW(e.target.value)} autoFocus /></div>
          <div className="field"><label htmlFor="sh">Plot depth ft</label>
            <input id="sh" className="num" type="number" min={15} max={300} placeholder="—"
                   value={h} onChange={e => setH(e.target.value)} /></div>
        </div>
        <div className="field">
          <label htmlFor="sf">Road side faces</label>
          <select id="sf" value={facing} onChange={e => setFacing(e.target.value)}>
            <option value="">Not stated</option>
            <option value="0">North</option><option value="45">North-east</option>
            <option value="90">East</option><option value="135">South-east</option>
            <option value="180">South</option><option value="225">South-west</option>
            <option value="270">West</option><option value="315">North-west</option>
          </select>
        </div>
        {err && <div className="bad">{err}</div>}
        <button className="btn primary" type="submit" style={{ justifyContent: "center" }}>
          Start the site
        </button>
      </form>
      <p className="hint">
        Nothing is assumed. Leave the road direction unstated and the sun, shading and vastu
        advice stay switched off rather than guessing which way you face.
      </p>
    </div>
  );
}
