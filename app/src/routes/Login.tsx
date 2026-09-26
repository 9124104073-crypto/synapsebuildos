import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DEMO_ACCOUNTS, DEMO_PASSWORD, login, register, myProjects, setProject, useSession } from "../api";

/* Sign in, or look around as someone. The demo accounts are here rather than
   buried in a panel because the roles are the part of this tool people most
   need to see working before they trust it with a client. */
export default function Login() {
  const nav = useNavigate();
  const { account } = useSession();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");

  async function openTheirProject() {
    try {
      const rows = await myProjects();
      const demo = rows.find(p => p.id === "demo-chennai-house") || rows[0];
      if (demo) setProject(demo.id, demo.role);
    } catch { /* signing in still worked; the project list is a nicety */ }
    nav("/dashboard");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(""); setBusy(mode);
    try {
      if (mode === "login") await login(email.trim(), password);
      else await register(email.trim(), password);
      await openTheirProject();
    } catch (e2) {
      setErr(e2 instanceof Error && e2.message !== "Failed to fetch"
        ? e2.message : "Could not reach the API. The studio still works without it.");
    } finally { setBusy(""); }
  }

  async function asDemo(demoEmail: string) {
    setErr(""); setBusy(demoEmail);
    try {
      await login(demoEmail, DEMO_PASSWORD);
      await openTheirProject();
    } catch (e2) {
      setErr(e2 instanceof Error && e2.message !== "Failed to fetch"
        ? e2.message : "Could not reach the API, so the demo accounts are unavailable.");
    } finally { setBusy(""); }
  }

  if (account) return (
    <div className="auth">
      <h1>Signed in</h1>
      <p className="lede">as {account.email}</p>
      <div style={{ display: "flex", gap: ".5rem", marginTop: "1.4rem" }}>
        <button className="btn primary" onClick={() => nav("/dashboard")}>Your projects</button>
        <button className="btn" onClick={() => nav("/studio")}>Open the studio</button>
      </div>
    </div>
  );

  return (
    <div className="auth">
      <h1>{mode === "login" ? "Sign in" : "Create an account"}</h1>
      <p className="lede" style={{ fontSize: "var(--s--1)" }}>
        Signing in is what saves projects and shares them with a client or a contractor.
        The studio itself works without it.
      </p>

      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" required
                 value={email} onChange={e => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="pw">Password</label>
          <input id="pw" type="password" required minLength={10}
                 autoComplete={mode === "login" ? "current-password" : "new-password"}
                 value={password} onChange={e => setPassword(e.target.value)} />
        </div>
        <p className="hint">At least 10 characters. Stored only as a PBKDF2 hash, never in the clear.</p>
        {err && <div className="bad">{err}</div>}
        <button className="btn primary" type="submit" disabled={!!busy}
                style={{ justifyContent: "center" }}>
          {busy === mode ? "…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
        <button className="btn" type="button" style={{ justifyContent: "center" }}
                onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
          {mode === "login" ? "Create an account instead" : "I already have an account"}
        </button>
      </form>

      <div className="divider">or look around as</div>
      <div className="demo-grid">
        {DEMO_ACCOUNTS.map(d => (
          <button key={d.email} className="btn" disabled={!!busy} onClick={() => asDemo(d.email)}>
            <b>{busy === d.email ? "Signing in…" : d.label}</b>
            <span>{d.can}</span>
          </button>
        ))}
      </div>
      <p className="hint">
        All three share one demo project, so what each role can and cannot do is something you
        can watch rather than take on trust. The password is public and the project resets when
        the server restarts.
      </p>
    </div>
  );
}
