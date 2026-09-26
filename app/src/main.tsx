import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Route, Routes, Link } from "react-router-dom";
import "./index.css";

import Landing from "./routes/Landing";
import Login from "./routes/Login";
import Dashboard from "./routes/Dashboard";
import Studio from "./routes/Studio";
import Report from "./routes/Report";
import { refreshAccount, useSession, signOut } from "./api";

/* The bar that is on every page except the studio, which needs its own. */
function TopBar() {
  const { account } = useSession();
  return (
    <div className="topbar">
      <Link className="brand" to="/"><i /> Synapse BuildOS</Link>
      <nav style={{ display: "flex", gap: ".2rem", marginLeft: "1rem" }}>
        <NavLink className={({ isActive }) => "navlink" + (isActive ? " on" : "")} to="/dashboard">Projects</NavLink>
        <NavLink className={({ isActive }) => "navlink" + (isActive ? " on" : "")} to="/studio">Studio</NavLink>
        <NavLink className={({ isActive }) => "navlink" + (isActive ? " on" : "")} to="/report">Report</NavLink>
      </nav>
      <div className="sp" />
      {account
        ? <>
            <span className="hint" style={{ margin: 0 }}>{account.email}</span>
            <button className="btn" onClick={signOut}>Sign out</button>
          </>
        : <Link className="btn primary" to="/login">Sign in</Link>}
    </div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gridTemplateRows: "58px 1fr", height: "100%" }}>
    <TopBar />
    <div style={{ overflowY: "auto" }}>{children}</div>
  </div>;
}

function App() {
  useEffect(() => { refreshAccount(); }, []);
  return (
    <Routes>
      <Route path="/" element={<Shell><Landing /></Shell>} />
      <Route path="/login" element={<Shell><Login /></Shell>} />
      <Route path="/dashboard" element={<Shell><Dashboard /></Shell>} />
      <Route path="/report" element={<Shell><Report /></Shell>} />
      {/* The studio fills the window and brings its own bar. */}
      <Route path="/studio" element={<Studio />} />
      <Route path="*" element={<Shell><div className="page">
        <h1>Not a page here</h1>
        <p className="lede">Try the <Link to="/studio">studio</Link>.</p>
      </div></Shell>} />
    </Routes>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
