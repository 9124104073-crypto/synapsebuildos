/* Talking to the API.

   The app works with no API at all — the engines run in the browser — so
   every call here is allowed to fail, and the caller decides whether that
   matters. Signing in is what unlocks saving, sharing and roles; it is not
   what makes the tool usable. */
import { useSyncExternalStore } from "react";

export type Account = { id: string; email: string; name: string };
export type ProjectRow = { id: string; name: string; region: string; role: string };

const TOKEN_KEY = "synapse.token";
const PROJECT_KEY = "synapse.project";

let token: string | null = localStorage.getItem(TOKEN_KEY);
let account: Account | null = null;
let projectId: string | null = localStorage.getItem(PROJECT_KEY);
let role: string | null = null;

const listeners = new Set<() => void>();
export type Session = { token: string | null; account: Account | null;
                        projectId: string | null; role: string | null };
let session: Session = { token, account, projectId, role };
const emit = () => {
  session = { token, account, projectId, role };
  listeners.forEach(fn => fn());
};

export function useSession() {
  return useSyncExternalStore(
    cb => { listeners.add(cb); return () => listeners.delete(cb); },
    () => session,
  );
}

export function setToken(next: string | null) {
  token = next;
  if (next) localStorage.setItem(TOKEN_KEY, next);
  else { localStorage.removeItem(TOKEN_KEY); account = null; role = null; }
  emit();
}
export function setProject(id: string | null, theirRole: string | null = null) {
  projectId = id; role = theirRole;
  if (id) localStorage.setItem(PROJECT_KEY, id); else localStorage.removeItem(PROJECT_KEY);
  emit();
}

export async function api(path: string, init: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(path, { ...init, headers });
  if (res.status === 401) setToken(null);          // the token expired; say so by signing out
  return res;
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await api(path, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (data as { detail?: unknown }).detail;
    throw new Error(typeof detail === "string" ? detail : `${res.status} ${res.statusText}`);
  }
  return data as T;
}

/** Is there an API behind this page at all? Checked once, cheaply. */
export async function probeApi(): Promise<boolean> {
  try {
    const res = await fetch("/health", { signal: AbortSignal.timeout(4000) });
    return res.ok;
  } catch { return false; }
}

export async function login(email: string, password: string) {
  const data = await apiJson<{ token: string; user: Account }>("/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) });
  setToken(data.token);
  account = data.user; emit();
  return data.user;
}

export async function register(email: string, password: string, name = "") {
  const data = await apiJson<{ token: string; user: Account }>("/auth/register",
    { method: "POST", body: JSON.stringify({ email, password, name }) });
  setToken(data.token);
  account = data.user; emit();
  return data.user;
}

export async function refreshAccount() {
  if (!token) { account = null; emit(); return null; }
  try {
    account = await apiJson<Account>("/auth/me");
  } catch { account = null; setToken(null); }
  emit();
  return account;
}

export const myProjects = () => apiJson<ProjectRow[]>("/auth/projects");

export function signOut() { setToken(null); setProject(null); }

/* The three demo accounts, and what each is for. The password is public on
   purpose: these accounts hold nothing, and the project they share is reset
   whenever the server restarts. */
export const DEMO_PASSWORD = "demo-synapse-2026";
export const DEMO_ACCOUNTS = [
  { email: "architect@demo.synapse", label: "Architect", can: "designs, edits and saves" },
  { email: "client@demo.synapse", label: "Client", can: "reads the design and the cost" },
  { email: "contractor@demo.synapse", label: "Contractor", can: "reads the BOQ and drawings" },
];
