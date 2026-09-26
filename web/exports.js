/* =====================================================================
   EXPORTS
   Four formats, four audiences: IFC for the architect's BIM software, DXF
   for the draughtsman, OBJ for anyone with a 3D viewer, and a bill of
   quantities for whoever is pricing it.

   Lifted out of studio.html unchanged, because these were written against
   what the receiving software actually accepts — the IFC in particular
   chains local placements from the site and offsets its profiles so that
   IfcOpenShell can build the geometry, which a cleaner-looking rewrite from
   the entity list alone did not.

   Every function takes the model and a wallPlan(model) function, so the
   exported building is the one the 3D view drew rather than a second guess.
   ===================================================================== */
import * as E from "./engine.js";

const FLOOR_H = E.FLOOR_H, LABEL = E.LABEL, UNCONDITIONED = E.UNCONDITIONED;
/* Opening sizes, matching the ones the 3D builder cuts into the walls — a door
   that is 3.2 ft on screen has to be 3.2 ft in the IFC. */
const WALL_EXT = .75, WALL_INT = .5, DOOR_W = 3.2, DOOR_H = 7, SILL = 3, HEAD = 7;
/* The bits the old page had lying around as globals. Each is a function of
   the model, so they live here rather than being passed in from two places. */
const ratesOf = M => E.ratesFor(M);
const rulesOf = M => E.ratesFor(M).rule;
const hasFacing = M => M.plot.facing !== null && M.plot.facing !== undefined;
const dirName = deg => ["north", "north-east", "east", "south-east", "south",
                        "south-west", "west", "north-west"][Math.round(((deg % 360) + 360) % 360 / 45) % 8];

/* Every catalogue item that has been chosen, with the room it sits in — the
   contractor prices the line, so it has to say where the thing goes. */
const interiorLines = M => {
  const out = [];
  for (const [key, ids] of Object.entries(M.interiors || {})) {
    const where = key === "exterior" ? "Exterior"
                : (M.rooms.find(r => r.id === key)?.name || key);
    for (const id of ids || []) {
      const item = E.catalogById(id);
      if (item) out.push({ id, name: item.name, where, price: item.price });
    }
  }
  return out;
};

/* An indicative programme: the same stages the report shows, in weeks. */
/* An indicative programme, moved with the exporters rather than stubbed:
   the BOQ prints a payment schedule, and a schedule of nothing is a header
   over an empty table. Stage shares are a stated convention, not a
   prediction — the contractor's own programme replaces it. */
const STAGES = [["Mobilisation and foundation", .15], ["Plinth and columns", .15],
                ["Structure and roof slab", .25], ["Masonry and plaster", .15],
                ["Electrical and plumbing", .10], ["Finishes", .15],
                ["Handover and snagging", .05]];
const schedule = (t, c) => {
  const months = Math.round(E.clamp(5 + t.built / 450 + (t.floors - 1) * 2, 5, 24));
  const construction = c.total - c.interiors;
  const weeks = months * 4.3;
  let wk = 0;
  return { months, rows: STAGES.map(([name, share]) => {
    const from = Math.round(wk) + 1;
    wk += weeks * share;
    return { name, share, amount: construction * share, from, to: Math.round(wk) };
  }) };
};

const itemsFor = (M, key) => E.itemsFor(M, key);
/* A filename the operating system will not argue with. */
const fileBase = M => (M.name || "").replace(/[^\w-]+/g, "-").toLowerCase() || "synapse";
const lakh = n => "₹" + (n / 100000).toFixed(1) + "L";
const inr = n => "₹" + Math.round(n).toLocaleString("en-IN");

export function buildIfc(M, walls, deps = {}) {
  const FT = .3048, H = FLOOR_H * FT;
  const L = []; let n = 0;
  const add = s => { L.push(`#${++n}=${s};`); return `#${n}`; };
  const f = v => { let s = (+v).toFixed(4).replace(/0+$/, ""); return s.endsWith(".") ? s : s.includes(".") ? s : s + "."; };
  const C64 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
  const gid = () => "'" + C64[Math.floor(Math.random() * 4)] + Array.from({ length: 21 }, () => C64[Math.floor(Math.random() * 64)]).join("") + "'";
  const str = s => "'" + String(s).replace(/[^\x20-\x7e]/g, "").replace(/'/g, "''") + "'";
  const dz = add("IFCDIRECTION((0.,0.,1.))"), dx = add("IFCDIRECTION((1.,0.,0.))");
  const ax = (x, y, z) => add(`IFCAXIS2PLACEMENT3D(${add(`IFCCARTESIANPOINT((${f(x)},${f(y)},${f(z)}))`)},${dz},${dx})`);
  const place = (rel, x, y, z) => add(`IFCLOCALPLACEMENT(${rel},${ax(x, y, z)})`);
  const ctx = add(`IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,${ax(0, 0, 0)},$)`);
  const body = add(`IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,${ctx},$,.MODEL_VIEW.,$)`);
  const shape = (w, d, h) => {
    const prof = add(`IFCRECTANGLEPROFILEDEF(.AREA.,$,${add(`IFCAXIS2PLACEMENT2D(${add(`IFCCARTESIANPOINT((${f(w / 2)},${f(d / 2)}))`)},$)`)},${f(w)},${f(d)})`);
    const solid = add(`IFCEXTRUDEDAREASOLID(${prof},${ax(0, 0, 0)},${dz},${f(h)})`);
    return add(`IFCPRODUCTDEFINITIONSHAPE($,$,(${add(`IFCSHAPEREPRESENTATION(${body},'Body','SweptSolid',(${solid}))`)}))`);
  };
  const units = add(`IFCUNITASSIGNMENT((${add("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)")},${add("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)")},${add("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")},${add("IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.)")}))`);
  const project = add(`IFCPROJECT(${gid()},$,${str(M.name)},$,$,$,$,(${ctx}),${units})`);
  const lpSite = place("$", 0, 0, 0);
  const site = add(`IFCSITE(${gid()},$,'Site',$,$,${lpSite},$,$,.ELEMENT.,$,$,$,$,$)`);
  const lpBldg = place(lpSite, 0, 0, 0);
  const bldg = add(`IFCBUILDING(${gid()},$,${str(M.name)},$,$,${lpBldg},$,$,.ELEMENT.,$,$,$)`);
  add(`IFCRELAGGREGATES(${gid()},$,$,$,${project},(${site}))`);
  add(`IFCRELAGGREGATES(${gid()},$,$,$,${site},(${bldg}))`);
  const storeys = [];
  const floors = E.measure(M).floors, segs = walls(M);
  for (let fl = 0; fl < floors; fl++) {
    const lp = place(lpBldg, 0, 0, fl * H);
    const st = add(`IFCBUILDINGSTOREY(${gid()},$,${str(fl === 0 ? "Ground floor" : "Floor " + fl)},$,$,${lp},$,$,.ELEMENT.,${f(fl * H)})`);
    storeys.push(st);
    const contained = [], spaces = [];
    for (const r of M.rooms.filter(r => r.floor === fl)) {
      spaces.push(add(`IFCSPACE(${gid()},$,${str(r.name)},$,${str(LABEL[r.type])},${place(lp, r.x * FT, r.y * FT, 0)},${shape(r.w * FT, r.h * FT, H - .15)},$,.ELEMENT.,.INTERNAL.,$)`));
      contained.push(add(`IFCSLAB(${gid()},$,${str(r.name + " slab")},$,$,${place(lp, r.x * FT, r.y * FT, -.15)},${shape(r.w * FT, r.h * FT, .15)},$,.FLOOR.)`));
    }
    for (const s of segs.filter(s => s.floor === fl)) {
      const th = s.thick * FT, len = (s.b - s.a) * FT;
      const [wx, wy] = s.horiz ? [s.a * FT, s.coord * FT - th / 2] : [s.coord * FT - th / 2, s.a * FT];
      const wlp = place(lp, wx, wy, 0);
      const wall = add(`IFCWALL(${gid()},$,${str((s.kind === "ext" ? "External wall, " : "Internal wall, ") + s.owner.name)},$,$,${wlp},${s.horiz ? shape(len, th, H) : shape(th, len, H)},$,.STANDARD.)`);
      contained.push(wall);
      if (!s.opening) continue;
      const door = s.opening === "door";
      const ow = (door ? (s.main ? DOOR_W + .8 : DOOR_W) : Math.min((s.b - s.a) * .46, 7.5)) * FT;
      const sill = door ? 0 : 3 * FT, oh = (door ? 7 : 4) * FT;
      const off = ((s.a + s.b) / 2) * FT - s.a * FT - ow / 2;
      const [ox, oy, w, d] = s.horiz ? [off, -.05, ow, th + .1] : [-.05, off, th + .1, ow];
      const olp = place(wlp, ox, oy, sill);
      const opening = add(`IFCOPENINGELEMENT(${gid()},$,'Opening',$,$,${olp},${shape(w, d, oh)},$,.OPENING.)`);
      add(`IFCRELVOIDSELEMENT(${gid()},$,$,$,${wall},${opening})`);
      const [fx, fy, fw, fd] = s.horiz ? [0, .05 + th / 2 - .025, ow, .05] : [.05 + th / 2 - .025, 0, .05, ow];
      const flp = place(olp, fx, fy, 0);
      const fill = door
        ? add(`IFCDOOR(${gid()},$,${str(s.main ? "Main door" : "Door")},$,$,${flp},${shape(fw, fd, oh)},$,${f(oh)},${f(ow)},.DOOR.,.SINGLE_SWING_LEFT.,$)`)
        : add(`IFCWINDOW(${gid()},$,'Window',$,$,${flp},${shape(fw, fd, oh)},$,${f(oh)},${f(ow)},.WINDOW.,.SINGLE_PANEL.,$)`);
      add(`IFCRELFILLSELEMENT(${gid()},$,$,$,${opening},${fill})`);
      contained.push(fill);
    }
    if (spaces.length) add(`IFCRELAGGREGATES(${gid()},$,$,$,${st},(${spaces.join(",")}))`);
    if (contained.length) add(`IFCRELCONTAINEDINSPATIALSTRUCTURE(${gid()},$,$,$,(${contained.join(",")}),${st})`);
  }
  add(`IFCRELAGGREGATES(${gid()},$,$,$,${bldg},(${storeys.join(",")}))`);
  const now = new Date().toISOString().slice(0, 19);
  return ["ISO-10303-21;", "HEADER;",
    "FILE_DESCRIPTION(('ViewDefinition [DesignTransferView]'),'2;1');",
    `FILE_NAME(${str(fileBase(M) + ".ifc")},'${now}',(''),(''),'Synapse Studio','Synapse Studio','');`,
    "FILE_SCHEMA(('IFC4'));", "ENDSEC;", "DATA;", ...L, "ENDSEC;", "END-ISO-10303-21;"].join("\n");
}

export function buildDxf(M, walls, deps = {}) {
  const P = M.plot, o = [];
  const put = (...a) => o.push(...a.map(String));
  const poly = (layer, pts, dx) => { put(0,"POLYLINE",8,layer,66,1,70,1,10,0,20,0,30,0);
    for (const [x, y] of pts) put(0,"VERTEX",8,layer,10,(x + dx).toFixed(3),20,y.toFixed(3),30,0); put(0,"SEQEND",8,layer); };
  const line = (layer, x1, y1, x2, y2) => put(0,"LINE",8,layer,10,x1.toFixed(3),20,y1.toFixed(3),30,0,11,x2.toFixed(3),21,y2.toFixed(3),31,0);
  const text = (layer, x, y, h, s) => put(0,"TEXT",8,layer,10,x.toFixed(3),20,y.toFixed(3),30,0,40,h,1,s);
  const rect = (x, y, w, h) => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
  put(0,"SECTION",2,"HEADER",9,"$ACADVER",1,"AC1009",9,"$INSUNITS",70,2,0,"ENDSEC");
  put(0,"SECTION",2,"ENTITIES");
  const floors = E.measure(M).floors;
  for (let f = 0; f < floors; f++) {
    const dx = f * (P.w + 20), L = `F${f}`;
    poly("PLOT", rect(0, 0, P.w, P.h), dx);
    poly("SETBACK", rect(rulesOf(M).side, rulesOf(M).front, P.w - 2*rulesOf(M).side, P.h - rulesOf(M).front - rulesOf(M).rear), dx);
    text("TEXT", dx, -4, 1.5, f === 0 ? "GROUND FLOOR" : `FLOOR ${f}`);
    text("TEXT", dx + P.w/2 - 2, -1.8, 1, "ROAD" + (hasFacing(M) ? ` (faces ${dirName(P.facing)})` : ""));
    for (const r of M.rooms.filter(r => r.floor === f)) {
      poly(`${L}_ROOMS`, rect(r.x, r.y, r.w, r.h), dx);
      text(`${L}_TEXT`, dx + r.x + .8, r.y + r.h/2, .9, `${r.name} ${r.w}x${r.h}`);
    }
    for (const s of walls(M).filter(s => s.floor === f && s.opening)) {
      const m = (s.a + s.b) / 2, D = s.opening === "door" ? (s.main ? DOOR_W + .8 : DOOR_W) : Math.min((s.b - s.a) * .46, 7.5);
      const lay = `${L}_${s.opening === "door" ? "DOORS" : "WINDOWS"}`;
      if (s.horiz) line(lay, dx + m - D/2, s.coord, dx + m + D/2, s.coord);
      else line(lay, dx + s.coord, m - D/2, dx + s.coord, m + D/2);
    }
  }
  put(0,"ENDSEC",0,"EOF");
  return o.join("\r\n");
}

export function buildBoq(M, walls, deps = {}) {
  const t = E.measure(M), c = E.cost(M, t), sch = schedule(t, c);
  const q = v => `"${String(v).replace(/"/g, '""')}"`;
  const rows = [["Code","Item","Unit","Quantity","Rate","Amount","Basis"]];
  for (const l of E.costLines(M, t))
    rows.push([l.code, l.item, l.unit, l.unit === "LS" ? 1 : Math.round(l.qty * 10) / 10, Math.round(l.rate), Math.round(l.amount), l.basis]);
  rows.push(["OH", "Overheads", "%", ratesOf(M).overhead_pct, "", Math.round(c.oh), ""]);
  rows.push(["CT", "Contingency", "%", ratesOf(M).contingency_pct, "", Math.round(c.cont), ""]);
  for (const i of interiorLines(M)) rows.push([i.id, `${i.name} (${i.where})`, "nos", 1, i.price, i.price, "Catalogue allowance"]);
  rows.push(["", "TOTAL", "", "", "", Math.round(c.total), ""], []);
  rows.push(["Stage","Weeks","Share","Payment"]);
  for (const s of sch.rows) rows.push([s.name, `${s.from}-${s.to}`, `${Math.round(s.share*100)}%`, Math.round(s.amount)]);
  return rows.map(r => r.map(q).join(",")).join("\r\n");
}

export function buildObj(M, walls, deps = {}) {
  const FT = .3048, P = M.plot, cx = P.w/2, cz = P.h/2;
  const out = ["# Synapse Studio massing export", "# units: metres", ""];
  let v = 1;
  for (const r of M.rooms) {
    const h = FLOOR_H * (UNCONDITIONED.has(r.type) ? .62 : .92);
    const x0=(r.x-cx)*FT, x1=(r.x+r.w-cx)*FT, z0=(r.y-cz)*FT, z1=(r.y+r.h-cz)*FT;
    const y0=r.floor*FLOOR_H*FT, y1=y0+h*FT;
    out.push(`g ${r.name.replace(/\s+/g,"_")}_F${r.floor}`);
    for (const p of [[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1],[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]])
      out.push(`v ${p[0].toFixed(4)} ${p[1].toFixed(4)} ${p[2].toFixed(4)}`);
    for (const f of [[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]])
      out.push(`f ${v+f[0]} ${v+f[1]} ${v+f[2]} ${v+f[3]}`);
    v += 8; out.push("");
  }
  return out.join("\n");
}
