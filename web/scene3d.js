/* =====================================================================
   THE HOUSE, IN THREE DIMENSIONS
   Lifted out of studio.html so the React studio and the original page build
   the same building — walls that know where their openings are, modelled
   furniture, fittings, skirting, and stairs with a ramp the camera climbs.

   It is a factory rather than a module of globals: hand it THREE and the
   engine, and it hands back build(model, options). Nothing in here reads the
   page, so the same call works from React, from the old page, and from a
   test with no DOM at all beyond a canvas.

       const builder = createBuilder(THREE, E);
       const { group, colliders, stairZones, spinners } = builder.build(model, {
         furniture: true, roof: false, walking: false, selected: "bed_1",
       });

   The caller owns the scene and the camera, and disposes of what it replaces.
   ===================================================================== */

export function createBuilder(THREE, E) {
  const { FLOOR_H, OPENING, UNCONDITIONED, finishById, finishOf, LABEL } = E;
  const WALLED = type => !UNCONDITIONED.has(type);
  /* The model being built right now. Set once at the top of build() and read
     by the helpers below, which were written as page-level functions and are
     kept that way so the geometry is line-for-line what it was. */
  let CUR = null;      // the model being built
  let SHELL = null;    // the group it is being built into
  const itemsFor = key => E.itemsFor(CUR, key);
  const hasItem = (key, id) => E.hasItem(CUR, key, id);
  const ext = id => E.hasItem(CUR, "exterior", id);

  /* Procedural finishes are expensive to draw and identical between rebuilds,
     so each one is drawn once and kept. */
  const texCache = new Map();

  function makeTexture(kind, color) {
    const key = kind + ":" + color;
    if (texCache.has(key)) return texCache.get(key);
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d");
    const hex = "#" + color.toString(16).padStart(6, "0");
    g.fillStyle = hex; g.fillRect(0, 0, 256, 256);

    const noise = (n, a) => {
      for (let i = 0; i < n; i++) {
        g.fillStyle = `rgba(0,0,0,${Math.random() * a})`;
        g.fillRect(Math.random()*256, Math.random()*256, 2, 2);
      }
    };
    switch (kind) {
      case "tile":
        g.strokeStyle = "rgba(0,0,0,.18)"; g.lineWidth = 3;
        for (let i = 0; i <= 256; i += 64) {
          g.beginPath(); g.moveTo(i,0); g.lineTo(i,256); g.stroke();
          g.beginPath(); g.moveTo(0,i); g.lineTo(256,i); g.stroke();
        }
        noise(260, .05); break;
      case "wood":
        for (let y = 0; y < 256; y += 5) {
          g.fillStyle = `rgba(0,0,0,${0.03 + Math.random()*0.07})`;
          g.fillRect(0, y, 256, 1 + Math.random()*2);
        }
        g.strokeStyle = "rgba(0,0,0,.14)"; g.lineWidth = 2;
        for (let x = 0; x <= 256; x += 85) { g.beginPath(); g.moveTo(x,0); g.lineTo(x,256); g.stroke(); }
        break;
      case "marble":
        g.strokeStyle = "rgba(120,120,130,.4)";
        for (let i = 0; i < 9; i++) {
          g.lineWidth = .6 + Math.random()*1.8;
          g.beginPath();
          let x = Math.random()*256, y = 0;
          g.moveTo(x, y);
          while (y < 256) { x += (Math.random()-.5)*40; y += 16; g.lineTo(x, y); }
          g.stroke();
        }
        noise(120, .04); break;
      case "granite":
        for (let i = 0; i < 2600; i++) {
          const v = Math.random();
          g.fillStyle = v > .5 ? `rgba(255,255,255,${v*.35})` : `rgba(0,0,0,${v*.5})`;
          g.fillRect(Math.random()*256, Math.random()*256, 2.2, 2.2);
        }
        break;
      case "stone":
        g.strokeStyle = "rgba(0,0,0,.28)"; g.lineWidth = 3;
        for (let row = 0, y = 0; y <= 256; y += 42, row++) {
          g.beginPath(); g.moveTo(0,y); g.lineTo(256,y); g.stroke();
          const off = row % 2 ? 42 : 0;
          for (let x = off; x <= 256; x += 84) {
            g.beginPath(); g.moveTo(x,y); g.lineTo(x,y+42); g.stroke();
          }
        }
        noise(400, .06); break;
      case "paper":
        g.strokeStyle = "rgba(0,0,0,.07)"; g.lineWidth = 2;
        for (let x = 0; x <= 256; x += 16) { g.beginPath(); g.moveTo(x,0); g.lineTo(x,256); g.stroke(); }
        break;
      default: noise(500, .05);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = 4;
    texCache.set(key, t);
    return t;
  }

  function finishMaterial(f, repeatX, repeatY) {
    const tex = makeTexture(f.tex, f.color).clone();
    tex.needsUpdate = true;
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(Math.max(repeatX, .4), Math.max(repeatY, .4));
    return new THREE.MeshLambertMaterial({ map: tex });
  }

  /* =====================================================================
     3D
     ===================================================================== */
  let renderer, scene, camera, controls, walkControls, shell, sun,
      ray, ptr, live = false, ready3d = false, dirty3d = true, walking = false;
  let drag3d = null;
  const groundPlane = new THREE.Plane(new THREE.Vector3(0,1,0), 0);
  const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  const { WALL_EXT, WALL_INT, DOOR_W, DOOR_H, SILL, HEAD, EYE } = E;
  let colliders = [];     // wall AABBs for the walkthrough
  let stairZones = [];    // ramp volumes the player can climb
  let spinners = [];      // ceiling fans, turned by the render loop

  function box(w, h, d, x, y, z, mat, cast = true) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = cast; m.receiveShadow = true;
    return m;
  }

  const GLASS = new THREE.MeshLambertMaterial({
    color:0xbcd4dc, transparent:true, opacity:.34, depthWrite:false });
  const FRAME = new THREE.MeshLambertMaterial({ color:0x574a3c });
  const DOORLEAF = new THREE.MeshLambertMaterial({ color:0x8a6a48 });
  const MAINDOOR = new THREE.MeshLambertMaterial({ color:0x5a3d28 });
  const CHAJJA = new THREE.MeshLambertMaterial({ color:0xd4cfc6 });

  /* ---------- walls ----------
     One straight run of wall, optionally punched with a door or a window, with
     the leaf or the glass in the hole. `faces` lets each side of the wall wear a
     different material — a shared wall shows the bedroom's paint on the bedroom
     side and the bathroom's tile on the other; an exterior wall shows the facade
     outside and the room's finish inside. BoxGeometry faces are ordered
     +x, -x, +y, -y, +z, -z. */
  const FACE = { "+x":0, "-x":1, "+z":4, "-z":5 };
  function wallRun(group, ax, az, bx, bz, thick, mat, opening, baseY, opts = {}) {
    const horiz = Math.abs(bx - ax) > Math.abs(bz - az);
    const len = horiz ? Math.abs(bx - ax) : Math.abs(bz - az);
    if (len < .2) return;
    const midX = (ax + bx) / 2, midZ = (az + bz) / 2, H = FLOOR_H;
    let m = mat;
    if (opts.faces) {
      m = [mat, mat, mat, mat, mat, mat];
      for (const [k, v] of Object.entries(opts.faces)) if (v && k in FACE) m[FACE[k]] = v;
    }

    const seg = (from, to, y0, y1) => {
      const L = to - from;
      if (L <= .05 || y1 - y0 <= .05) return;
      const off = from + L/2 - len/2;
      const w = box(horiz ? L : thick, y1-y0, horiz ? thick : L,
                    horiz ? midX+off : midX, baseY + (y0+y1)/2, horiz ? midZ : midZ+off, m);
      group.add(w);
      if (y0 < EYE + 1.2 && y1 > 0.2)
        colliders.push({ x:w.position.x, z:w.position.z,
                         hw:(horiz ? L : thick)/2, hd:(horiz ? thick : L)/2,
                         y0: baseY, y1: baseY + H });
    };

    if (!opening || len < DOOR_W + 1.4) { seg(0, len, 0, H); return; }

    if (opening === "door") {
      const dw = opts.main ? DOOR_W + .8 : DOOR_W;
      const a = len/2 - dw/2, b = a + dw;
      seg(0, a, 0, H); seg(b, len, 0, H); seg(a, b, DOOR_H, H);
      const hinge = new THREE.Group();
      hinge.position.set(horiz ? midX - dw/2 : midX, baseY, horiz ? midZ : midZ - dw/2);
      const leaf = horiz
        ? box(dw, DOOR_H - .2, .18, dw/2, (DOOR_H - .2)/2, 0, opts.main ? MAINDOOR : DOORLEAF)
        : box(.18, DOOR_H - .2, dw, 0, (DOOR_H - .2)/2, dw/2, opts.main ? MAINDOOR : DOORLEAF);
      hinge.add(leaf);
      hinge.rotation.y = (horiz ? -1 : 1) * (opts.main ? 1.05 : .62);
      group.add(hinge);
    } else {
      const winW = Math.min(len * .46, 7.5);
      const a = len/2 - winW/2, b = a + winW;
      seg(0, a, 0, H); seg(b, len, 0, H);
      seg(a, b, 0, SILL); seg(a, b, HEAD, H);
      group.add(box(horiz ? winW : .1, HEAD - SILL, horiz ? .1 : winW,
                    midX, baseY + (SILL+HEAD)/2, midZ, GLASS, false));
      const fT = .22;
      group.add(box(horiz ? winW : fT, fT, horiz ? fT : winW, midX, baseY + SILL, midZ, FRAME));
      group.add(box(horiz ? winW : fT, fT, horiz ? fT : winW, midX, baseY + HEAD, midZ, FRAME));
      group.add(box(horiz ? fT : fT, HEAD - SILL, horiz ? fT : fT,
                    horiz ? midX : midX, baseY + (SILL+HEAD)/2, horiz ? midZ : midZ, FRAME)); // mullion
      if (opts.chajja && opts.outward) {
        // a chajja sunshade: a thin concrete shelf over the window, on the outside
        const sgn = opts.outward[0] === "+" ? 1 : -1, off = thick/2 + 1;
        const x = horiz ? midX : midX + sgn*off, z = horiz ? midZ + sgn*off : midZ;
        group.add(box(horiz ? winW + 1.6 : 2, .3, horiz ? 2 : winW + 1.6,
                      x, baseY + HEAD + .45, z, CHAJJA));
      }
    }
  }

  /* ---------- which rooms open into which ----------
     Hubs (living, dining, stairs) open into almost anything; beyond that only
     pairs a real house connects. A bedroom does not open into the kitchen. */

  const HUB = new Set(["living", "dining", "stairs"]);
  const PAIRS = new Set(["bath|bedroom", "balcony|bedroom", "dining|kitchen", "kitchen|utility",
                         "bedroom|office", "balcony|living", "balcony|office"]);
  function connects(a, b) {
    if (a === "parking" || b === "parking") return false;
    const k = [a, b].sort().join("|");
    if (k === "bath|stairs" || k === "bath|kitchen" || k === "bath|dining") return false;
    if (HUB.has(a) || HUB.has(b)) return true;
    return PAIRS.has(k);
  }

  /* ---------- wall plan ----------
     Partition every room edge into the stretches shared with a neighbour and
     the stretches that face outside. Each shared stretch becomes ONE wall, owned
     by one room, with a door if the two rooms connect. Exterior stretches get
     windows. Then: a main entrance on the living room's front, and a door for
     any room left with none, so nothing is sealed off. Used by the 3D builder
     and the 2D door and window symbols, so the two always agree. */
  const TOL = 1.2;
  let wallPlanCache = { key:"", segs:[] };
  function wallPlan(M = CUR) {
    const key = JSON.stringify(M.rooms.map(r => [r.id, r.type, r.floor, r.x, r.y, r.w, r.h]));
    if (wallPlanCache.key === key) return wallPlanCache.segs;

    const rooms = M.rooms, segs = [];
    const doors = new Map(rooms.map(r => [r.id, 0]));
    const paired = new Set();
    const sides = r => [
      { s:"n", horiz:true,  coord:r.y,       a:r.x, b:r.x + r.w, out:"-z", opp:"s" },
      { s:"s", horiz:true,  coord:r.y + r.h, a:r.x, b:r.x + r.w, out:"+z", opp:"n" },
      { s:"w", horiz:false, coord:r.x,       a:r.y, b:r.y + r.h, out:"-x", opp:"e" },
      { s:"e", horiz:false, coord:r.x + r.w, a:r.y, b:r.y + r.h, out:"+x", opp:"w" }];
    const edgeOf = (q, s) => sides(q).find(e => e.s === s);
    const bump = id => doors.set(id, (doors.get(id) || 0) + 1);

    for (const r of rooms) {
      if (!WALLED(r.type)) continue;
      for (const e of sides(r)) {
        const shared = [];
        for (const q of rooms) {
          if (q === r || q.floor !== r.floor) continue;
          const qe = edgeOf(q, e.opp);
          if (Math.abs(qe.coord - e.coord) > TOL) continue;
          const a = Math.max(e.a, qe.a), b = Math.min(e.b, qe.b);
          if (b - a < .8) continue;
          shared.push({ a, b, q, coord:(e.coord + qe.coord) / 2 });
        }
        shared.sort((m, n) => m.a - n.a);
        const pieces = [];
        let cur = e.a;
        for (const sh of shared) {
          if (sh.a > cur + .05) pieces.push({ a:cur, b:sh.a, ext:true, coord:e.coord });
          if (sh.b > cur) pieces.push({ a:Math.max(sh.a, cur), b:sh.b, ext:false, q:sh.q, coord:sh.coord });
          cur = Math.max(cur, sh.b);
        }
        if (e.b > cur + .05) pieces.push({ a:cur, b:e.b, ext:true, coord:e.coord });

        for (const p of pieces) {
          if (p.b - p.a < .2) continue;
          if (!p.ext) {
            const q = p.q;
            if (WALLED(q.type) && q.id < r.id) continue;      // the other room draws it
            const pk = [r.id, q.id].sort().join("|");
            let opening = null;
            if (!paired.has(pk) && connects(r.type, q.type) && p.b - p.a >= DOOR_W + 1.4) {
              opening = "door"; paired.add(pk); bump(r.id); bump(q.id);
            }
            segs.push({ floor:r.floor, horiz:e.horiz, coord:p.coord, a:p.a, b:p.b,
                        owner:r, other:q, kind:"shared", opening, thick:WALL_INT, side:e.s });
          } else {
            const windowOk = !["utility"].includes(r.type) && p.b - p.a >= 5;
            segs.push({ floor:r.floor, horiz:e.horiz, coord:p.coord, a:p.a, b:p.b,
                        owner:r, other:null, kind:"ext", opening: windowOk ? "window" : null,
                        thick:WALL_EXT, outward:e.out, side:e.s });
          }
        }
      }
    }

    // The front door: the living room's exterior run nearest the road (lowest y).
    for (const L of rooms.filter(r => r.type === "living" && r.floor === 0)) {
      const cand = segs.filter(s => s.owner === L && s.kind === "ext" && s.b - s.a >= DOOR_W + 2.2)
                       .sort((m, n) => (m.horiz ? m.coord : 1e3) - (n.horiz ? n.coord : 1e3));
      if (cand[0]) { cand[0].opening = "door"; cand[0].main = true; bump(L.id); }
    }
    // No sealed rooms: longest shared run first, then the longest exterior one.
    for (const r of rooms) {
      if (!WALLED(r.type) || doors.get(r.id) > 0) continue;
      const mine = segs.filter(s => (s.owner === r || s.other === r) && s.b - s.a >= DOOR_W + 1.4);
      const byLen = (m, n) => (n.b - n.a) - (m.b - m.a);
      const pick = mine.filter(s => s.kind === "shared").sort(byLen)[0] || mine.sort(byLen)[0];
      if (pick) { pick.opening = "door"; bump(r.id); if (pick.other) bump(pick.other.id); }
    }

    wallPlanCache = { key, segs };
    return segs;
  }
  const doorCount = () => wallPlan().filter(s => s.opening === "door").length;

  /* ---------- furniture placement ----------
     Each catalogue item has a footprint and an anchor (n, s, e, w, corners,
     centre) inside its room. Items that would collide with something already
     placed are still priced but not drawn, and the panel says so — better than
     stacking a bathtub through a basin. */
  function placeItems(r) {
    const placed = [], skipped = [];
    const hit = (a, b) => !(a.x + a.w/2 <= b.x - b.w/2 || b.x + b.w/2 <= a.x - a.w/2 ||
                            a.y + a.d/2 <= b.y - b.d/2 || b.y + b.d/2 <= a.y - a.d/2);
    for (const it of itemsFor(r.id)) {
      if (it.counter) {
        const d = 2.1, h = 3;
        placed.push({ it, x:r.x + r.w/2, y:r.y + .35 + d/2, w:Math.max(r.w - .7, 1), d, h });
        placed.push({ it, x:r.x + .35 + d/2, y:r.y + d + (r.h - d)/2 + .1,
                      w:d, d:Math.max(r.h - d - 1.3, 1), h });
        continue;
      }
      if (!it.fp) continue;
      let [w, d, h] = it.fp;
      w = Math.min(w, r.w - .9); d = Math.min(d, r.h - .9);
      if (w <= .4 || d <= .4) { skipped.push(it); continue; }
      const m = .45;
      const L = r.x + m + w/2, R = r.x + r.w - m - w/2, T = r.y + m + d/2, B = r.y + r.h - m - d/2;
      const CX = r.x + r.w/2, CY = r.y + r.h/2;
      const [x, y] = ({ c:[CX,CY], n:[CX,T], s:[CX,B], w:[L,CY], e:[R,CY],
                        nw:[L,T], ne:[R,T], sw:[L,B], se:[R,B] })[it.at] || [CX, CY];
      const cand = { it, x, y, w, d, h };
      if (it.tone !== "rug" && placed.some(p => p.it.tone !== "rug" && hit(p, cand))) { skipped.push(it); continue; }
      placed.push(cand);
    }
    return { placed, skipped };
  }

  /* ---------- furniture in 3D ---------- */
  const TONE = {
    soft: 0x8b8578, wood: 0x8a6a48, white: 0xe8e6e0, rug: 0xb49a7a, plant: 0x5d7a4f,
    brass: 0xb08d3f
  };
  /* ---------- furniture, modelled rather than boxed ----------
     Every piece is built in its own local frame — origin on the floor, +z the
     way it faces — then rotated to the wall it was anchored against. A sofa
     gets arms, cushions and legs; a bed gets a mattress, a duvet and pillows;
     a WC gets a cistern and a seat. Small parts, but they are what makes a
     walkthrough read as a room instead of a diagram. */
  const FMAT = () => ({
    fabric:  new THREE.MeshLambertMaterial({ color:0x8d8578 }),
    fabric2: new THREE.MeshLambertMaterial({ color:0xa39a8b }),
    wood:    new THREE.MeshLambertMaterial({ color:0x8a6a48 }),
    wood2:   new THREE.MeshLambertMaterial({ color:0x6f5438 }),
    white:   new THREE.MeshLambertMaterial({ color:0xeceae4 }),
    ceramic: new THREE.MeshLambertMaterial({ color:0xf4f3ef }),
    metal:   new THREE.MeshLambertMaterial({ color:0x9aa0a6 }),
    dark:    new THREE.MeshLambertMaterial({ color:0x2b2b2e }),
    brass:   new THREE.MeshLambertMaterial({ color:0xb08d3f }),
    leaf:    new THREE.MeshLambertMaterial({ color:0x5d7a4f }),
    terra:   new THREE.MeshLambertMaterial({ color:0xa8623f }),
    glass:   GLASS,
  });

  /* local-space helpers: y is measured up from the floor */
  const fb = (g, w, h, d, x, y, z, m, cast = true) => { g.add(box(w, h, d, x, y + h / 2, z, m, cast)); };
  const fcyl = (g, r, h, x, y, z, m, seg = 12, rot) => {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), m);
    c.position.set(x, y + h / 2, z); if (rot) c.rotation.set(rot[0] || 0, rot[1] || 0, rot[2] || 0);
    c.castShadow = true; g.add(c);
  };
  const fsph = (g, r, x, y, z, m, squash = 1) => {
    const s = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 10), m);
    s.position.set(x, y + r * squash, z); s.scale.y = squash; s.castShadow = true; g.add(s);
  };
  const legs = (g, W, D, h, m, inset = .18) => {
    for (const sx of [-1, 1]) for (const sz of [-1, 1])
      fb(g, .16, h, .16, sx * (W / 2 - inset), 0, sz * (D / 2 - inset), m);
  };
  const handles = (g, n, W, h, z, m) => {
    for (let i = 0; i < n; i++)
      fcyl(g, .045, Math.min(.9, W / n * .5), -W / 2 + W * (i + .5) / n + (i % 2 ? -.18 : .18), h, z, m, 8, [0, 0, Math.PI / 2]);
  };

  /* one builder per kind of thing; `k` picks it from the catalogue id */
  function buildPiece(g, kind, W, D, H, M, it) {
    switch (kind) {
      case "sofa": {
        const armW = Math.min(.55, W * .12), seatH = H * .42, backH = H;
        fb(g, W, seatH * .55, D, 0, .28, 0, M.fabric);                                  // base
        fb(g, W, backH - seatH, .42, 0, seatH, -D / 2 + .21, M.fabric2);                // backrest
        for (const s of [-1, 1]) fb(g, armW, seatH * 1.25, D - .3, s * (W / 2 - armW / 2), .28, .1, M.fabric2);
        const n = Math.max(2, Math.round(W / 2.6)), cw = (W - armW * 2 - .2) / n;
        for (let i = 0; i < n; i++) {                                                   // seat cushions
          fb(g, cw - .1, .32, D - .7, -W / 2 + armW + .1 + cw * (i + .5), seatH * .55 + .28, .12, M.fabric);
          fb(g, cw - .35, .5, .22, -W / 2 + armW + .1 + cw * (i + .5), seatH + .1, -D / 2 + .42, M.fabric); // back cushion
        }
        legs(g, W, D, .28, M.wood2, .3);
        break;
      }
      case "chair": {
        fb(g, W, .18, D, 0, H * .42, 0, M.fabric);
        fb(g, W, H * .5, .14, 0, H * .42 + .18, -D / 2 + .07, M.fabric2);
        legs(g, W, D, H * .42, M.wood2, .12);
        break;
      }
      case "table": {
        const topH = .14;
        fb(g, W, topH, D, 0, H - topH, 0, M.wood);
        fb(g, W - .5, .18, D - .5, 0, H - topH - .2, 0, M.wood2);                        // apron
        legs(g, W, D, H - topH - .2, M.wood2);
        if (it.chairs) {
          const n = Math.max(2, Math.round(W / 2.2));
          for (const s of [-1, 1]) for (let i = 0; i < n; i++) {
            const cg = new THREE.Group();
            cg.position.set(-W / 2 + W * (i + .5) / n, 0, s * (D / 2 + .75));
            cg.rotation.y = s > 0 ? Math.PI : 0;
            buildPiece(cg, "chair", 1.35, 1.35, 2.9, M, {});
            g.add(cg);
          }
        }
        break;
      }
      case "desk": {
        fb(g, W, .12, D, 0, H - .12, 0, M.wood);
        fb(g, W * .38, H - .3, D - .25, W / 2 - W * .19, 0, .05, M.wood2);               // drawer pedestal
        handles(g, 3, W * .3, H * .55, D / 2 - .06, M.metal);
        fb(g, .12, H - .2, .12, -W / 2 + .2, 0, D / 2 - .2, M.wood2);
        fb(g, .12, H - .2, .12, -W / 2 + .2, 0, -D / 2 + .2, M.wood2);
        break;
      }
      case "storage": {                                                                  // wardrobe, crockery, tall unit
        fb(g, W, H, D, 0, 0, 0, M.wood);
        const doors = Math.max(2, Math.round(W / 2.2));
        for (let i = 0; i < doors; i++)                                                  // door faces, slightly proud
          fb(g, W / doors - .06, H - .2, .06, -W / 2 + W * (i + .5) / doors, .1, D / 2 + .01, M.wood2);
        handles(g, doors, W, H * .5, D / 2 + .08, M.metal);
        fb(g, W - .1, .12, D - .06, 0, 0, 0, M.dark);                                     // plinth shadow
        break;
      }
      case "shelf": {
        fb(g, .12, H, D, -W / 2 + .06, 0, 0, M.wood2);
        fb(g, .12, H, D, W / 2 - .06, 0, 0, M.wood2);
        fb(g, W, .1, D, 0, H - .1, 0, M.wood2);
        const tiers = Math.max(2, Math.round(H / 1.5));
        for (let i = 1; i < tiers; i++) {
          const y = H * i / tiers;
          fb(g, W - .24, .09, D - .1, 0, y, 0, M.wood);
          const books = Math.max(3, Math.round(W / .5));                                  // a few spines
          for (let b = 0; b < books; b++) {
            if ((b * 7 + i * 3) % 4 === 0) continue;
            const bh = .55 + ((b * 13 + i) % 5) * .07;
            const col = [0x7d5a44, 0x5a6b53, 0x8d6b6b, 0x4f5a63, 0xb08d3f][(b + i) % 5];
            fb(g, W / books * .8, bh, D * .55, -W / 2 + .12 + (W - .24) * (b + .5) / books,
               y + .09, 0, new THREE.MeshLambertMaterial({ color: col }), false);
          }
        }
        break;
      }
      case "tv": {                                                                        // console + screen + soundbar
        fb(g, W, H * .75, D, 0, 0, 0, M.wood);
        handles(g, 2, W, H * .4, D / 2 + .06, M.metal);
        const sw = Math.min(W * .95, 5), sh = sw * .56;
        fb(g, sw, sh, .09, 0, H + .55, -D / 2 + .06, M.dark);
        fb(g, sw - .12, sh - .12, .02, 0, H + .61, -D / 2 + .11, new THREE.MeshLambertMaterial({ color:0x11161c }), false);
        fb(g, sw * .5, .12, .18, 0, H + .3, -D / 2 + .1, M.dark, false);
        break;
      }
      case "bed": {
        const frameH = .85, matH = .62;
        fb(g, W, frameH, D, 0, 0, 0, M.wood2);
        fb(g, W - .24, matH, D - .3, 0, frameH, .1, M.white);                              // mattress
        fb(g, W - .24, .18, (D - .3) * .62, 0, frameH + matH, .45, M.fabric);              // duvet fold
        for (const s of [-1, 1])                                                           // pillows
          fb(g, W * .38, .28, .95, s * W * .22, frameH + matH, -D / 2 + .85, M.white);
        fb(g, W + .2, 3.1, .22, 0, 0, -D / 2 - .05, M.fabric2);                            // headboard
        for (const s of [-1, 1]) {                                                         // side tables + lamps
          fb(g, 1.25, 1.6, 1.15, s * (W / 2 + .75), 0, -D / 2 + .55, M.wood);
          fcyl(g, .12, .5, s * (W / 2 + .75), 1.6, -D / 2 + .55, M.metal, 8);
          const shade = new THREE.Mesh(new THREE.CylinderGeometry(.34, .26, .5, 12), M.white);
          shade.position.set(s * (W / 2 + .75), 2.35, -D / 2 + .55); g.add(shade);
        }
        break;
      }
      case "wc": {
        fb(g, W * .75, 1.55, D * .42, 0, .55, -D / 2 + D * .21, M.ceramic);                // cistern
        fcyl(g, W * .33, .5, 0, 1.05, .1, M.ceramic, 14);                                  // bowl
        fb(g, W * .68, .5, D * .55, 0, .55, .12, M.ceramic);
        fcyl(g, W * .34, .09, 0, 1.55, .1, M.white, 14);                                   // seat
        break;
      }
      case "basin": {
        fb(g, W, .16, D, 0, 2.5, 0, M.wood2);                                              // counter
        fb(g, W - .2, 1.1, D - .12, 0, 1.35, 0, M.wood);                                    // vanity
        handles(g, 2, W - .4, 1.8, D / 2 + .06, M.metal);
        fcyl(g, Math.min(W, D) * .3, .34, 0, 2.66, 0, M.ceramic, 16);                       // bowl
        fcyl(g, .05, .75, 0, 2.66, -D / 2 + .16, M.metal, 8);                               // tap
        fb(g, .06, .06, .32, 0, 3.3, -D / 2 + .3, M.metal, false);
        fb(g, W * .8, 1.5, .05, 0, 3.5, -D / 2 + .04, M.glass, false);                       // mirror
        break;
      }
      case "shower": {
        fb(g, W, .2, D, 0, 0, 0, M.ceramic);                                                 // tray
        fb(g, W, H - .2, .06, 0, .2, -D / 2, M.glass, false);
        fb(g, .06, H - .2, D, -W / 2, .2, 0, M.glass, false);
        fcyl(g, .07, 3.2, -W / 2 + .35, H - 3.4, -D / 2 + .3, M.metal, 8);
        fcyl(g, .42, .1, -W / 2 + .35, H - .45, -D / 2 + .62, M.metal, 14);                  // rose
        break;
      }
      case "tub": {
        fb(g, W, H, D, 0, 0, 0, M.ceramic);
        fb(g, W - .5, H * .55, D - .45, 0, H * .45 + .02, 0, new THREE.MeshLambertMaterial({ color:0xdfe7ea }), false);
        fcyl(g, .05, .55, -W / 2 + .4, H, -D / 2 + .3, M.metal, 8);
        break;
      }
      case "appliance": {                                                                    // fridge, washer, dryer
        fb(g, W, H, D, 0, 0, 0, M.white);
        fb(g, W - .08, H * .55, .05, 0, H * .44, D / 2 + .02, new THREE.MeshLambertMaterial({ color:0xdcdcd8 }), false);
        fcyl(g, W * .26, .06, 0, H * .45, D / 2 + .05, M.metal, 16, [Math.PI / 2, 0, 0]);     // drum door
        fcyl(g, .05, H * .5, W / 2 - .18, H * .3, D / 2 + .08, M.metal, 8);                   // handle
        break;
      }
      case "plant": {
        fcyl(g, Math.min(W, D) * .34, .95, 0, 0, 0, M.terra, 14);
        fcyl(g, .07, H * .45, 0, .9, 0, M.wood2, 6);
        const r = Math.min(W, D) * .46;
        fsph(g, r, 0, H * .45, 0, M.leaf, .85);
        fsph(g, r * .7, r * .5, H * .45 + .25, r * .3, M.leaf, .8);
        fsph(g, r * .6, -r * .45, H * .45 + .1, -r * .35, M.leaf, .8);
        break;
      }
      case "rug": {
        fb(g, W, .05, D, 0, 0, 0, new THREE.MeshLambertMaterial({ color: TONE.rug }), false);
        fb(g, W - .5, .06, D - .5, 0, .005, 0, new THREE.MeshLambertMaterial({ color:0xc7b193 }), false);
        break;
      }
      case "lamp": {
        fcyl(g, .45, .1, 0, 0, 0, M.dark, 14);
        fcyl(g, .05, H - .8, 0, .1, 0, M.metal, 8);
        const shade = new THREE.Mesh(new THREE.CylinderGeometry(.55, .42, .8, 14), M.white);
        shade.position.set(0, H - .35, 0); g.add(shade);
        break;
      }
      case "pooja": {
        fb(g, W, H * .55, D, 0, 0, 0, M.wood);                                               // cabinet
        fb(g, W, .12, D + .18, 0, H * .55, .06, M.wood2);                                     // platform
        for (const s of [-1, 1]) fb(g, .14, H * .42, .14, s * (W / 2 - .12), H * .55, -D / 2 + .12, M.wood2);
        fb(g, W, .18, D, 0, H * .97, 0, M.wood2);                                             // canopy
        for (const s of [-1, 1]) { fcyl(g, .11, .5, s * W * .22, H * .55 + .12, .1, M.brass, 10);
          fsph(g, .13, s * W * .22, H * .55 + .6, .1, M.brass, .8); }
        break;
      }
      case "swing": {
        fb(g, W, .28, D, 0, 2.1, 0, M.wood);
        fb(g, W, 1.3, .16, 0, 2.38, -D / 2 + .08, M.wood2);
        for (const s of [-1, 1]) fb(g, .16, .9, D, s * (W / 2 - .08), 2.38, 0, M.wood2);
        for (const sx of [-1, 1]) for (const sz of [-1, 1])
          fcyl(g, .045, FLOOR_H - 2.4, sx * (W / 2 - .25), 2.38, sz * (D / 2 - .18), M.metal, 6);
        break;
      }
      case "jaali": {
        const n = Math.max(4, Math.round(W / .7));
        for (let i = 0; i < n; i++) fb(g, W / (n * 2), H, D, -W / 2 + W * (i + .5) / n, 0, 0, M.wood2);
        for (const y of [0, H * .5, H - .2]) fb(g, W, .2, D + .02, 0, y, 0, M.wood);
        break;
      }
      case "ottoman": {                                   // a soft round pouffe
        const r = Math.min(W, D) / 2;
        fcyl(g, r, H - .35, 0, .3, 0, M.fabric, 18);
        fcyl(g, r * .94, .3, 0, 0, 0, M.fabric, 18);
        for (let i = 0; i < 4; i++) {
          const a = Math.PI / 4 + i * Math.PI / 2;
          fcyl(g, .06, .3, Math.cos(a) * r * .7, 0, Math.sin(a) * r * .7, M.wood2, 6);
        }
        break;
      }
      case "stools": {                                    // breakfast stools in a row
        const n = Math.max(2, Math.round(W / 1.6));
        for (let i = 0; i < n; i++) {
          const x = -W / 2 + W * (i + .5) / n;
          fcyl(g, .55, .18, x, H - .18, 0, M.wood, 16);
          fcyl(g, .12, H - .18, x, 0, 0, M.metal, 10);
          fcyl(g, .42, .06, x, .02, 0, M.metal, 14);
          fcyl(g, .06, .5, x, H * .35, .52, M.metal, 8);    // footrest
        }
        break;
      }
      case "tower": {                                     // slim speaker tower
        fb(g, W, H - .2, D, 0, .2, 0, M.dark);
        fb(g, W * .8, .2, D * .8, 0, 0, 0, M.metal);
        for (const y of [H * .3, H * .55, H * .78])
          fcyl(g, W * .3, .06, 0, y, D / 2 + .03, M.metal, 14, [Math.PI / 2, 0, 0]);
        break;
      }
      case "rack": {                                      // clothes drying rack
        for (const s of [-1, 1]) {
          fcyl(g, .05, H, s * (W / 2 - .1), 0, D / 2 - .08, M.metal, 6);
          fcyl(g, .05, H, s * (W / 2 - .1), 0, -D / 2 + .08, M.metal, 6);
        }
        for (let i = 0; i < 4; i++)
          fb(g, W - .2, .06, .06, 0, H - .5 - i * .55, -D / 2 + .08 + i * (D - .16) / 3, M.metal, false);
        break;
      }
      case "wallcab": {                                   // cabinet hung off the wall
        fb(g, W, H * .6, D, 0, 3.4, 0, M.white);
        fb(g, W - .12, .05, .06, 0, 3.4 + H * .3, D / 2 + .04, M.metal, false);
        break;
      }
      case "mirror-tall": {
        fb(g, W, H, D, 0, .2, 0, M.wood2);
        fb(g, W - .3, H - .3, .04, 0, .35, D / 2 + .03, M.glass, false);
        break;
      }
      case "nest": {                                      // two tables, one tucked under
        for (const [k, s] of [[0, 1], [1, .72]]) {
          const w = W * s, d = D * s, h = H - k * .35;
          fb(g, w, .14, d, k * .35, h - .14, k * .3, M.wood);
          for (const sx of [-1, 1]) for (const sz of [-1, 1])
            fcyl(g, .05, h - .14, k * .35 + sx * (w / 2 - .12), 0, k * .3 + sz * (d / 2 - .12), M.metal, 6);
        }
        break;
      }
      case "bell": {
        fcyl(g, .35, .12, 0, 0, 0, M.wood2, 12);
        for (const s of [-1, 1]) fcyl(g, .05, H - .6, s * .28, .12, 0, M.brass, 6);
        fb(g, .68, .06, .08, 0, H - .48, 0, M.brass, false);
        const bell = new THREE.Mesh(new THREE.ConeGeometry(.22, .45, 12), M.brass);
        bell.position.set(0, H - .72, 0); g.add(bell);
        break;
      }
      case "bistro": {
        fcyl(g, Math.min(W, D) / 2, .1, 0, H - .1, 0, M.metal, 16);
        fcyl(g, .12, H - .1, 0, 0, 0, M.metal, 10);
        fcyl(g, Math.min(W, D) * .4, .08, 0, 0, 0, M.metal, 16);
        break;
      }
      default:
        fb(g, W, H, D, 0, 0, 0, M[it.tone] || M.fabric);
    }
  }

  /* catalogue id → builder */
  const PIECE = {
    "l-sofa":"sofa", "l-recliner":"sofa", "l-arm":"sofa", "bl-chairs":"chair", "bl-swing":"swing",
    "l-coffee":"table", "d-table":"table", "k-break":"table",
    "b-study":"desk", "o-desk":"desk", "o-chair":"chair",
    "b-ward":"storage", "d-crock":"storage", "k-tall":"storage", "o-file":"storage",
    "l-console":"storage", "u-sink":"storage", "d-bar":"storage", "k-island":"storage",
    "b-dress":"basin", "t-van":"basin", "t-basin":"basin",
    "l-shelf":"shelf", "o-shelf":"shelf", "l-tv":"tv",
    "t-wc":"wc", "t-shower":"shower", "t-tub":"tub",
    "k-fridge":"appliance", "u-washer":"appliance", "u-dryer":"appliance",
    "l-d-plant":"plant", "bl-plant":"plant", "l-d-rug":"rug", "l-lt-floor":"lamp",
    "p-unit":"pooja", "p-jaali":"jaali", "l-partition":"jaali", "l-swing":"swing",
    "b-bench":"chair", "b-side":"storage",
    "l-ottoman":"ottoman", "l-speaker":"tower", "l-nest":"nest", "k-stool":"stools",
    "k-open":"shelf", "u-shelf":"shelf", "u-rack":"rack", "t-cab":"wallcab",
    "b-mirror":"mirror-tall", "b-rug":"rug", "d-rug":"rug", "o-rug":"rug", "p-mat":"rug",
    "p-bell":"bell", "o-lamp":"lamp", "bl-table":"bistro",
  };

  function furniture3d(group, r, baseY, cx, cz) {
    const M = FMAT();
    const { placed } = placeItems(r);
    for (const p of placed) {
      const it = p.it;
      if (it.counter) { kitchenRun(group, p, baseY, cx, cz, M); continue; }
      // face away from the wall it was anchored to, so backs are against walls
      const face = ({ n:"s", s:"n", w:"e", e:"w", nw:"s", ne:"s", sw:"n", se:"n", c:"s" })[it.at] || "s";
      const yaw = { s:0, n:Math.PI, e:Math.PI / 2, w:-Math.PI / 2 }[face];
      const sideways = face === "e" || face === "w";
      const g = new THREE.Group();
      g.position.set(p.x - cx, baseY, p.y - cz);
      g.rotation.y = yaw;
      buildPiece(g, it.bed ? "bed" : PIECE[it.id] || (it.tone === "plant" ? "plant" : "storage"),
                 sideways ? p.d : p.w, sideways ? p.w : p.d, p.h, M, it);
      group.add(g);
    }
    fittings3d(group, r, baseY, cx, cz, M);
  }

  /* The kitchen: base cabinets with a counter, an upper run, a sink and a hob. */
  function kitchenRun(group, p, baseY, cx, cz, M) {
    const along = p.w >= p.d, L = along ? p.w : p.d, T = along ? p.d : p.w;
    const g = new THREE.Group();
    g.position.set(p.x - cx, baseY, p.y - cz);
    if (!along) g.rotation.y = Math.PI / 2;
    fb(g, L, 2.6, T, 0, .35, 0, M.white);                        // carcass
    fb(g, L - .3, .35, T - .4, 0, 0, 0, M.dark);                  // toe kick
    fb(g, L, .22, T + .12, 0, 2.95, .06, new THREE.MeshLambertMaterial({ color:0x55575a }));  // counter
    const doors = Math.max(2, Math.round(L / 2));
    handles(g, doors, L, 2.4, T / 2 + .06, M.metal);
    fb(g, L * .6, 2.1, T * .55, -L * .2, FLOOR_H - 4.4, -T / 2 + T * .28, M.white);           // uppers
    handles(g, 2, L * .5, FLOOR_H - 4.6, -T / 2 + T * .55, M.metal);
    fb(g, 1.9, .06, 1.35, L * .26, 3.11, .05, M.metal, false);                                 // sink
    fcyl(g, .05, .8, L * .26, 3.17, -T / 2 + .2, M.metal, 8);
    fb(g, 2.1, .05, 1.5, -L * .3, 3.17, .05, M.dark, false);                                   // hob
    for (const dx of [-.5, .5]) for (const dz of [-.35, .35])
      fcyl(g, .3, .04, -L * .3 + dx, 3.2, .05 + dz, new THREE.MeshLambertMaterial({ color:0x1b1b1d }), 12);
    group.add(g);
  }

  /* Light fittings, curtains and wall art — the things that finish a room. */
  function fittings3d(group, r, baseY, cx, cz, M) {
    const glow = new THREE.MeshBasicMaterial({ color:0xfff1c9 });
    const X = r.x + r.w / 2 - cx, Z = r.y + r.h / 2 - cz, Y = baseY + FLOOR_H;
    for (const it of itemsFor(r.id)) {
      if (it.light === "pendant") {
        group.add(box(.05, 1.6, .05, X, Y - .8, Z, M.dark, false));
        const shade = new THREE.Mesh(new THREE.ConeGeometry(.75, .8, 16, 1, true), M.dark);
        shade.position.set(X, Y - 1.75, Z); group.add(shade);
        const bulb = new THREE.Mesh(new THREE.SphereGeometry(.3, 10, 8), glow);
        bulb.position.set(X, Y - 2, Z); group.add(bulb);
      } else if (it.light === "cove") {
        const y = Y - .7, x0 = r.x + .6 - cx, x1 = r.x + r.w - .6 - cx,
              z0 = r.y + .6 - cz, z1 = r.y + r.h - .6 - cz;
        group.add(box(r.w - 1.2, .12, .12, (x0 + x1) / 2, y, z0, glow, false));
        group.add(box(r.w - 1.2, .12, .12, (x0 + x1) / 2, y, z1, glow, false));
        group.add(box(.12, .12, r.h - 1.2, x0, y, (z0 + z1) / 2, glow, false));
        group.add(box(.12, .12, r.h - 1.2, x1, y, (z0 + z1) / 2, glow, false));
      } else if (it.id === "b-lt-ceil" || it.id === "k-lt" || it.id === "t-mirror") {
        const disc = new THREE.Mesh(new THREE.CylinderGeometry(.6, .6, .12, 16), glow);
        disc.position.set(X, Y - .25, Z); group.add(disc);
      }
      // curtains and blinds hang on this room's exterior windows
      if (/win|curt|blind/.test(it.id)) {
        for (const s of wallPlan()) {
          if (s.owner !== r || s.kind !== "ext" || s.opening !== "window") continue;
          const m = (s.a + s.b) / 2, wW = Math.min((s.b - s.a) * .46, 7.5) + 1.2;
          const fabric = new THREE.MeshLambertMaterial({ color: it.id === "b-win" ? 0x6a6357 : 0xd8d2c4 });
          for (const side of [-1, 1]) {
            const w = wW * .3;
            group.add(s.horiz
              ? box(w, 6.4, .28, m + side * (wW / 2 - w / 2) - cx, baseY + 4.2, s.coord + (s.owner.y + s.owner.h / 2 > s.coord ? .35 : -.35) - cz, fabric)
              : box(.28, 6.4, w, s.coord + (s.owner.x + s.owner.w / 2 > s.coord ? .35 : -.35) - cx, baseY + 4.2, m + side * (wW / 2 - w / 2) - cz, fabric));
          }
        }
      }
      if (it.fan) {                                                     // a ceiling fan, turning slowly
        const rod = box(.12, 1.1, .12, X, Y - .55, Z, M.metal, false); group.add(rod);
        const hub = new THREE.Group(); hub.position.set(X, Y - 1.25, Z);
        hub.add(new THREE.Mesh(new THREE.CylinderGeometry(.42, .5, .5, 14), M.metal));
        for (let i = 0; i < 3; i++) {
          const b = box(4.2, .06, .55, 0, -.1, 0, M.wood, false);
          b.position.set(Math.cos(i * 2.094) * 2.1, -.1, Math.sin(i * 2.094) * 2.1);
          b.rotation.y = -i * 2.094; hub.add(b);
        }
        group.add(hub); spinners.push(hub);
      }
      if (it.walltv) {                                                  // a screen on the rear wall
        group.add(box(Math.min(r.w * .45, 5.2), 3, .12, X, baseY + 5.4, r.y + .28 - cz, M.dark));
        group.add(box(Math.min(r.w * .45, 5.2) - .2, 2.8, .04, X, baseY + 5.4, r.y + .36 - cz,
          new THREE.MeshLambertMaterial({ color:0x11161c }), false));
      }
      if (it.wallbox) {                                                 // exhaust fan high on the wall
        group.add(box(1.1, 1.1, .16, X, baseY + FLOOR_H - 1.6, r.y + .26 - cz, M.white));
        group.add(box(.85, .85, .05, X, baseY + FLOOR_H - 1.6, r.y + .35 - cz, M.dark, false));
      }
      if (it.panel) {                                                   // vertical wood battens, one wall
        const n = Math.max(6, Math.round(r.w / .9));
        for (let i = 0; i < n; i++)
          group.add(box((r.w - .8) / (n * 2), 7.4, .12, r.x + .4 + (r.w - .8) * (i + .5) / n - cx,
                        baseY + 3.9, r.y + .26 - cz, M.wood2));
        group.add(box(r.w - .8, .18, .2, X, baseY + .3, r.y + .28 - cz, M.wood));
      }
      if (it.string) {                                                  // bulbs strung along the rail
        const glowS = new THREE.MeshBasicMaterial({ color:0xffdf9e });
        for (let i = 0; i < 9; i++) {
          const t = (i + .5) / 9, sag = Math.sin(t * Math.PI) * .6;
          const b = new THREE.Mesh(new THREE.SphereGeometry(.16, 8, 6), glowS);
          b.position.set(r.x + r.w * t - cx, baseY + FLOOR_H - 1.4 - sag, r.y + .4 - cz);
          group.add(b);
        }
      }
      if (it.id === "l-d-art" || it.id === "d-mirror") {                    // a framed piece on the rear wall
        const frame = new THREE.MeshLambertMaterial({ color: it.id === "d-mirror" ? 0xb8bcc0 : 0x6d5b45 });
        group.add(box(Math.min(r.w * .35, 4), 2.6, .12, X, baseY + 5.2, r.y + .25 - cz, frame));
        group.add(box(Math.min(r.w * .35, 4) - .3, 2.3, .04, X, baseY + 5.2, r.y + .33 - cz,
          new THREE.MeshLambertMaterial({ color: it.id === "d-mirror" ? 0xdfe6ea : 0x9c8f76 }), false));
      }
    }
  }

  /* A real staircase: treads the player can climb, and a ramp volume that
     moves the camera up with them. */
  function buildStairs(group, r, baseY, cx, cz) {
    const treads = 14, rise = FLOOR_H / treads;
    const alongZ = r.h >= r.w;
    const run = (alongZ ? r.h : r.w) / treads;
    const wood = new THREE.MeshLambertMaterial({ color:0xa07d55 });
    for (let i = 0; i < treads; i++) {
      const t = i * run + run/2;
      const x = alongZ ? r.x + r.w/2 - cx : r.x + t - cx;
      const z = alongZ ? r.y + t - cz : r.y + r.h/2 - cz;
      group.add(box(alongZ ? r.w - .4 : run, rise, alongZ ? run : r.h - .4,
                    x, baseY + i*rise + rise/2, z, wood));
    }
    stairZones.push({ x0:r.x, y0:r.y, x1:r.x + r.w, y1:r.y + r.h,
                      base:baseY, alongZ, from: alongZ ? r.y : r.x,
                      len: alongZ ? r.h : r.w });
  }

  /* ---------- exterior: roof, site, services ---------- */
  function facadeMaterial(len) {
    if (ext("x-facade-plaster")) return finishMaterial({ tex:"plaster", color:0xe6dfd1 }, len/3, FLOOR_H/3);
    if (ext("x-facade-brick")) return finishMaterial({ tex:"stone", color:0x9c5a3c }, len/4, FLOOR_H/3);
    if (ext("x-facade-stone")) return finishMaterial({ tex:"stone", color:0x8f877b }, len/6, FLOOR_H/5);
    if (ext("x-facade-wood"))  return finishMaterial({ tex:"wood",  color:0x9a6a40 }, len/6, FLOOR_H/6);
    return null;
  }
  function exterior3d(cx, cz, showRoof) {
    const P = CUR.plot, t = E.measure(CUR), top = t.floors - 1;
    const mat = c => new THREE.MeshLambertMaterial({ color:c });
    const topRooms = CUR.rooms.filter(r => r.floor === top && !UNCONDITIONED.has(r.type));
    const g = new THREE.Group();

    if (topRooms.length) {
      const x0 = Math.min(...topRooms.map(r => r.x)) - cx, x1 = Math.max(...topRooms.map(r => r.x + r.w)) - cx;
      const z0 = Math.min(...topRooms.map(r => r.y)) - cz, z1 = Math.max(...topRooms.map(r => r.y + r.h)) - cz;
      const W = x1 - x0, D = z1 - z0, Y = (top + 1) * FLOOR_H, mx = (x0+x1)/2, mz = (z0+z1)/2;
      const tile = finishMaterial({ tex:"stone", color:0xa65a3a }, W/5, D/5);
      const sloped = ext("x-roof-gable") || ext("x-roof-hip") || ext("x-roof-mangalore");

      if (sloped && showRoof) {
        const oh = 1.6;
        if (ext("x-roof-gable") || ext("x-roof-mangalore")) {
          const alongX = W >= D, span = (alongX ? D : W) + oh*2, run = (alongX ? W : D) + oh*2;
          const rise = span * .32;
          const shape = new THREE.Shape();
          shape.moveTo(-span/2, 0); shape.lineTo(span/2, 0); shape.lineTo(0, rise); shape.closePath();
          const geo = new THREE.ExtrudeGeometry(shape, { depth:run, bevelEnabled:false });
          geo.translate(0, 0, -run/2);
          const roof = new THREE.Mesh(geo, tile);
          roof.castShadow = roof.receiveShadow = true;
          if (alongX) roof.rotation.y = Math.PI / 2;
          roof.position.set(mx, Y + .3, mz);
          g.add(roof);
        } else {
          const rise = Math.min(W, D) * .34;
          const geo = new THREE.ConeGeometry(Math.SQRT1_2, 1, 4, 1);
          geo.rotateY(Math.PI / 4);
          const roof = new THREE.Mesh(geo, tile);
          roof.scale.set(W + oh*2, rise, D + oh*2);
          roof.position.set(mx, Y + .3 + rise/2, mz);
          roof.castShadow = roof.receiveShadow = true;
          g.add(roof);
        }
      } else if (showRoof) {
        const par = mat(0xd9d4ca);                          // parapet on a flat terrace
        g.add(box(W, 3, .5, mx, Y + 1.5, z0, par)); g.add(box(W, 3, .5, mx, Y + 1.5, z1, par));
        g.add(box(.5, 3, D, x0, Y + 1.5, mz, par)); g.add(box(.5, 3, D, x1, Y + 1.5, mz, par));
      }
      if (ext("x-pergola") && !sloped) {
        const post = mat(0x5f4a36);
        const px0 = mx - W/4, px1 = mx + W/4, pz0 = mz - D/4, pz1 = mz + D/4;
        for (const [x, z] of [[px0,pz0],[px1,pz0],[px0,pz1],[px1,pz1]]) g.add(box(.4, 8, .4, x, Y + 4, z, post));
        for (let i = 0; i <= 8; i++)
          g.add(box(W/2 + .8, .25, .3, mx, Y + 8, pz0 + (pz1 - pz0) * i / 8, post));
      }
      if (ext("x-solar")) {
        const panel = mat(0x1f3552), frame = mat(0x9aa3ab);
        const lift = sloped ? Math.min(W, D) * .2 : 1.2;
        for (let i = 0; i < 6; i++) {
          const p = new THREE.Group();
          p.add(box(3.2, .12, 5.4, 0, 0, 0, panel)); p.add(box(3.3, .06, 5.5, 0, -.08, 0, frame));
          p.rotation.x = -.26;
          p.position.set(mx - W/3 + (i % 3) * 3.6, Y + lift + 1, mz - 2.8 + Math.floor(i / 3) * 5.8);
          g.add(p);
        }
      }
    }

    // Car porch: a slab over the parking bay, on four columns.
    const park = CUR.rooms.find(r => r.type === "parking" && r.floor === 0);
    if (ext("x-porch") && park) {
      const col = mat(0xdcd6c9), slab = mat(0xcfc9bc), H = 9.5;
      const x0 = park.x - cx, x1 = park.x + park.w - cx, z0 = park.y - cz, z1 = park.y + park.h - cz;
      for (const [x, z] of [[x0+.4,z0+.4],[x1-.4,z0+.4],[x0+.4,z1-.4],[x1-.4,z1-.4]])
        g.add(box(.8, H, .8, x, H/2, z, col));
      g.add(box(park.w + 1.2, .5, park.h + 1.2, (x0+x1)/2, H + .25, (z0+z1)/2, slab));
    }
    // Portico columns at the main door, and a raised sit-out beside it.
    const mainSeg = wallPlan().find(s => s.main);
    if (ext("x-portico") && mainSeg) {
      const col = mat(0xe4ded1), m = (mainSeg.a + mainSeg.b) / 2;
      const [px, pz] = mainSeg.horiz ? [m - cx, mainSeg.coord - cz] : [mainSeg.coord - cx, m - cz];
      const out = mainSeg.horiz ? [0, -4] : [-4, 0];
      for (const d of [-3.5, 3.5]) {
        const x = px + out[0] + (mainSeg.horiz ? d : 0), z = pz + out[1] + (mainSeg.horiz ? 0 : d);
        g.add(box(1.1, FLOOR_H - .5, 1.1, x, (FLOOR_H - .5)/2, z, col));
      }
      g.add(box(mainSeg.horiz ? 9 : 5, .6, mainSeg.horiz ? 5 : 9,
                px + out[0], FLOOR_H - .2, pz + out[1], col));
    }
    if (ext("x-thinnai") && mainSeg) {
      const plinth = mat(0xd3ccbd), m = (mainSeg.a + mainSeg.b) / 2;
      const [px, pz] = mainSeg.horiz ? [m - cx, mainSeg.coord - cz] : [mainSeg.coord - cx, m - cz];
      g.add(mainSeg.horiz ? box(10, 1.4, 4, px, .7, pz - 2.6, plinth)
                          : box(4, 1.4, 10, px - 2.6, .7, pz, plinth));
    }
    // Window grills and balcony railings, drawn from the same wall plan the
    // windows come from.
    if (ext("x-grills") || ext("x-railing-ms") || ext("x-railing-ss")) {
      const bar = mat(0x3a3a3a), glass = ext("x-railing-ss");
      for (const s of wallPlan()) {
        const base = s.floor * FLOOR_H;
        if (ext("x-grills") && s.kind === "ext" && s.opening === "window") {
          const wW = Math.min((s.b - s.a) * .46, 7.5), m = (s.a + s.b) / 2;
          const n = Math.max(3, Math.round(wW / 1.1));
          for (let i = 0; i < n; i++) {
            const o = -wW/2 + wW * (i + .5) / n;
            g.add(s.horiz ? box(.08, 4, .08, m + o - cx, base + 5, s.coord - cz, bar, false)
                          : box(.08, 4, .08, s.coord - cx, base + 5, m + o - cz, bar, false));
          }
        }
        if (s.kind === "ext" && s.owner.type === "balcony" && (ext("x-railing-ms") || glass)) {
          const len = s.b - s.a, m = (s.a + s.b) / 2;
          if (glass) {
            g.add(s.horiz ? box(len, 3, .12, m - cx, base + 1.5, s.coord - cz, GLASS, false)
                          : box(.12, 3, len, s.coord - cx, base + 1.5, m - cz, GLASS, false));
          } else {
            const n = Math.max(3, Math.round(len / 1.2));
            for (let i = 0; i < n; i++) {
              const o = -len/2 + len * (i + .5) / n;
              g.add(s.horiz ? box(.1, 3, .1, m + o - cx, base + 1.5, s.coord - cz, bar, false)
                            : box(.1, 3, .1, s.coord - cx, base + 1.5, m + o - cz, bar, false));
            }
          }
          g.add(s.horiz ? box(len, .18, .3, m - cx, base + 3, s.coord - cz, bar, false)
                        : box(.3, .18, len, s.coord - cx, base + 3, m - cz, bar, false));
        }
      }
    }
    if (ext("x-driveway") && park) {
      const pave = finishMaterial({ tex:"tile", color:0x9c978c }, park.w / 3, (park.y + park.h) / 3);
      g.add(box(park.w + 2, .1, park.y + park.h, park.x + park.w/2 - cx, .05,
                (park.y + park.h)/2 - cz, pave, false));
    }
    if (ext("x-tank")) {
      const tank = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 4, 16),
                                  mat(0x2a2a2e));
      const top = E.measure(CUR).floors * FLOOR_H;
      tank.position.set(P.w/2 - cx - 6, top + 2.6, P.h/2 - cz + 6);
      tank.castShadow = true;
      g.add(box(5, .6, 5, P.w/2 - cx - 6, top + .3, P.h/2 - cz + 6, mat(0xbdb7ab)));
      g.add(tank);
    }
    if (ext("x-lights")) {
      const post = mat(0x3f3f3f), glow = new THREE.MeshBasicMaterial({ color:0xffe9b0 });
      for (const [x, z] of [[2, RULE.front - 2], [P.w - 2, RULE.front - 2], [2, P.h - 2], [P.w - 2, P.h - 2]]) {
        g.add(box(.25, 6, .25, x - cx, 3, z - cz, post, false));
        const b = new THREE.Mesh(new THREE.SphereGeometry(.45, 10, 8), glow);
        b.position.set(x - cx, 6.4, z - cz); g.add(b);
      }
    }
    if (ext("x-gate") || ext("x-wall")) {
      const wall = mat(0xcfc8bb), gate = mat(0x2e2e2e), H = 4.5, T = .6;
      const gc = park ? park.x + park.w/2 : P.w/2, gw = ext("x-gate") ? 12 : 0;
      const fx = -cx, bx = P.w - cx, fz = -cz, bz = P.h - cz;
      const left = gc - gw/2, right = gc + gw/2;
      if (left > .2) g.add(box(left, H, T, fx + left/2, H/2, fz, wall));
      if (P.w - right > .2) g.add(box(P.w - right, H, T, fx + right + (P.w - right)/2, H/2, fz, wall));
      g.add(box(P.w, H, T, 0, H/2, bz, wall));
      g.add(box(T, H, P.h, fx, H/2, 0, wall)); g.add(box(T, H, P.h, bx, H/2, 0, wall));
      if (gw) {
        g.add(box(gw/2 - .2, H - .6, .2, fx + left + gw/4, (H - .6)/2, fz, gate));
        g.add(box(gw/2 - .2, H - .6, .2, fx + right - gw/4, (H - .6)/2, fz, gate));
      }
    }
    if (ext("x-garden")) {
      const grass = mat(0x6e8f55), trunk = mat(0x6b4f36), crown = mat(0x4f7a43);
      g.add(box(P.w - 2, .12, RULE.front - 2, 0, .06, -cz + RULE.front/2, grass, false));
      for (const x of [2.5, P.w - 2.5]) {
        g.add(box(.7, 5, .7, x - cx, 2.5, 3 - cz, trunk));
        const c = new THREE.Mesh(new THREE.SphereGeometry(3, 12, 10), crown);
        c.position.set(x - cx, 6.5, 3 - cz); c.castShadow = true; g.add(c);
      }
    }
    SHELL.add(g);
  }

  /** Build the whole house as one group.
   *
   *  Returns the group plus the three things a host needs to drive it: the
   *  walls to walk into, the stairs to climb, and the fans to turn. The caller
   *  owns the scene, the camera and the disposal of whatever it replaces. */
  function build(M, opts = {}) {
    // bound to this model for the duration of the build, so the body below
    // reads exactly as it did when it lived on the page
    CUR = M;
    const shell = new THREE.Group();
    SHELL = shell;
    const colliders = [], stairZones = [], spinners = [];

    const darkUi = (getComputedStyle(document.body).backgroundColor.match(/\d+/g)?.[0] | 0) < 100;
    const SITE = new THREE.MeshLambertMaterial({ color: darkUi ? 0x4a5245 : 0xbfc8b5 });
    const SEL  = new THREE.MeshLambertMaterial({ color:0x8a9a82 });
    const BAD  = new THREE.MeshLambertMaterial({ color:0xc46355 });

    const P = M.plot, cx = P.w/2, cz = P.h/2;
    const t = E.measure(M);
    const bad = new Set([...t.overlaps.flat(), ...t.outside]);
    const showFurn = opts.furniture !== false;
    const showRoof = opts.roof === true || opts.walking;
    const chajja = ext("x-chajja");

    shell.add(box(P.w + 18, .8, P.h + 18, 0, -.4, 0, SITE, false));

    // one material pair per room, shared by every wall face that room owns
    const mats = new Map();
    for (const r of M.rooms) {
      const fin = finishOf(r);
      mats.set(r.id, {
        wall: bad.has(r.id) ? BAD : r.id === M.selected ? SEL
              : finishMaterial(finishById("wall", fin.wall), Math.max(r.w, r.h)/8, FLOOR_H/8),
        floor: bad.has(r.id) ? BAD : finishMaterial(finishById("floor", fin.floor), r.w/4, r.h/4)
      });
    }
    const groups = new Map();
    for (const r of M.rooms) {
      const g = new THREE.Group();
      g.userData = { id:r.id, floor:r.floor };
      const slab = box(r.w, .4, r.h, r.x + r.w/2 - cx, r.floor*FLOOR_H + .2, r.y + r.h/2 - cz,
                       mats.get(r.id).floor, false);
      slab.userData = { id:r.id, floor:r.floor, pickable:true };
      g.add(slab);
      if (WALLED(r.type)) {                      // skirting — the detail rooms always have
        const sk = new THREE.MeshLambertMaterial({ color:0x6f6558 }), y = r.floor * FLOOR_H + .7;
        for (const [w, d, dx, dz] of [[r.w, .18, 0, -r.h / 2], [r.w, .18, 0, r.h / 2],
                                      [.18, r.h, -r.w / 2, 0], [.18, r.h, r.w / 2, 0]])
          g.add(box(w, .6, d, r.x + r.w / 2 + dx - cx, y, r.y + r.h / 2 + dz - cz, sk, false));
      }
      groups.set(r.id, g);
    }

    for (const s of wallPlan(M)) {
      const g = groups.get(s.owner.id), baseY = s.floor * FLOOR_H;
      const own = mats.get(s.owner.id).wall;
      const [ax, az, bx, bz] = s.horiz
        ? [s.a - cx, s.coord - cz, s.b - cx, s.coord - cz]
        : [s.coord - cx, s.a - cz, s.coord - cx, s.b - cz];
      // which face of the wall looks into the owning room?
      const ownerSide = s.horiz
        ? ((s.owner.y + s.owner.h/2) > s.coord ? "+z" : "-z")
        : ((s.owner.x + s.owner.w/2) > s.coord ? "+x" : "-x");
      const flip = { "+z":"-z", "-z":"+z", "+x":"-x", "-x":"+x" }[ownerSide];
      const faces = { [ownerSide]: own };
      let other = null;
      if (s.kind === "shared" && s.other && WALLED(s.other.type)) other = mats.get(s.other.id).wall;
      if (s.kind === "ext") other = facadeMaterial(s.b - s.a);
      if (other) faces[flip] = other;
      wallRun(g, ax, az, bx, bz, s.thick, own, s.opening, baseY,
              { faces, main:s.main, chajja: chajja && s.kind === "ext", outward:s.outward });
    }

    for (const r of M.rooms) {
      const g = groups.get(r.id), baseY = r.floor * FLOOR_H;
      if (r.type === "stairs") buildStairs(g, r, baseY + .4, cx, cz);
      else if (r.type === "balcony") {
        const rail = new THREE.MeshLambertMaterial({ color:0x9aa093 });
        const x0 = r.x - cx, x1 = r.x + r.w - cx, z0 = r.y - cz, z1 = r.y + r.h - cz;
        const touches = side => M.rooms.some(q => q !== r && q.floor === r.floor && WALLED(q.type) && (
          side === "n" ? Math.abs(q.y + q.h - r.y) <= TOL && Math.min(q.x+q.w, r.x+r.w) - Math.max(q.x, r.x) > 1
        : side === "s" ? Math.abs(q.y - (r.y + r.h)) <= TOL && Math.min(q.x+q.w, r.x+r.w) - Math.max(q.x, r.x) > 1
        : side === "w" ? Math.abs(q.x + q.w - r.x) <= TOL && Math.min(q.y+q.h, r.y+r.h) - Math.max(q.y, r.y) > 1
        :                Math.abs(q.x - (r.x + r.w)) <= TOL && Math.min(q.y+q.h, r.y+r.h) - Math.max(q.y, r.y) > 1));
        if (!touches("n")) g.add(box(r.w, 3.2, .2, (x0+x1)/2, baseY + 1.6, z0, rail));
        if (!touches("s")) g.add(box(r.w, 3.2, .2, (x0+x1)/2, baseY + 1.6, z1, rail));
        if (!touches("w")) g.add(box(.2, 3.2, r.h, x0, baseY + 1.6, (z0+z1)/2, rail));
        if (!touches("e")) g.add(box(.2, 3.2, r.h, x1, baseY + 1.6, (z0+z1)/2, rail));
      }
      if (showRoof && WALLED(r.type)) {
        // the ceiling you chose, seen from inside on the walkthrough
        const cf = finishById("ceiling", finishOf(r).ceiling);
        g.add(box(r.w, .35, r.h, r.x + r.w/2 - cx, baseY + FLOOR_H - .17, r.y + r.h/2 - cz,
                  finishMaterial(cf, r.w / 4, r.h / 4)));
        if (cf.id === "c-cove") {                     // a cove reads as a recessed border
          const t = new THREE.MeshLambertMaterial({ color:0xfffaf0 });
          g.add(box(r.w - 1.2, .18, .3, r.x + r.w/2 - cx, baseY + FLOOR_H - .5, r.y + .8 - cz, t, false));
          g.add(box(r.w - 1.2, .18, .3, r.x + r.w/2 - cx, baseY + FLOOR_H - .5, r.y + r.h - .8 - cz, t, false));
        }
      }
      if (showFurn) furniture3d(g, r, baseY + .4, cx, cz);
      shell.add(g);
    }
    exterior3d(cx, cz, showRoof);

    return { group: shell, colliders, stairZones, spinners };
  }

  /* What a host needs besides the building itself.

     wallPlan and placeItems are here because the 2D plan draws the same doors,
     windows and furniture footprints the 3D view does — one set of openings,
     drawn twice, rather than two sets that can disagree. clearTextures exists
     because the procedural finishes bake the theme's colours in, so switching
     between light and dark has to throw them away. */
  return {
    build,
    wallPlan,
    placeItems: (M, room) => { CUR = M; return placeItems(room); },
    WALLED,
    clearTextures: () => texCache.clear(),
  };
}
