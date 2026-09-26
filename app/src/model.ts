/* The model, and the one place it changes.

   Every route reads the same object: rooms as rectangles in feet, a plot, a
   budget, the interiors. Cost, compliance, drawings and exports are all
   measured from it by engine.js, which is imported rather than copied, so
   this app and the Python engines cannot drift apart.

   State lives in a tiny store rather than a library: one object, one
   subscribe, and an undo stack. React re-renders through useSyncExternal-
   Store, so a drag on the plan is not fifty reducer round trips. */
import { useSyncExternalStore } from "react";
import * as E from "@engine";

export type Room = {
  id: string; name: string; type: string; floor: number;
  x: number; y: number; w: number; h: number;
  finish?: { wall?: string; floor?: string; ceiling?: string };
};
export type Plot = { w: number; h: number; facing?: number | null };
export type Brief = {
  family_members: number; elderly_residents: number; children: number;
  theme: string; region: string; coastal: string; notes: string;
  sbc: number; concrete: string; steel: string;
};
export type Model = {
  plot: Plot; budget: number; floor: number; selected: string | null;
  interiors: Record<string, string[]>; name: string; brief: Brief; rooms: Room[];
};

/* An empty model. No rooms, no plot, no budget — the plot reads 0 until
   somebody states it, and every panel checks `isStarted` rather than
   pretending a 40 x 50 site exists. */
const START: Model = {
  plot: { w: 0, h: 0, facing: null }, budget: 0, floor: 0, selected: null,
  interiors: {}, name: "Untitled house",
  brief: { family_members: 0, elderly_residents: 0, children: 0, theme: "",
           region: "Chennai", coastal: "inland", notes: "",
           sbc: 150, concrete: "M25", steel: "Fe500" },
  rooms: [],
};

/** Has anyone said anything yet? Until they have, the numbers are not zero —
 *  they are unknown, and the difference matters. */
export const isStarted = (m: Model) => m.plot.w > 0 && m.plot.h > 0;
export const hasRooms = (m: Model) => m.rooms.length > 0;

const KEY = "synapse.model";
function load(): Model {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) return { ...START, ...JSON.parse(saved), selected: null };
  } catch { /* a corrupt draft should not stop the app opening */ }
  return structuredClone(START);
}

let model: Model = load();
const listeners = new Set<() => void>();
const undoStack: string[] = [];
const redoStack: string[] = [];
let lastCommitted = snap();

function snap() {
  const { rooms, plot, budget, interiors, brief } = model;
  return JSON.stringify({ rooms, plot, budget, interiors, brief });
}
function emit() {
  model = { ...model };                       // a new identity, so React notices
  listeners.forEach(fn => fn());
  try { localStorage.setItem(KEY, JSON.stringify(model)); } catch { /* private mode */ }
}

/** Change the model. `commit` pushes an undo point; a drag passes false until
 *  the pointer comes up, so one drag is one undo rather than two hundred. */
export function update(fn: (m: Model) => void, commit = true) {
  if (commit) {
    const before = snap();
    if (before !== lastCommitted) { undoStack.push(lastCommitted); lastCommitted = before; }
  }
  fn(model);
  if (commit) {
    const after = snap();
    if (after !== lastCommitted) {
      undoStack.push(lastCommitted);
      lastCommitted = after;
      redoStack.length = 0;
      if (undoStack.length > 90) undoStack.shift();
    }
  }
  emit();
}
export function commitNow() {
  const now = snap();
  if (now === lastCommitted) return;
  undoStack.push(lastCommitted); lastCommitted = now; redoStack.length = 0;
  emit();
}
function restore(json: string) {
  const o = JSON.parse(json);
  model.rooms = o.rooms; model.plot = o.plot; model.budget = o.budget;
  model.interiors = o.interiors || {}; if (o.brief) model.brief = o.brief;
  lastCommitted = snap();
  emit();
}
export function undo() { const s = undoStack.pop(); if (s) { redoStack.push(snap()); restore(s); } }
export function redo() { const s = redoStack.pop(); if (s) { undoStack.push(snap()); restore(s); } }
export const canUndo = () => undoStack.length > 0;
export const canRedo = () => redoStack.length > 0;

export function replaceModel(next: Partial<Model>) {
  update(m => { Object.assign(m, next); });
}

export function useModel(): Model {
  return useSyncExternalStore(
    cb => { listeners.add(cb); return () => listeners.delete(cb); },
    () => model,
  );
}
export const getModel = () => model;

/* ---------- the engines, bound to the current model ---------- */
export const rates = (m: Model) => E.ratesFor(m);
export const rules = (m: Model) => E.ratesFor(m).rule;
export const measure = (m: Model) => E.measure(m);
export const cost = (m: Model, t: any) => E.cost(m, t);
export const costLines = (m: Model, t: any) => E.costLines(m, t);
export const compliance = (m: Model, t: any) => E.compliance(m, t, rules(m));
export const readiness = (m: Model, t: any, c: any, f: any) => E.readiness(m, t, c, f);

export const LABEL: Record<string, string> = E.LABEL;
export const DEFAULT_SIZE: Record<string, [number, number]> = E.DEFAULT_SIZE;
export const MIN_SIZE: Record<string, [number, number]> = E.MIN_SIZE;
export const FINISH = E.FINISH;
export const REGIONS = E.REGIONS;
export const CATALOG = E.CATALOG;
export const finishOf = E.finishOf;
export const finishById = E.finishById;
export const clamp = E.clamp;
export const layoutFromBrief = E.layoutFromBrief;

export const inr = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");
export const lakh = (n: number) => "₹" + (n / 100000).toFixed(1) + "L";

/* ---------- room operations, shared by the rail and the assistant ---------- */
let seq = 100;
export const minFor = (type: string): [number, number] =>
  (MIN_SIZE[type] as [number, number]) || (MIN_SIZE.default as [number, number]);

export function uniqueName(type: string, rooms: Room[]) {
  const base = LABEL[type];
  const taken = new Set(rooms.map(r => r.name));
  if (!taken.has(base)) return base;
  for (let i = 2; ; i++) if (!taken.has(`${base} ${i}`)) return `${base} ${i}`;
}

/** Add a room at a stated size. The size is an argument, not a constant:
 *  a brief that says 12 × 14 should produce a 12 × 14 room. */
export function addRoom(type: string, size?: [number, number]): string | null {
  const m = getModel();
  if (!isStarted(m)) return null;             // no plot, nowhere to put it
  const [dw, dh] = size || (DEFAULT_SIZE[type] as [number, number]) || [10, 10];
  const R = rules(m);
  let spot: { x: number; y: number } | null = null;
  outer:
  for (let y = R.front; y + dh <= m.plot.h - R.rear; y += 1)
    for (let x = R.side; x + dw <= m.plot.w - R.side; x += 1) {
      const hit = m.rooms.some(r => r.floor === m.floor &&
        !(x + dw <= r.x + .05 || r.x + r.w <= x + .05 || y + dh <= r.y + .05 || r.y + r.h <= y + .05));
      if (!hit) { spot = { x, y }; break outer; }
    }
  if (!spot) return null;
  const id = `${type}_${seq++}`;
  update(mm => {
    mm.rooms = [...mm.rooms, { id, type, floor: mm.floor, name: uniqueName(type, mm.rooms),
                               x: spot!.x, y: spot!.y, w: dw, h: dh }];
    mm.selected = id;
  });
  return id;
}

export function removeRoom(id: string) {
  update(m => {
    m.rooms = m.rooms.filter(r => r.id !== id);
    const { [id]: _drop, ...rest } = m.interiors;
    m.interiors = rest;
    if (m.selected === id) m.selected = null;
  });
}
