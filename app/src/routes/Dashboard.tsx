import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { myProjects, setProject, useSession, type ProjectRow } from "../api";
import { useModel, measure, cost, compliance, readiness, lakh } from "../model";

/* Projects, and the one you have open. Kept deliberately thin: the useful
   work is one click away, and a dashboard that makes you read it first is a
   toll booth. */
export default function Dashboard() {
  const { account, projectId } = useSession();
  const nav = useNavigate();
  const m = useModel();
  const t = measure(m), c = cost(m, t), f = compliance(m, t), rd = readiness(m, t, c, f);
  const [rows, setRows] = useState<ProjectRow[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!account) { setRows([]); return; }
    myProjects().then(setRows).catch(e => setErr(String(e.message || e)));
  }, [account]);

  return (
    <div className="page">
      <h1>Projects</h1>
      <p className="lede">
        {account ? `Signed in as ${account.email}.`
                 : "Not signed in — the design below lives in this browser only."}
      </p>

      <div className="cards">
        <div className="card">
          <span className="eyebrow">Open in this browser</span>
          <h3>{m.name}</h3>
          <p>{Math.round(t.built).toLocaleString("en-IN")} sq ft · {t.bedrooms} bed · {lakh(c.total)}
             {" · readiness "}{rd.composite}</p>
          <div style={{ display: "flex", gap: ".4rem", marginTop: ".6rem" }}>
            <Link className="btn primary" to="/studio">Open the studio</Link>
            <Link className="btn" to="/report">Report</Link>
          </div>
        </div>

        {!account && (
          <div className="card">
            <span className="eyebrow">Saving and sharing</span>
            <h3>Sign in to keep it</h3>
            <p>A signed-in project can be opened from another machine and shared with a
               client or a contractor, each seeing what their role should see.</p>
            <Link className="btn" to="/login" style={{ marginTop: ".6rem" }}>Sign in</Link>
          </div>
        )}
      </div>

      {account && (
        <>
          <h2 style={{ marginTop: "2.6rem", fontSize: "var(--s-2)" }}>On the server</h2>
          {err && <div className="bad">{err}</div>}
          {rows === null && <p className="empty">Loading…</p>}
          {rows?.length === 0 && <p className="empty">No projects on the server yet.</p>}
          {!!rows?.length && (
            <table className="data" style={{ marginTop: ".8rem" }}>
              <thead><tr><th>Project</th><th>Region</th><th>Your role</th><th /></tr></thead>
              <tbody>
                {rows.map(p => (
                  <tr key={p.id}>
                    <td>{p.name}</td>
                    <td>{p.region}</td>
                    <td>{p.role}</td>
                    <td className="n">
                      {p.id === projectId
                        ? <span className="hint" style={{ margin: 0 }}>open</span>
                        : <button className="btn" onClick={() => { setProject(p.id, p.role); nav("/studio"); }}>
                            Open
                          </button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
