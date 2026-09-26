import { Link } from "react-router-dom";
import { useModel, measure, cost, readiness, compliance, lakh, isStarted, hasRooms } from "../model";

/* What the tool is, said once, with the live numbers from whatever design is
   currently open — a landing page that is already doing the work is a better
   argument than a landing page describing it. */
export default function Landing() {
  const m = useModel();
  const ready = isStarted(m) && hasRooms(m);
  const t = measure(m), c = cost(m, t), f = compliance(m, t), rd = readiness(m, t, c, f);

  return (
    <div className="page">
      <span className="eyebrow">Tamil Nadu · residential</span>
      <h1>Change one thing. See everything it affects.</h1>
      <p className="lede">
        Move a wall and the cost, the bylaw checks, the drawings and the bill of quantities
        all move with it — because they are four views of one set of rectangles, not four
        documents someone has to keep in step.
      </p>

      <div className="cards">
        <Link className="card" to="/studio">
          <h3>Open the studio</h3>
          <p>Draw, or describe the change in a sentence. Upload the client's brief and it
             reads it — PDF, Word, or a photo of a page.</p>
        </Link>
        <Link className="card" to="/login">
          <h3>Look around as someone</h3>
          <p>Architect, client or contractor, one click each, on a shared demo project.
             The roles are real: the client genuinely cannot edit.</p>
        </Link>
        <Link className="card" to="/report">
          <h3>Read the report</h3>
          <p>Every cost line traced to the published rate, every check to the clause it
             came from.</p>
        </Link>
      </div>

      {ready && (
        <div className="cards" style={{ marginTop: "1rem" }}>
          <div className="card">
            <span className="eyebrow">Open design</span>
            <h3>{Math.round(t.built).toLocaleString("en-IN")} sq ft</h3>
            <p>{t.bedrooms} bed · {t.baths} bath · FSI {t.fsi.toFixed(2)}</p>
          </div>
          <div className="card">
            <span className="eyebrow">Cost</span>
            <h3>{lakh(c.total)}</h3>
            <p>{m.budget
              ? <>Against a ₹{m.budget}L budget · {rd.over > 0 ? `over by ${lakh(rd.over)}` : `${lakh(-rd.over)} left`}</>
              : "No budget set yet"}</p>
          </div>
          <div className="card">
            <span className="eyebrow">Readiness</span>
            <h3>{rd.composite}</h3>
            <p>{rd.verdict}</p>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: "3rem", fontSize: "var(--s-2)" }}>What the numbers rest on</h2>
      <p className="lede" style={{ marginTop: ".6rem" }}>
        Costs come from the Tamil Nadu PWD Plinth Area Rates 2025-26 — the published circular,
        with its memo number on the line. Compliance is checked against TNCDBR 2019. Neither is
        a prediction: the cost is arithmetic over a rate card, the checks are a checklist, and
        your municipality approves plans, not this tool.
      </p>
    </div>
  );
}
