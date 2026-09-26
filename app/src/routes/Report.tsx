import { Link } from "react-router-dom";
import {
  compliance, cost, costLines, inr, lakh, measure, rates, readiness, useModel,
} from "../model";

/* The report is the thing that leaves the building: what it costs, what it
   rests on, and what might stop it. Every line names its source, because a
   number a client cannot trace is a number they are right to distrust. */
export default function Report() {
  const m = useModel();
  const t = measure(m), c = cost(m, t), f = compliance(m, t), rd = readiness(m, t, c, f);
  const lines = costLines(m, t).filter((l: any) => l.amount > 0);
  const R = rates(m);

  return (
    <div className="page">
      <span className="eyebrow">{m.brief.region} · {new Date().toLocaleDateString("en-IN",
        { day: "numeric", month: "long", year: "numeric" })}</span>
      <h1>{m.name}</h1>
      <p className="lede">
        {t.bedrooms} bedrooms and {t.baths} bathrooms over {Math.max(...m.rooms.map(r => r.floor)) + 1} floor(s),
        {" "}{Math.round(t.built).toLocaleString("en-IN")} sq ft built-up on a {m.plot.w} × {m.plot.h} ft plot.
      </p>

      <div className="cards" style={{ marginTop: "1.6rem" }}>
        <div className="card"><span className="eyebrow">Cost</span><h3>{lakh(c.total)}</h3>
          <p>{inr(c.total / Math.max(t.built, 1))} per sq ft</p></div>
        <div className="card"><span className="eyebrow">Against budget</span>
          <h3>{rd.over > 0 ? "over " + lakh(rd.over) : lakh(-rd.over) + " left"}</h3>
          <p>Budget ₹{m.budget}L</p></div>
        <div className="card"><span className="eyebrow">FSI</span><h3>{t.fsi.toFixed(2)}</h3>
          <p>{(t.cover * 100).toFixed(0)}% ground coverage</p></div>
        <div className="card"><span className="eyebrow">Readiness</span><h3>{rd.composite}</h3>
          <p>{rd.verdict}</p></div>
      </div>

      <h2 style={{ marginTop: "2.6rem", fontSize: "var(--s-2)" }}>Where the money goes</h2>
      <table className="data" style={{ marginTop: ".8rem" }}>
        <thead><tr><th>Item</th><th>Basis</th><th className="n">Amount</th></tr></thead>
        <tbody>
          {lines.map((l: any, i: number) => (
            <tr key={i}>
              <td>{l.item}</td>
              <td style={{ color: "var(--muted-2)", fontSize: "var(--s--2)" }}>{l.basis}</td>
              <td className="n">{inr(l.amount)}</td>
            </tr>
          ))}
          <tr><td>Furniture and exterior</td>
            <td style={{ color: "var(--muted-2)", fontSize: "var(--s--2)" }}>selected catalogue items</td>
            <td className="n">{inr(c.interiors)}</td></tr>
          <tr><td>Contingency</td>
            <td style={{ color: "var(--muted-2)", fontSize: "var(--s--2)" }}>on the total above</td>
            <td className="n">{inr(c.cont)}</td></tr>
        </tbody>
        <tfoot><tr><td colSpan={2}><b>Total</b></td><td className="n"><b>{inr(c.total)}</b></td></tr></tfoot>
      </table>
      <p className="hint">{R.source}</p>

      <h2 style={{ marginTop: "2.6rem", fontSize: "var(--s-2)" }}>Rooms</h2>
      <table className="data" style={{ marginTop: ".8rem" }}>
        <thead><tr><th>Room</th><th>Floor</th><th className="n">Size</th><th className="n">Area</th></tr></thead>
        <tbody>
          {[...m.rooms].sort((a, b) => a.floor - b.floor || a.name.localeCompare(b.name)).map(r => (
            <tr key={r.id}>
              <td>{r.name}</td><td>{r.floor === 0 ? "Ground" : `Floor ${r.floor}`}</td>
              <td className="n">{r.w} × {r.h} ft</td>
              <td className="n">{Math.round(r.w * r.h)} sq ft</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: "2.6rem", fontSize: "var(--s-2)" }}>Preliminary bylaw checks</h2>
      <div style={{ marginTop: ".8rem" }}>
        {f.map((x: any, i: number) => (
          <div key={i} className={"finding " + (x.outcome === "LIKELY_FAIL" ? "fail"
                                 : x.outcome === "LIKELY_PASS" ? "pass" : "")}>
            <div className="t">{x.title}</div>
            <div className="e">{x.why}</div>
          </div>
        ))}
      </div>
      <p className="hint">
        Checked against {R.rule.version}. Advisory only: your municipality approves plans, not this
        tool, and a check that cannot be evaluated is reported as undetermined rather than passed.
      </p>

      <div style={{ display: "flex", gap: ".5rem", marginTop: "2rem" }}>
        <button className="btn primary" onClick={() => print()}>Print / save PDF</button>
        <Link className="btn" to="/studio">Back to the studio</Link>
      </div>
    </div>
  );
}
