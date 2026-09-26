/* The assistant: spelling, memory, and instructions that change the model.

   Half of what people type at a design tool is a question, not an order, and
   most of the orders are follow-ups — "make it wider" only means something if
   you remember what "it" was. Both are handled here, against the same engines
   the panels use, so an answer cannot disagree with the number on screen. */
import * as E from "@engine";
import {
  addRoom, clamp, compliance, cost, costLines, FINISH, finishById, finishOf,
  getModel, inr, lakh, LABEL, measure, minFor, readiness, REGIONS, removeRoom, uniqueName,
  update, type Room,
} from "./model";

/* ---------- memory ---------- */
type Turn = { role: "you" | "synapse"; text: string };
const MEM = "synapse.chat";
export const chat = {
  room: null as string | null,
  last: null as string | null,
  turns: [] as Turn[],
  saw(room: Room | null | undefined) { if (room) this.room = room.id; return room; },
  subject(): Room | null { return getModel().rooms.find(r => r.id === this.room) || null; },
  say(role: Turn["role"], text: string) {
    this.turns.push({ role, text });
    if (this.turns.length > 24) this.turns.shift();
    this.save();
  },
  save() {
    try { localStorage.setItem(MEM, JSON.stringify(
      { room: this.room, last: this.last, turns: this.turns })); } catch { /* private mode */ }
  },
  load() {
    try {
      const o = JSON.parse(localStorage.getItem(MEM) || "{}");
      this.room = o.room ?? null; this.last = o.last ?? null; this.turns = o.turns || [];
    } catch { /* ignore a corrupt transcript */ }
  },
  forget() { this.room = null; this.last = null; this.turns = []; localStorage.removeItem(MEM); },
};
chat.load();

/* ---------- spelling ----------
   Unknown words snap to the nearest word the engine knows, and only when the
   nearest one is close. Ordinary English is left alone: correcting "keep" to
   "deep" is far worse than leaving a genuine typo in place. */
const VOCAB = ("add remove delete move make bigger smaller wider narrower taller split divide "
  + "separate partition merge combine join apart away bedroom bathroom toilet living hall "
  + "kitchen dining office study pooja utility stairs balcony parking porch room house floor "
  + "ground first upstairs downstairs plot budget lakhs region north south east west facing "
  + "road furnish furniture essentials comfort premium marble granite wood tile vitrified "
  + "wall walls ceiling window door solar metre metres feet wide deep long cost price rules "
  + "setback coverage readiness").split(" ");
const VOCAB_SET = new Set(VOCAB);
const COMMON = new Set(("the a an and or but if then than that this these those with without for "
  + "from into onto over under near next beside between behind front back side there here keep "
  + "make made move moved put place placed give given take taken want need should would could "
  + "must have has had been being does did done like also just only even still more most less "
  + "each other another same different new old big small long short high low wide open close "
  + "please thanks okay yes not never always maybe about around after before while when where "
  + "which what why how who can cannot will shall may might let its their our your house home "
  + "family children kids parents money cost costs price prices lakh lakhs crore rupees budget "
  + "total area size left right upper lower inside outside above below along across through "
  + "instead rather enough already almost nearly quite really actually probably").split(" "));

function editDistance(a: string, b: string) {
  if (Math.abs(a.length - b.length) > 2) return 9;
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let last = prev[0]; prev[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cur = prev[j];
      prev[j] = Math.min(prev[j] + 1, prev[j - 1] + 1, last + (a[i - 1] === b[j - 1] ? 0 : 1));
      last = cur;
    }
  }
  return prev[b.length];
}

export function spell(raw: string) {
  const fixes: string[] = [];
  const rooms = getModel().rooms;
  const text = raw.split(/(\s+)/).map(tok => {
    const w = tok.toLowerCase();
    if (!/^[a-z]{4,}$/.test(w) || VOCAB_SET.has(w) || COMMON.has(w)) return tok;
    if (rooms.some(r => r.name.toLowerCase().split(/\s+/).includes(w))) return tok;
    let best: string | null = null, bestD = 3;
    const limit = w.length <= 5 ? 1 : 2;
    for (const cand of VOCAB) {
      const d = editDistance(w, cand);
      if (d < bestD && d <= limit) { bestD = d; best = cand; }
    }
    if (!best) return tok;
    fixes.push(`${tok.trim()} → ${best}`);
    return best;
  }).join("");
  return { text, fixes };
}

/* Speech writes words where this needs numbers: "forty by sixty" is a plot. */
const SPOKEN: Record<string, number> = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5,
  six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13,
  fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19,
  twenty: 20, thirty: 30, forty: 40, fourty: 40, fifty: 50, sixty: 60, seventy: 70,
  eighty: 80, ninety: 90 };
export function digitise(text: string) {
  let out = " " + text.toLowerCase() + " ";
  out = out.replace(/\b(twenty|thirty|forty|fourty|fifty|sixty|seventy|eighty|ninety)[ -](one|two|three|four|five|six|seven|eight|nine)\b/g,
    (_, tens, ones) => String(SPOKEN[tens] + SPOKEN[ones]));
  out = out.replace(new RegExp("\\b(" + Object.keys(SPOKEN).join("|") + ")\\b", "g"), w => String(SPOKEN[w]));
  return out.replace(/\b(\d+(?:\.\d+)?)\s*(metres?|meters?)\b/g, "$1 m")
            .replace(/\b(\d+(?:\.\d+)?)\s*(feet|foot)\b/g, "$1 ft")
            .replace(/\blakhs?\b|\blacs?\b/g, "lakh")
            .trim();
}

/* ---------- finding things in a sentence ---------- */
const norm = (s: string) => " " + s.toLowerCase().replace(/[^a-z0-9.\s×'-]/g, " ").replace(/\s+/g, " ") + " ";

const TYPE_WORDS: [string, string[]][] = [
  ["bedroom", ["bedroom", "bed room", "bedrooms"]], ["bath", ["bathroom", "toilet", "wc", "bath"]],
  ["living", ["living", "hall", "drawing room"]], ["kitchen", ["kitchen"]], ["dining", ["dining"]],
  ["office", ["office", "study"]], ["pooja", ["pooja", "puja", "prayer"]],
  ["utility", ["utility", "laundry", "wash"]], ["stairs", ["stairs", "staircase"]],
  ["balcony", ["balcony", "sitout", "sit out"]], ["parking", ["parking", "garage", "porch", "car park"]],
];

export function findType(s: string): string | null {
  let best: string | null = null, len = 0;
  for (const [type, words] of TYPE_WORDS)
    for (const w of words)
      if ((s.includes(" " + w + " ") || s.includes(" " + w + "s ")) && w.length > len)
        { best = type; len = w.length; }
  return best;
}

export function findRoom(s: string): Room | null {
  const m = getModel();
  const named = m.rooms.find(r => s.includes(" " + r.name.toLowerCase()));
  if (named) return chat.saw(named) as Room;
  const type = findType(s);
  if (!type) return null;
  const pool = m.rooms.filter(r => r.type === type);
  if (!pool.length) return null;
  // same rule: a bare number picks the nth room, a number with a unit is a size
  const n = s.match(/\b(\d)\b(?!\s*(m|ft|feet|foot|metre|meter)\b)/);
  if (n && pool[Number(n[1]) - 1]) return chat.saw(pool[Number(n[1]) - 1]) as Room;
  return chat.saw(pool[0]) as Room;
}

/** Two rooms in the order they were said — the first is the one that stays put. */
export function findTwoRooms(s: string): [Room, Room] | null {
  const m = getModel();
  const hits: { r: Room; at: number }[] = [];
  const claim = (room: Room | undefined, at: number) => {
    if (room && at >= 0 && !hits.some(h => h.r === room)) hits.push({ r: room, at });
  };
  for (const r of m.rooms) claim(r, s.indexOf(" " + r.name.toLowerCase()));
  for (const [type, words] of TYPE_WORDS)
    for (const w of words) {
      const at = s.indexOf(" " + w);
      if (at < 0) continue;
      // "bedroom 2" is the second bedroom; "kitchen 2 m" is a distance. The
      // unit is what tells them apart.
      const tail = s.slice(at + w.length + 1, at + w.length + 8);
      const after = /^\s*(\d)(?!\s*(m|ft|feet|foot|metre|meter)\b)/.exec(tail);
      const pool = m.rooms.filter(r => r.type === type);
      claim(after && pool[Number(after[1]) - 1]
        ? pool[Number(after[1]) - 1]
        : pool.find(r => !hits.some(h => h.r === r)), at);
    }
  hits.sort((a, b) => a.at - b.at);
  return hits.length >= 2 ? [hits[0].r, hits[1].r] : null;
}

const M_PER_FT = 3.28084;
export function feetFrom(s: string) {
  const m = s.match(/(\d+(?:\.\d+)?)\s*(m|metre|metres|meter|meters|ft|feet|foot|')/);
  if (!m) return null;
  const n = Number(m[1]);
  return /^m/.test(m[2]) ? { ft: n * M_PER_FT, said: `${n} m` } : { ft: n, said: `${n} ft` };
}

/* A size stated as "12 x 14" or "12 by 14 ft". */
export function sizeFrom(s: string): [number, number] | null {
  const m = s.match(/(\d{1,2}(?:\.\d)?)\s*(?:ft|feet|')?\s*(?:x|×|by)\s*(\d{1,2}(?:\.\d)?)/);
  return m ? [Number(m[1]), Number(m[2])] : null;
}

/* ---------- context ---------- */
const PRONOUN = /\b(it|that|this|there|the room|the same)\b/;
export function resolveContext(raw: string) {
  let text = raw.trim();
  if (/^(again|do (it|that) again|once more|repeat)\b/i.test(text) && chat.last)
    return { text: chat.last, note: `Repeating “${chat.last}”` };

  const carry = text.match(/^(?:and|also|same (?:for|in|with)|do the same (?:for|in|to))\s+(.*)$/i);
  if (carry && chat.last) {
    const prev = chat.subject();
    const room = findRoom(norm(carry[1]));
    if (room) {
      const rebuilt = prev && prev !== room
        ? chat.last.replace(new RegExp(prev.name, "i"), room.name)
        : `${chat.last} in ${room.name}`;
      return { text: rebuilt, note: `Reading that as “${rebuilt}”` };
    }
  }
  if (PRONOUN.test(text.toLowerCase()) && !findRoom(norm(text))) {
    const room = chat.subject();
    if (room) return { text: text.replace(PRONOUN, room.name), note: `“it” = ${room.name}` };
  }
  return { text, note: "" };
}

/* ---------- geometry the instructions need ---------- */
export function splitRoom(room: Room, parts: number, newType: string | null) {
  const n = clamp(parts || 2, 2, 4);
  const alongW = room.w >= room.h;
  const span = (alongW ? room.w : room.h) / n;
  const [minW, minH] = minFor(newType || room.type);
  const need = alongW ? minW : minH;
  if (span < need)
    return { bad: `${room.name} is too small to divide into ${n} — each part would be under ${need} ft.` };
  update(m => {
    const target = m.rooms.find(r => r.id === room.id)!;
    const made: Room[] = [];
    for (let i = 1; i < n; i++) {
      const type = newType || target.type;
      made.push({
        id: `${type}_${Date.now()}_${i}`, type, floor: target.floor,
        name: uniqueName(type, [...m.rooms, ...made]),
        x: alongW ? target.x + span * i : target.x,
        y: alongW ? target.y : target.y + span * i,
        w: alongW ? span : target.w,
        h: alongW ? target.h : span,
      });
    }
    if (alongW) target.w = span; else target.h = span;
    m.rooms = [...m.rooms, ...made];
    m.selected = made[0].id;
  });
  const w = alongW ? span : room.w, h = alongW ? room.h : span;
  return { summary: `Divided ${room.name} into ${n}, ${alongW ? "side by side" : "front to back"}, `
                  + `${w.toFixed(1)} × ${h.toFixed(1)} ft each.` };
}

export function mergeRooms(a: Room, b: Room) {
  if (a.floor !== b.floor) return { bad: `${a.name} and ${b.name} are on different floors.` };
  const m = getModel();
  const x0 = Math.min(a.x, b.x), y0 = Math.min(a.y, b.y);
  const x1 = Math.max(a.x + a.w, b.x + b.w), y1 = Math.max(a.y + a.h, b.y + b.h);
  const caught = m.rooms.filter(r => r !== a && r !== b && r.floor === a.floor &&
    r.x + r.w > x0 + .05 && r.x < x1 - .05 && r.y + r.h > y0 + .05 && r.y < y1 - .05);
  if (caught.length)
    return { bad: `That would swallow ${caught.map(r => r.name).join(" and ")}. Move it out of the way first.` };
  const keep = a.w * a.h >= b.w * b.h ? a : b, drop = keep === a ? b : a;
  update(mm => {
    const k = mm.rooms.find(r => r.id === keep.id)!;
    k.x = x0; k.y = y0; k.w = x1 - x0; k.h = y1 - y0;
    mm.rooms = mm.rooms.filter(r => r.id !== drop.id);
    mm.selected = k.id;
  });
  return { summary: `Knocked ${a.name} and ${b.name} together — one ${(x1 - x0).toFixed(1)} × `
                  + `${(y1 - y0).toFixed(1)} ft ${LABEL[keep.type].toLowerCase()}, `
                  + `${Math.round((x1 - x0) * (y1 - y0))} sq ft.` };
}

export function setGap(a: Room, b: Room, ft: number) {
  const m = getModel(), P = m.plot;
  const fitsX = a.w + b.w + ft <= P.w, fitsY = a.h + b.h + ft <= P.h;
  const gapX = Math.max(a.x - (b.x + b.w), b.x - (a.x + a.w));
  const gapY = Math.max(a.y - (b.y + b.h), b.y - (a.y + a.h));
  let useX = gapX >= gapY;
  if (useX && !fitsX) useX = false; else if (!useX && !fitsY) useX = true;
  if (useX ? !fitsX : !fitsY) {
    const need = useX ? a.w + b.w + ft : a.h + b.h + ft;
    return { bad: `A ${ft.toFixed(1)} ft gap does not fit either way on a ${P.w} × ${P.h} ft plot — `
                + `${a.name} and ${b.name} plus the gap need ${need.toFixed(1)} ft.` };
  }
  const half = (v: number) => Math.round(v * 2) / 2;
  update(mm => {
    const t = mm.rooms.find(r => r.id === b.id)!;
    if (useX) {
      const right = b.x >= a.x;
      let nx = right ? a.x + a.w + ft : a.x - ft - b.w;
      if (nx < 0 || nx + b.w > P.w) nx = right ? a.x - ft - b.w : a.x + a.w + ft;
      t.x = half(clamp(nx, 0, P.w - b.w));
    } else {
      const below = b.y >= a.y;
      let ny = below ? a.y + a.h + ft : a.y - ft - b.h;
      if (ny < 0 || ny + b.h > P.h) ny = below ? a.y - ft - b.h : a.y + a.h + ft;
      t.y = half(clamp(ny, 0, P.h - b.h));
    }
  });
  return { ok: true, axis: useX ? "across the plot" : "front to back" };
}

/* ---------- questions ---------- */
export type Answer = { title: string; lines: string[]; note?: string };
const ORDER = /^\s*(set|make|change|add|remove|delete|move|put|use|keep|split|divide|merge|join|furnish|apply|resize|rename|increase|reduce|raise|lower)\b/;
const QUESTION = /^(what|whats|what's|how|why|which|where|when|is|are|can|do|does|show|tell|list|explain|give)\b|\?$/;

export function answerQuestion(raw: string): Answer | null {
  const s = norm(raw), m = getModel();
  if (ORDER.test(s) && !/\?\s*$/.test(s)) return null;
  if (!QUESTION.test(s.trim()) && !/\b(cost|budget|score|help)\b/.test(s)) return null;

  const t = measure(m), c = cost(m, t), f = compliance(m, t), rd = readiness(m, t, c, f);

  if (/\b(help|what can you do|commands)\b/.test(s)) return { title: "What I can do", lines: [
    "<b>Change it</b> — “add a bedroom 12 by 14”, “make the kitchen 3 ft wider”, “split the living room”, “merge the dining and the kitchen”",
    "<b>Distance</b> — “keep the bedroom 5 m from the living room”",
    "<b>Finishes</b> — “marble floor in the living room”, “furnish the bedroom premium”",
    "<b>Site</b> — “plot 40 by 60”, “budget 72 lakh”, “location Coimbatore”",
    "<b>Questions</b> — “what does it cost?”, “why am I over budget?”, “what breaks the rules?”",
  ] };

  if (/\b(cost|price|budget|expensive|total|estimate)\b/.test(s)) {
    if (/\b(why|over|reduce|save|cut|cheaper|lower)\b/.test(s)) return {
      title: rd.over > 0 ? `Over budget by ${lakh(rd.over)}` : `Under budget by ${lakh(-rd.over)}`,
      lines: [
        `Furniture and exterior: <b>${lakh(c.interiors)}</b> — the easiest to defer`,
        `Chosen finishes: <b>${lakh(t.wallCost + t.floorCost + t.ceilCost)}</b> over the base specification`,
        `Built-up area: <b>${Math.round(t.built)} sq ft</b> — every 100 sq ft is about ${lakh(c.total / Math.max(t.built, 1) * 100)}`,
      ],
      note: `${lakh(c.total)} against a ₹${m.budget}L budget.`,
    };
    const lines = costLines(m, t).filter((l: any) => l.amount > 0)
      .sort((a: any, b: any) => b.amount - a.amount).slice(0, 5)
      .map((l: any) => `${l.item}: <b>${inr(l.amount)}</b>`);
    return { title: `${lakh(c.total)} all in`,
      lines: [...lines, `Furniture and exterior: <b>${inr(c.interiors)}</b>`],
      note: `${Math.round(t.built)} sq ft · ${inr(c.total / Math.max(t.built, 1))} per sq ft` };
  }

  if (/\b(rule|rules|bylaw|legal|compliance|setback|fsi|coverage|approv|sanction)\b/.test(s)) {
    const fails = f.filter((x: any) => x.outcome === "LIKELY_FAIL");
    return { title: fails.length ? `${fails.length} problem(s) to fix` : "Nothing fails right now",
      lines: f.slice(0, 7).map((x: any) =>
        `${x.outcome === "LIKELY_FAIL" ? "✗" : x.outcome === "LIKELY_PASS" ? "✓" : "?"} <b>${x.title}</b> — ${x.why}`),
      note: "Advisory only. Your municipality approves plans, not this tool." };
  }

  if (/\b(ready|readiness|score)\b/.test(s)) return {
    title: `Readiness ${rd.composite} — ${rd.verdict}`,
    lines: [`Budget fit <b>${rd.bFit}</b>`, `Compliance <b>${rd.comp}</b>`,
            `Buildability <b>${rd.build}</b>`, `Sustainability <b>${rd.sus}</b>`],
    note: "Weighted 35 / 25 / 25 / 15. The weights are a stated guess, to be tuned against real projects." };

  const room = findRoom(s);
  if (room && /\b(big|size|area|dimension|wide|long|finish|floor|wall|ceiling)\b/.test(s)) {
    const fin = finishOf(room);
    return { title: `${room.name} — ${room.w} × ${room.h} ft`, lines: [
      `Area <b>${Math.round(room.w * room.h)} sq ft</b> on ${room.floor === 0 ? "the ground floor" : "floor " + room.floor}`,
      `Floor <b>${finishById("floor", fin.floor).name}</b> · walls <b>${finishById("wall", fin.wall).name}</b> · ceiling <b>${finishById("ceiling", fin.ceiling).name}</b>`,
    ] };
  }

  if (/\b(room|rooms|plan|house|layout|summary)\b/.test(s)) return {
    title: `${t.bedrooms} bed · ${t.baths} bath · ${Math.round(t.built)} sq ft`,
    lines: [...m.rooms].sort((a, b) => a.floor - b.floor).slice(0, 12)
      .map(r => `${r.name} — ${r.w} × ${r.h} ft${r.floor ? ", floor " + r.floor : ""}`),
    note: `Plot ${m.plot.w} × ${m.plot.h} ft · FSI ${t.fsi.toFixed(2)} · ${(t.cover * 100).toFixed(0)}% covered` };

  return null;
}

/* ---------- instructions ---------- */
export type Did = { summary: string[] } | null;

export function instruct(raw: string): Did {
  const s = norm(raw);
  const m = getModel();

  // a measured gap between two rooms
  if (/\b(apart|away|gap|distance|separate|separated|between|clear|far|from|off)\b/.test(s)) {
    const d = feetFrom(s), pair = findTwoRooms(s);
    if (d && pair && pair[0] !== pair[1]) {
      const out = setGap(pair[0], pair[1], d.ft);
      if (!out.bad) chat.saw(pair[1]);        // "it" now means the room that moved
      return { summary: [out.bad || `Moved ${pair[1].name} to sit ${d.said} (${d.ft.toFixed(1)} ft) `
                                  + `clear of ${pair[0].name}, ${(out as any).axis}.`] };
    }
  }

  if (/\b(split|divide|separate|partition|halve|into two|into three)\b/.test(s)
      && !/\b(merge|combine|join)\b/.test(s) && !feetFrom(s)) {
    // The remembered room stands in for a pronoun — "split it" — and nothing
    // else. If a room was named and not found, say so: dividing whatever was
    // mentioned last would look exactly like success.
    const named = findRoom(s);
    const asked = findType(s);
    if (!named) {
      if (asked) return { summary: [`There is no ${LABEL[asked].toLowerCase()} in this design to divide.`] };
      if (!PRONOUN.test(s)) return { summary: [
        "I could not tell which room to divide. Name it — “split the living room” — or select it first."] };
    }
    const room = named || chat.subject();
    if (!room) return null;
    const n = /\bthree\b/.test(s) ? 3 : 2;
    const after = s.split(/\binto\b/)[1] || "";
    const t = after ? findType(" " + after + " ") : null;
    const out = splitRoom(room, n, t && t !== room.type ? t : null);
    if (!out.bad) chat.saw(room);             // the room that was divided
    return { summary: [out.bad || out.summary!] };
  }

  if (/\b(merge|combine|join|knock together|open up)\b/.test(s)) {
    const pair = findTwoRooms(s);
    if (!pair) return null;
    const out = mergeRooms(pair[0], pair[1]);
    return { summary: [out.bad || out.summary!] };
  }

  // add a room, at a stated size if one was given
  if (/\b(add|another|extra|need|want|put in)\b/.test(s) && !/\b(remove|delete)\b/.test(s)) {
    const type = findType(s);
    if (type) {
      const size = sizeFrom(s);
      const id = addRoom(type, size || undefined);
      if (!id) return { summary: [`No free space on this floor for a ${LABEL[type].toLowerCase()}. `
                                + `Move something first, or add a floor.`] };
      const room = getModel().rooms.find(r => r.id === id)!;
      chat.saw(room);
      return { summary: [`Added ${room.name}, ${room.w} × ${room.h} ft`
                       + `${size ? " as asked" : " at the usual size — say a size to change it"}.`] };
    }
  }

  if (/\b(remove|delete|drop|get rid of|take out)\b/.test(s)) {
    const room = findRoom(s);
    if (room) { removeRoom(room.id); return { summary: [`Removed ${room.name}.`] }; }
  }

  // resize: "make the kitchen 3 ft wider", "kitchen 12 by 14"
  const room = findRoom(s);
  if (room) {
    const exact = sizeFrom(s);
    if (exact) {
      const [minW, minH] = minFor(room.type);
      const w = clamp(exact[0], minW, m.plot.w), h = clamp(exact[1], minH, m.plot.h);
      update(mm => { const r = mm.rooms.find(x => x.id === room.id)!; r.w = w; r.h = h; });
      return { summary: [`${room.name} set to ${w} × ${h} ft (${Math.round(w * h)} sq ft).`] };
    }
    const by = s.match(/(\d+(?:\.\d+)?)\s*(?:ft|feet|')?\s*(wider|narrower|deeper|shallower|longer|shorter|bigger|smaller)/);
    const vague = /\b(wider|bigger|larger|narrower|smaller)\b/.test(s);
    if (by || vague) {
      const step = by ? Number(by[1]) : 2;
      const word = by ? by[2] : (s.match(/\b(wider|bigger|larger|narrower|smaller)\b/)![1]);
      const grow = /wider|deeper|longer|bigger|larger/.test(word);
      const acrossW = /wider|narrower|bigger|larger|smaller/.test(word);
      const [minW, minH] = minFor(room.type);
      update(mm => {
        const r = mm.rooms.find(x => x.id === room.id)!;
        if (acrossW) r.w = clamp(r.w + (grow ? step : -step), minW, mm.plot.w - r.x);
        if (!acrossW || /bigger|larger|smaller/.test(word))
          r.h = clamp(r.h + (grow ? step : -step), minH, mm.plot.h - r.y);
      });
      const after = getModel().rooms.find(x => x.id === room.id)!;
      return { summary: [`${room.name} is now ${after.w} × ${after.h} ft (${Math.round(after.w * after.h)} sq ft).`] };
    }
  }

  // plot, budget, region
  const plot = s.match(/plot\s*(?:of|is|to)?\s*(\d{2,3})\s*(?:ft|feet|')?\s*(?:x|×|by)\s*(\d{2,3})/);
  if (plot) {
    update(mm => { mm.plot = { ...mm.plot, w: clamp(Number(plot[1]), 15, 300), h: clamp(Number(plot[2]), 15, 300) }; });
    return { summary: [`Plot set to ${getModel().plot.w} × ${getModel().plot.h} ft.`] };
  }
  const budget = s.match(/budget\s*(?:of|is|to|at)?\s*(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(lakh|l|crore|cr)?/);
  if (budget) {
    let v = Number(budget[1]);
    if (/^cr/.test(budget[2] || "")) v *= 100;
    update(mm => { mm.budget = clamp(v, 10, 500); });
    return { summary: [`Budget set to ₹${getModel().budget}L.`] };
  }
  for (const name of Object.keys(REGIONS))
    if (s.includes(" " + name.split(" ")[0].toLowerCase()) && /\b(location|region|city|in|at|move to)\b/.test(s)) {
      update(mm => { mm.brief = { ...mm.brief, region: name }; });
      return { summary: [`Rates and bylaws switched to ${name}.`] };
    }

  // finishes: "marble floor in the living room"
  const SURFACE: [("wall" | "floor" | "ceiling"), RegExp][] = [
    ["floor", /\b(floor|floors|flooring|tiles|tiling)\b/],
    ["wall", /\b(wall|walls|paint|painting)\b/],
    ["ceiling", /\b(ceiling|ceilings|false ceiling|soffit)\b/],
  ];
  for (const [kind, said] of SURFACE) {
    if (!said.test(s)) continue;
    const option = (FINISH[kind] as any[]).find(o => s.includes(" " + o.name.toLowerCase()));
    if (option && room) {
      update(mm => {
        const r = mm.rooms.find(x => x.id === room.id)!;
        r.finish = { ...(r.finish || {}), [kind]: option.id };
      });
      return { summary: [`${option.name} ${kind === "wall" ? "walls" : kind} applied to ${room.name} `
                       + `(₹${option.rate}/sq ft).`] };
    }
  }

  // furnish
  const level = s.match(/\b(essentials?|comfort|premium|basic|luxury)\b/);
  if (level && /\b(furnish|furniture|fit out|set)\b/.test(s)) {
    const want = ({ basic: "essentials", essential: "essentials", essentials: "essentials",
                    comfort: "comfort", premium: "premium", luxury: "premium" } as Record<string, string>)[level[1]];
    const target = findRoom(s);
    update(mm => {
      const rooms = target ? [mm.rooms.find(r => r.id === target.id)!] : mm.rooms;
      for (const r of rooms) E.furnishRoom(mm, r, want);
    });
    return { summary: [target ? `Furnished ${target.name} to ${want}.` : `Furnished every room to ${want}.`] };
  }

  return null;
}

/** One line in, one thing done or answered. The order matters: a question is
 *  answered rather than acted on, and a typo is fixed before either. */
export function ask(raw: string) {
  const said = raw.trim();
  chat.say("you", said);
  const fixed = spell(digitise(said) === said.toLowerCase() ? said : said);
  const ctx = resolveContext(fixed.text);
  const aside = [fixed.fixes.length ? "Read as: " + fixed.fixes.join(", ") : "", ctx.note]
    .filter(Boolean).join(" · ");

  const answer = answerQuestion(ctx.text);
  if (answer) {
    chat.say("synapse", answer.title);
    return { kind: "answer" as const, answer, aside };
  }
  const did = instruct(ctx.text);
  if (did) {
    chat.last = ctx.text;
    chat.say("synapse", did.summary.join(". "));
    chat.save();
    return { kind: "did" as const, summary: did.summary, aside };
  }
  return { kind: "lost" as const, aside };
}
