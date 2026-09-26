/* =====================================================================
   SYNAPSE ENGINE — the shared model
   One copy of the geometry, cost, compliance and scoring rules, imported by
   both the landing page and the studio, and mirroring api/app/engines/*.py.
   Every function takes the model explicitly:

     M = { rooms, plot, interiors, budget, brief }

   so nothing here reaches for page state, and the two pages cannot drift.
   ===================================================================== */
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/* ---------- constants mirrored from geometry.py ---------- */
export const FLOOR_H = 10, OPENING = 0.12, SNAP = 0.5;
/* Wall thicknesses and opening sizes, in feet. They belong here rather than
   inside the 3D builder because the plan draws the same doors the model
   builds and the IFC writes the same widths — one set of numbers, three
   readers. */
export const WALL_EXT = .75, WALL_INT = .5, DOOR_W = 3.2, DOOR_H = 7,
             SILL = 3, HEAD = 7, EYE = 5.6;
export const POINTS = {
  bedroom:[1,2,8], living:[1,3,10], kitchen:[1,2,12], bath:[1,1,3], dining:[0,2,6],
  office:[1,1,8], pooja:[1,0,3], parking:[0,0,2], utility:[1,1,4],
  stairs:[0,1,3], balcony:[1,0,2]
};
export const DEFAULT_SIZE = {
  bedroom:[13,10], bath:[7,6.5], living:[18,12], kitchen:[11,10], dining:[11,9],
  office:[10,10], pooja:[6,6], utility:[8,6.5], stairs:[4,12], balcony:[10,6], parking:[15,10]
};
export const MIN_SIZE = { bath:[4,4], pooja:[4,4], stairs:[3,8], default:[5,5] };
export const LABEL = { bedroom:"Bedroom", bath:"Bathroom", living:"Living room", kitchen:"Kitchen",
  dining:"Dining", office:"Office", pooja:"Pooja room", utility:"Utility",
  stairs:"Stairs", balcony:"Balcony", parking:"Parking" };
/* Spaces that are not enclosed conditioned area. Parking and balcony are
   excluded from built-up the way a municipality would exclude them. */
export const UNCONDITIONED = new Set(["parking", "balcony"]);

/* Published plinth-area rates (₹ per sq m) and bylaws per region. Mirrors
   api/app/regions.py — change both together.
   Tamil Nadu: TN PWD Plinth Area Rates 2025-26, Circular Memo HDO(A)/48518/2003
   dated 30.07.2025, residential framed, effective 01.08.2025. */
export const TN_SERVICES = { "Internal water supply":767, "Internal sanitary arrangements":597,
                      "Internal electrical arrangements":1269 };
export const tnPar = (foundation, superstructure, roof, nonres) => ({ foundation, superstructure, roof,
  stilt: Math.round(.65 * nonres * 100) / 100, anti_termite:144, services_per_sqm:TN_SERVICES,
  services_pct:{}, location_index:100, coastal:{ under10:328, "10to24":164 } });
export const TN_DOC = "Tamil Nadu PWD — Plinth Area Rates 2025-26, Circular Memo HDO(A)/48518/2003 dated 30.07.2025 (Annexure I, III)";
export const TNCDBR = { version:"TNCDBR-2019.v1", front:4.92, rear:4.92, side:3.28, max_fsi:2.0, max_cover:1.0, max_height:39.4, min_parking:1 };
export const TN_BIG = tnPar(6420, 17455, 2170, 13110), TN_MID = tnPar(6255, 17070, 2135, 12820), TN_MOF = tnPar(5955, 16260, 2025, 12215);
export const REGIONS = {
  "Chennai":            { state:"Tamil Nadu", par:TN_BIG, rule:TNCDBR, source:TN_DOC },
  "Coimbatore":         { state:"Tamil Nadu", par:TN_BIG, rule:TNCDBR, source:TN_DOC },
  "Madurai":            { state:"Tamil Nadu", par:TN_BIG, rule:TNCDBR, source:TN_DOC },
  "Trichy":             { state:"Tamil Nadu", par:TN_MID, rule:TNCDBR, source:TN_DOC },
  "Salem":              { state:"Tamil Nadu", par:TN_MID, rule:TNCDBR, source:TN_DOC },
  "Tamil Nadu (other towns)": { state:"Tamil Nadu", par:TN_MOF, rule:TNCDBR, source:TN_DOC }
};
export const SQM = 0.09290304;
export const WEIGHTS = { budget:.35, compliance:.25, buildability:.25, sustainability:.15 };
/* ---------- finishes ----------
   Each carries a rate, so choosing marble is a design decision with a
   number attached rather than a swatch. */
export const FINISH = {
  wall: [
    { id:"p-white", name:"White",    rate:28,  color:0xf2efe8, tex:"plaster" },
    { id:"p-warm",  name:"Warm",     rate:28,  color:0xefe5d4, tex:"plaster" },
    { id:"p-sage",  name:"Sage",     rate:32,  color:0xbcc7b2, tex:"plaster" },
    { id:"p-clay",  name:"Clay",     rate:32,  color:0xd9b69a, tex:"plaster" },
    { id:"p-slate", name:"Slate",    rate:32,  color:0x8d97a0, tex:"plaster" },
    { id:"p-teal",  name:"Teal",     rate:32,  color:0x6f9390, tex:"plaster" },
    { id:"p-terra", name:"Terracotta", rate:32, color:0xc0714b, tex:"plaster" },
    { id:"p-tex",   name:"Textured", rate:55,  color:0xe8e2d6, tex:"plaster" },
    { id:"lime",    name:"Lime",     rate:70,  color:0xeae3d2, tex:"plaster" },
    { id:"paper",   name:"Paper",    rate:95,  color:0xe7dccb, tex:"paper" },
    { id:"dado",    name:"Tile dado", rate:120, color:0xd9e2e4, tex:"tile" },
    { id:"conc",    name:"Concrete", rate:210, color:0xa9a49c, tex:"plaster" },
    { id:"brick-e", name:"Brick",    rate:260, color:0x9c5a3c, tex:"stone" },
    { id:"wood-p",  name:"Wood",     rate:340, color:0xa8794b, tex:"wood" },
    { id:"stone-c", name:"Stone",    rate:520, color:0x9d958a, tex:"stone" }
  ],
  floor: [
    { id:"f-skid",   name:"Anti-skid", rate:85,  color:0xc6c2b8, tex:"tile" },
    { id:"f-vit",    name:"Vitrified", rate:95,  color:0xe0dcd4, tex:"tile" },
    { id:"f-oxide",  name:"Red oxide", rate:120, color:0xa8503c, tex:"plaster" },
    { id:"f-terra",  name:"Terracotta", rate:140, color:0xc27a53, tex:"tile" },
    { id:"f-kota",   name:"Kota stone", rate:150, color:0x6f7468, tex:"granite" },
    { id:"f-prem",   name:"Premium",   rate:165, color:0xd2ccc0, tex:"tile" },
    { id:"f-mosaic", name:"Mosaic",    rate:180, color:0xded6c4, tex:"granite" },
    { id:"f-lam",    name:"Laminate",  rate:190, color:0xbb8e60, tex:"wood" },
    { id:"f-athan",  name:"Athangudi", rate:260, color:0xc9a25c, tex:"tile" },
    { id:"f-wood",   name:"Wood",      rate:320, color:0xb07f4f, tex:"wood" },
    { id:"f-gran",   name:"Granite",   rate:380, color:0x6f6b66, tex:"granite" },
    { id:"f-marble", name:"Marble",    rate:420, color:0xeeece8, tex:"marble" }
  ],
  /* Ceilings are the surface people forget to price and always notice. */
  ceiling: [
    { id:"c-plain",  name:"Plain",     rate:45,  color:0xf4f1ea, tex:"plaster" },
    { id:"c-conc",   name:"Exposed",   rate:30,  color:0xb4afa6, tex:"plaster" },
    { id:"c-pop",    name:"POP false", rate:130, color:0xf6f4ef, tex:"plaster" },
    { id:"c-cove",   name:"Cove + gypsum", rate:180, color:0xf7f5f0, tex:"plaster" },
    { id:"c-wood",   name:"Wood rafters", rate:420, color:0x9a6a40, tex:"wood" }
  ]
};
export const DEFAULT_FINISH = {
  bedroom:{ wall:"p-warm",  floor:"f-vit",   ceiling:"c-plain" },
  living: { wall:"p-white", floor:"f-vit",   ceiling:"c-plain" },
  kitchen:{ wall:"p-white", floor:"f-skid",  ceiling:"c-plain" },
  bath:   { wall:"p-white", floor:"f-skid",  ceiling:"c-plain" },
  dining: { wall:"p-warm",  floor:"f-vit",   ceiling:"c-plain" },
  office: { wall:"p-white", floor:"f-vit",   ceiling:"c-plain" },
  pooja:  { wall:"p-warm",  floor:"f-vit",   ceiling:"c-plain" },
  utility:{ wall:"p-white", floor:"f-skid",  ceiling:"c-conc"  },
  stairs: { wall:"p-white", floor:"f-vit",   ceiling:"c-plain" },
  balcony:{ wall:"p-white", floor:"f-skid",  ceiling:"c-conc"  },
  parking:{ wall:"p-white", floor:"f-skid",  ceiling:"c-conc"  }
};
export const finishById = (kind, id) => FINISH[kind].find(f => f.id === id) || FINISH[kind][0];

/* ---------- furniture, fittings and exterior ----------
   MIRRORED from api/app/seed.py INTERIOR_CATALOG — same ids, same prices — so
   an item picked here is priced identically by the server. fp = footprint
   [width, depth, height] in feet; `at` is where it sits in the room. Items
   without fp (lighting, curtains, appliances in a counter) are priced and
   listed but add no geometry of their own. Flooring and wall items from the
   seed are deliberately absent: those are the per-room finishes above, and
   listing them here too would charge for the floor twice. */
export const CATALOG = [
  { id:"l-sofa", room:"living", cat:"Seating", name:"3-seater sofa", price:45000, fp:[7,3,2.4], at:"s", tone:"soft" },
  { id:"l-recliner", room:"living", cat:"Seating", name:"Recliner", price:28000, fp:[3,3,3], at:"e", tone:"soft" },
  { id:"l-coffee", room:"living", cat:"Tables", name:"Coffee table", price:12000, fp:[3.6,2,1.3], at:"c", tone:"wood" },
  { id:"l-tv", room:"living", cat:"Storage", name:"TV unit", price:70000, fp:[5.2,1.4,1.8], at:"n", tone:"wood", screen:true },
  { id:"l-shelf", room:"living", cat:"Storage", name:"Bookshelf", price:22000, fp:[3,1.2,6], at:"w", tone:"wood" },
  { id:"l-lt-cove", room:"living", cat:"Lighting", name:"Cove lighting", price:35000, light:"cove" },
  { id:"l-lt-pend", room:"living", cat:"Lighting", name:"Pendant", price:14000, light:"pendant" },
  { id:"l-win-curt", room:"living", cat:"Windows", name:"Curtains", price:16000 },
  { id:"l-win-blind", room:"living", cat:"Windows", name:"Blinds", price:11000 },
  { id:"l-d-rug", room:"living", cat:"Decor", name:"Rug", price:9000, fp:[6,4,.06], at:"c", tone:"rug" },
  { id:"l-d-art", room:"living", cat:"Decor", name:"Artwork", price:15000 },
  { id:"l-d-plant", room:"living", cat:"Decor", name:"Indoor plants", price:6000, fp:[1.3,1.3,3.6], at:"ne", tone:"plant" },

  { id:"b-bed", room:"bedroom", cat:"Furniture", name:"King bed", price:65000, fp:[6.6,6.8,1.8], at:"n", tone:"soft", bed:true },
  { id:"b-ward", room:"bedroom", cat:"Storage", name:"Wardrobe", price:95000, fp:[5,2,6.8], at:"s", tone:"wood" },
  { id:"b-study", room:"bedroom", cat:"Furniture", name:"Study table", price:18000, fp:[4,2,2.5], at:"e", tone:"wood" },
  { id:"b-side", room:"bedroom", cat:"Furniture", name:"Side tables", price:9000, fp:[1.5,1.5,1.8], at:"nw", tone:"wood" },
  { id:"b-lt-ceil", room:"bedroom", cat:"Lighting", name:"Ceiling light", price:7000, light:"pendant" },
  { id:"b-lt-read", room:"bedroom", cat:"Lighting", name:"Reading lights", price:9000 },
  { id:"b-win", room:"bedroom", cat:"Windows", name:"Blackout curtains", price:14000 },

  { id:"k-cab", room:"kitchen", cat:"Cabinetry", name:"Modular cabinets", price:240000, counter:true },
  { id:"k-island", room:"kitchen", cat:"Cabinetry", name:"Island", price:85000, fp:[5,2.6,3], at:"c", tone:"white" },
  { id:"k-top-gran", room:"kitchen", cat:"Countertop", name:"Granite", price:52000, group:"top" },
  { id:"k-top-quartz", room:"kitchen", cat:"Countertop", name:"Quartz", price:96000, group:"top" },
  { id:"k-hob", room:"kitchen", cat:"Appliances", name:"Hob", price:24000 },
  { id:"k-chim", room:"kitchen", cat:"Appliances", name:"Chimney", price:32000 },
  { id:"k-oven", room:"kitchen", cat:"Appliances", name:"Built-in oven", price:45000 },
  { id:"k-dish", room:"kitchen", cat:"Appliances", name:"Dishwasher", price:48000 },
  { id:"k-splash", room:"kitchen", cat:"Finishes", name:"Backsplash tile", price:18000 },
  { id:"k-lt", room:"kitchen", cat:"Lighting", name:"Under-cabinet lighting", price:16000 },

  { id:"t-wc", room:"bath", cat:"Fixtures", name:"Wall-hung WC", price:28000, fp:[1.5,2.2,2.5], at:"nw", tone:"white" },
  { id:"t-basin", room:"bath", cat:"Fixtures", name:"Counter basin", price:16000, fp:[2,1.4,2.8], at:"se", tone:"white" },
  { id:"t-shower", room:"bath", cat:"Fixtures", name:"Shower enclosure", price:42000, fp:[3,3,7], at:"ne", tone:"glass" },
  { id:"t-tub", room:"bath", cat:"Fixtures", name:"Bathtub", price:78000, fp:[5,2.5,1.8], at:"s", tone:"white" },
  { id:"t-van", room:"bath", cat:"Furniture", name:"Vanity unit", price:34000, fp:[2.4,1.6,2.8], at:"sw", tone:"wood" },
  { id:"t-mirror", room:"bath", cat:"Furniture", name:"Backlit mirror", price:12000 },
  { id:"t-acc", room:"bath", cat:"Accessories", name:"Grab bars and accessories", price:8000 },

  { id:"d-table", room:"dining", cat:"Furniture", name:"6-seater dining table", price:52000, fp:[5.6,3.2,2.5], at:"c", tone:"wood", chairs:true },
  { id:"d-crock", room:"dining", cat:"Furniture", name:"Crockery unit", price:38000, fp:[4,1.5,6], at:"n", tone:"wood" },
  { id:"d-lt", room:"dining", cat:"Lighting", name:"Pendant over table", price:18000, light:"pendant" },

  { id:"o-desk", room:"office", cat:"Furniture", name:"Work desk", price:22000, fp:[5,2.2,2.5], at:"n", tone:"wood" },
  { id:"o-chair", room:"office", cat:"Furniture", name:"Task chair", price:12000, fp:[1.8,1.8,3], at:"c", tone:"soft" },
  { id:"o-shelf", room:"office", cat:"Furniture", name:"Book shelving", price:18000, fp:[3,1.2,6], at:"w", tone:"wood" },
  { id:"p-unit", room:"pooja", cat:"Furniture", name:"Pooja unit", price:35000, fp:[3,1.4,3.4], at:"n", tone:"wood" },
  { id:"u-washer", room:"utility", cat:"Appliances", name:"Washing machine", price:32000, fp:[2,2,2.8], at:"nw", tone:"white" },
  { id:"bl-chairs", room:"balcony", cat:"Furniture", name:"Balcony chairs", price:15000, fp:[4,2,2.6], at:"c", tone:"wood" },
  { id:"bl-plant", room:"balcony", cat:"Decor", name:"Planters", price:8000, fp:[1.4,1.4,2.6], at:"ne", tone:"plant" },

  { id:"x-roof-gable", room:"exterior", cat:"Roof", name:"Sloped tile roof", price:280000, group:"roof" },
  { id:"x-roof-hip", room:"exterior", cat:"Roof", name:"Hip roof, clay tile", price:340000, group:"roof" },
  { id:"x-facade-brick", room:"exterior", cat:"Facade", name:"Exposed brick facade", price:190000, group:"facade" },
  { id:"x-facade-stone", room:"exterior", cat:"Facade", name:"Stone cladding", price:360000, group:"facade" },
  { id:"x-facade-wood", room:"exterior", cat:"Facade", name:"Wood cladding accents", price:240000, group:"facade" },
  { id:"x-chajja", room:"exterior", cat:"Shading", name:"Window sunshades (chajjas)", price:60000 },
  { id:"x-pergola", room:"exterior", cat:"Shading", name:"Terrace pergola", price:110000 },
  { id:"x-gate", room:"exterior", cat:"Site", name:"Compound wall and gate", price:220000, group:"boundary" },
  { id:"x-garden", room:"exterior", cat:"Site", name:"Front landscaping", price:90000 },
  { id:"x-solar", room:"exterior", cat:"Services", name:"Rooftop solar, 3 kW", price:180000 },

  // --- more detail, by room ---
  { id:"l-arm", room:"living", cat:"Seating", name:"Armchair", price:18000, fp:[2.6,2.6,2.8], at:"w", tone:"soft" },
  { id:"l-swing", room:"living", cat:"Seating", name:"Oonjal, teak swing", price:85000, fp:[5,2,6.5], at:"e", tone:"wood", swing:true },
  { id:"l-console", room:"living", cat:"Storage", name:"Console table", price:16000, fp:[3.6,1.2,2.6], at:"nw", tone:"wood" },
  { id:"l-partition", room:"living", cat:"Decor", name:"Jaali partition", price:42000, fp:[5,.5,7], at:"e", tone:"wood", jaali:true },
  { id:"l-lt-floor", room:"living", cat:"Lighting", name:"Floor lamp", price:9000, fp:[1.2,1.2,5], at:"nw", tone:"soft" },
  { id:"b-dress", room:"bedroom", cat:"Furniture", name:"Dressing table", price:22000, fp:[3.2,1.6,5.5], at:"w", tone:"wood" },
  { id:"b-bench", room:"bedroom", cat:"Furniture", name:"Bed bench", price:14000, fp:[4,1.4,1.5], at:"s", tone:"soft" },
  { id:"b-loft", room:"bedroom", cat:"Storage", name:"Loft storage", price:28000 },
  { id:"b-ac", room:"bedroom", cat:"Appliances", name:"Split AC", price:42000 },
  { id:"k-tall", room:"kitchen", cat:"Cabinetry", name:"Tall unit", price:65000, fp:[2.5,2,7], at:"e", tone:"white" },
  { id:"k-break", room:"kitchen", cat:"Cabinetry", name:"Breakfast counter", price:38000, fp:[5,1.6,3], at:"s", tone:"wood" },
  { id:"k-sink", room:"kitchen", cat:"Fixtures", name:"Double-bowl sink", price:18000 },
  { id:"k-ro", room:"kitchen", cat:"Appliances", name:"Water purifier", price:16000 },
  { id:"k-fridge", room:"kitchen", cat:"Appliances", name:"Refrigerator", price:52000, fp:[2.6,2.4,6], at:"ne", tone:"white" },
  { id:"t-geyser", room:"bath", cat:"Fixtures", name:"Geyser", price:14000 },
  { id:"t-faucet", room:"bath", cat:"Fixtures", name:"Health faucet and mixer set", price:11000 },
  { id:"t-rail", room:"bath", cat:"Accessories", name:"Towel rail and hooks", price:5000 },
  { id:"t-niche", room:"bath", cat:"Tiling", name:"Shower niche and feature tile", price:16000 },
  { id:"d-bar", room:"dining", cat:"Furniture", name:"Bar cabinet", price:34000, fp:[3.2,1.4,6], at:"e", tone:"wood" },
  { id:"d-mirror", room:"dining", cat:"Decor", name:"Wall mirror", price:12000 },
  { id:"p-jaali", room:"pooja", cat:"Decor", name:"Jaali screen and door", price:38000, fp:[4,.5,7], at:"s", tone:"wood", jaali:true },
  { id:"p-lamp", room:"pooja", cat:"Decor", name:"Brass lamp pair", price:14000, fp:[1,1,3], at:"e", tone:"brass" },
  { id:"o-file", room:"office", cat:"Storage", name:"Filing cabinet", price:14000, fp:[1.6,1.6,3.6], at:"e", tone:"white" },
  { id:"u-dryer", room:"utility", cat:"Appliances", name:"Dryer", price:38000, fp:[2,2,2.8], at:"ne", tone:"white" },
  { id:"u-sink", room:"utility", cat:"Fixtures", name:"Utility sink and counter", price:18000, fp:[3,1.8,3], at:"s", tone:"white" },
  { id:"bl-deck", room:"balcony", cat:"Finishes", name:"Wood deck flooring", price:36000 },
  { id:"bl-swing", room:"balcony", cat:"Furniture", name:"Hanging swing chair", price:22000, fp:[3,3,6], at:"w", tone:"soft" },

  // --- exterior detail ---
  { id:"x-roof-mangalore", room:"exterior", cat:"Roof", name:"Mangalore tile roof", price:240000, group:"roof" },
  { id:"x-facade-plaster", room:"exterior", cat:"Facade", name:"Textured exterior plaster", price:95000, group:"facade" },
  { id:"x-porch", room:"exterior", cat:"Structure", name:"Car porch roof", price:180000 },
  { id:"x-portico", room:"exterior", cat:"Structure", name:"Portico columns", price:140000 },
  { id:"x-thinnai", room:"exterior", cat:"Structure", name:"Sit-out (thinnai)", price:95000 },
  { id:"x-grills", room:"exterior", cat:"Openings", name:"Window grills", price:85000 },
  { id:"x-railing-ms", room:"exterior", cat:"Openings", name:"MS balcony railing", price:45000, group:"railing" },
  { id:"x-railing-ss", room:"exterior", cat:"Openings", name:"Steel and glass railing", price:120000, group:"railing" },
  { id:"x-wall", room:"exterior", cat:"Site", name:"Compound wall only", price:140000, group:"boundary" },
  { id:"x-driveway", room:"exterior", cat:"Site", name:"Paved driveway", price:75000 },
  { id:"x-tank", room:"exterior", cat:"Services", name:"Terrace water tank", price:35000 },
  { id:"x-rain", room:"exterior", cat:"Services", name:"Rainwater harvesting pit", price:55000 },
  { id:"x-lights", room:"exterior", cat:"Services", name:"Outdoor and facade lighting", price:65000 },

  // --- interiors, the things a room actually has in it ---
  { id:"l-fan", room:"living", cat:"Comfort", name:"Ceiling fan", price:6500, fan:true },
  { id:"l-ottoman", room:"living", cat:"Seating", name:"Ottoman", price:9000, fp:[2.4,2.4,1.4], at:"c", tone:"soft" },
  { id:"l-speaker", room:"living", cat:"Electronics", name:"Home theatre", price:65000, fp:[1.1,1.1,3.6], at:"ne", tone:"dark" },
  { id:"l-panel", room:"living", cat:"Finishes", name:"Wood wall panelling", price:55000, panel:true },
  { id:"l-nest", room:"living", cat:"Tables", name:"Nesting side tables", price:11000, fp:[1.8,1.8,1.6], at:"sw", tone:"wood" },
  { id:"b-fan", room:"bedroom", cat:"Comfort", name:"Ceiling fan", price:6500, fan:true },
  { id:"b-tv", room:"bedroom", cat:"Electronics", name:"Wall-mounted TV", price:38000, walltv:true },
  { id:"b-rug", room:"bedroom", cat:"Decor", name:"Bedside rug", price:7000, fp:[5,3,.06], at:"s", tone:"rug" },
  { id:"b-mirror", room:"bedroom", cat:"Decor", name:"Full-length mirror", price:9000, fp:[1.6,.4,6], at:"e", tone:"glass" },
  { id:"k-stool", room:"kitchen", cat:"Seating", name:"Breakfast stools", price:12000, fp:[3.4,1.3,2.6], at:"s", tone:"wood", stool:true },
  { id:"k-open", room:"kitchen", cat:"Cabinetry", name:"Open shelves", price:14000, fp:[3.2,1,3.4], at:"e", tone:"wood" },
  { id:"t-exh", room:"bath", cat:"Services", name:"Exhaust fan", price:3500, wallbox:true },
  { id:"t-cab", room:"bath", cat:"Storage", name:"Wall cabinet", price:9000, fp:[2.2,1,2.6], at:"n", tone:"white" },
  { id:"d-fan", room:"dining", cat:"Comfort", name:"Ceiling fan", price:6500, fan:true },
  { id:"d-rug", room:"dining", cat:"Decor", name:"Dining rug", price:12000, fp:[7,5,.06], at:"c", tone:"rug" },
  { id:"o-lamp", room:"office", cat:"Lighting", name:"Desk lamp", price:4000, fp:[.9,.9,1.6], at:"n", tone:"dark" },
  { id:"o-rug", room:"office", cat:"Decor", name:"Rug", price:8000, fp:[6,4,.06], at:"c", tone:"rug" },
  { id:"p-mat", room:"pooja", cat:"Decor", name:"Prayer mats", price:3000, fp:[3.5,2.4,.08], at:"c", tone:"rug" },
  { id:"p-bell", room:"pooja", cat:"Decor", name:"Brass bell and stand", price:2500, fp:[.8,.8,3.2], at:"w", tone:"brass" },
  { id:"u-rack", room:"utility", cat:"Fittings", name:"Drying rack", price:6000, fp:[3.2,1.6,4.2], at:"e", tone:"metal", rack:true },
  { id:"u-shelf", room:"utility", cat:"Storage", name:"Utility shelves", price:9000, fp:[3,1.2,5.5], at:"w", tone:"white" },
  { id:"bl-light", room:"balcony", cat:"Lighting", name:"String lights", price:4000, string:true },
  { id:"bl-table", room:"balcony", cat:"Furniture", name:"Bistro table", price:9000, fp:[2.2,2.2,2.5], at:"c", tone:"metal" }
];
export const catalogById = Object.fromEntries(CATALOG.map(c => [c.id, c]));
export const itemsFor = (M, key) => (M.interiors[key] || []).map(id => catalogById[id]).filter(Boolean);
export const hasItem = (M, key, id) => (M.interiors[key] || []).includes(id);
export function toggleItem(M, key, id) {
  const it = catalogById[id];
  let list = [...(M.interiors[key] || [])];
  if (list.includes(id)) list = list.filter(x => x !== id);
  else {
    // one roof, one facade, one countertop
    if (it?.group) list = list.filter(x => catalogById[x]?.group !== it.group);
    list.push(id);
  }
  M.interiors[key] = list;
}
/* Priced like the server's interiors: flat catalogue prices, only for items
   attached to a room that still exists (or to the exterior). */
export function catalogTotal(M) {
  const live = new Set(M.rooms.map(r => r.id).concat("exterior"));
  let sum = 0;
  for (const [key, ids] of Object.entries(M.interiors))
    if (live.has(key)) for (const id of ids) sum += catalogById[id]?.price || 0;
  return sum;
}
/* Starter sets. A style is a starting point; every piece stays individually
   removable. */
export const FURNISH_SETS = {
  essentials: { living:["l-sofa","l-coffee","l-tv"], bedroom:["b-bed","b-ward"],
                kitchen:["k-cab","k-top-gran","k-hob"], bath:["t-wc","t-basin"],
                dining:["d-table"], office:["o-desk","o-chair"], pooja:["p-unit"],
                utility:["u-washer"], balcony:["bl-plant"] },
  comfort:    { living:["l-sofa","l-coffee","l-tv","l-d-rug","l-lt-pend","l-win-curt","l-d-plant","l-fan"],
                bedroom:["b-bed","b-ward","b-side","b-lt-ceil","b-win","b-fan"],
                kitchen:["k-cab","k-top-gran","k-hob","k-chim","k-lt"],
                bath:["t-wc","t-basin","t-shower","t-van"], dining:["d-table","d-crock","d-lt"],
                office:["o-desk","o-chair","o-shelf"], pooja:["p-unit"],
                utility:["u-washer","u-sink"], balcony:["bl-chairs","bl-plant"] },
  premium:    { living:["l-sofa","l-recliner","l-arm","l-swing","l-coffee","l-nest","l-ottoman","l-tv","l-speaker","l-shelf","l-console","l-panel","l-d-rug","l-lt-cove","l-lt-pend","l-lt-floor","l-fan","l-win-curt","l-d-art","l-d-plant"],
                bedroom:["b-bed","b-ward","b-side","b-study","b-dress","b-bench","b-lt-ceil","b-lt-read","b-win","b-ac","b-fan","b-tv","b-rug","b-mirror"],
                kitchen:["k-cab","k-tall","k-island","k-top-quartz","k-hob","k-chim","k-oven","k-dish","k-sink","k-ro","k-fridge","k-splash","k-lt","k-stool","k-open"],
                bath:["t-wc","t-basin","t-shower","t-tub","t-van","t-mirror","t-acc","t-geyser","t-faucet","t-niche","t-exh","t-cab"],
                dining:["d-table","d-crock","d-bar","d-lt","d-mirror","d-fan","d-rug"],
                office:["o-desk","o-chair","o-shelf","o-file"],
                pooja:["p-unit","p-jaali","p-lamp"], utility:["u-washer","u-dryer","u-sink"],
                balcony:["bl-chairs","bl-plant","bl-deck","bl-swing"] }
};
export function furnishRoom(M, r, level) {
  const ids = FURNISH_SETS[level]?.[r.type];
  if (ids) M.interiors[r.id] = [...ids];
}
/* =====================================================================
   ENGINES
   ===================================================================== */
export function measure(M) {
  const r = M.rooms, P = M.plot, plotArea = P.w * P.h;
  const t = { built:0, footprint:0, wall:0, floorArea:0, doors:1, windows:0, elec:6,
              bedrooms:0, baths:0, parking:0, overlaps:[], outside:[], stairs:0,
              floors: r.length ? Math.max(...r.map(x => x.floor)) + 1 : 1,
              wallCost:0, floorCost:0, ceilCost:0, openArea:0 };
  for (const x of r) {
    const area = x.w * x.h;
    const conditioned = !UNCONDITIONED.has(x.type);
    if (conditioned) { t.built += area; t.floorArea += area; }
    if (x.floor === 0) t.footprint += area;
    if (!conditioned) t.openArea += area;

    const wallArea = 2 * (x.w + x.h) * FLOOR_H * (1 - OPENING) * 0.5;
    t.wall += wallArea;

    const fin = finishOf(x);
    t.wallCost  += wallArea * finishById("wall",  fin.wall).rate;
    t.floorCost += area     * finishById("floor", fin.floor).rate;
    if (conditioned) t.ceilCost += area * finishById("ceiling", fin.ceiling).rate;

    const [d, w, e] = POINTS[x.type] || [1,1,5];
    t.doors += d; t.windows += w; t.elec += e;
    if (x.type === "bedroom") t.bedrooms++;
    else if (x.type === "bath") t.baths++;
    else if (x.type === "parking") t.parking++;
    else if (x.type === "stairs") t.stairs++;
    if (x.x < -0.01 || x.y < -0.01 || x.x + x.w > P.w + 0.01 || x.y + x.h > P.h + 0.01)
      t.outside.push(x.id);
  }
  for (let i = 0; i < r.length; i++)
    for (let j = i + 1; j < r.length; j++) {
      const a = r[i], b = r[j];
      if (a.floor !== b.floor) continue;
      if (!(a.x + a.w <= b.x + .05 || b.x + b.w <= a.x + .05 ||
            a.y + a.h <= b.y + .05 || b.y + b.h <= a.y + .05)) t.overlaps.push([a.id, b.id]);
    }
  t.plotArea = plotArea;
  t.fsi = plotArea ? t.built / plotArea : 0;
  t.cover = plotArea ? t.footprint / plotArea : 0;
  return t;
}

/* Mirrors api/app/engines/cost.py (par_lines) line for line: a plinth-area-
   rate estimate the way a PWD engineer writes one, with the chosen finishes
   charged on top of the schedule's base specification. */
export function costLines(M, t) {
  const P = ratesFor(M).par, idx = (P.location_index ?? 100) / 100;
  const ground = t.footprint * SQM, cond = t.built * SQM, open = t.openArea * SQM;
  const L = (item, code, unit, qty, rate, basis, amount = qty * rate) => ({ item, code, unit, qty, rate, amount, basis });
  const building = [
    ["Foundation", "PAR-F", ground, "foundation", "Ground-floor plinth area, all rooms on the ground floor."],
    ["Superstructure", "PAR-S", cond, "superstructure", "Plinth area of every enclosed floor."],
    ["Stilt, parking and balconies", "PAR-ST", open, "stilt", "Open and stilt areas at the reduced rate."],
    ["Roof finishing", "PAR-R", ground, "roof", "Ground-floor plinth area, as the schedule specifies."],
    ["Anti-termite treatment", "PAR-AT", ground, "anti_termite", "Ground-floor plinth area."]
  ].filter(([, , , k]) => P[k]).map(([n, c, q, k, b]) => L(n, c, "sqm", q, P[k] * idx, b));
  const coastRate = (P.coastal || {})[M.brief.coastal] || 0;
  if (coastRate) building.push(L("Coastal extra, higher-grade concrete", "PAR-CO", "sqm", cond + open,
    coastRate * idx, `Total plinth area, for a plot ${M.brief.coastal === "under10" ? "within 10 km" : "10-24 km from"} the sea.`));
  const base = building.reduce((s, l) => s + l.amount, 0);
  const services = [
    ...Object.entries(P.services_per_sqm || {}).map(([n, r]) => L(n, "PAR-SV", "sqm", cond, r * idx, "Per square metre of enclosed plinth area.")),
    ...Object.entries(P.services_pct || {}).map(([n, pct]) => L(n, "PAR-SV", "%", pct, Math.round(base), `${pct}% of the building cost above.`, base * pct / 100))
  ];
  return [...building, ...services,
    L("Wall finishes", "F-8.0", "LS", 1, t.wallCost, "Paint, paper or cladding chosen per room, over the plastered wall."),
    L("Floor finishes", "F-9.0", "LS", 1, t.floorCost, "Tile, wood or stone chosen per room, over the base floor."),
    L("Ceiling finishes", "F-10.0", "LS", 1, t.ceilCost, "Paint, false ceiling or rafters chosen per room, over the slab soffit.")];
}
export function cost(M, t) {
  const lines = costLines(M, t);
  const civil = lines.filter(l => l.code !== "PAR-SV" && !l.code.startsWith("F-")).reduce((s, l) => s + l.amount, 0);
  const finish = lines.filter(l => l.code === "PAR-SV" || l.code.startsWith("F-")).reduce((s, l) => s + l.amount, 0);
  const subtotal = civil + finish;
  const interiors = catalogTotal(M);
  const oh = subtotal * ratesFor(M).overhead_pct / 100;     // overheads on construction only,
  const cont = subtotal * ratesFor(M).contingency_pct / 100; // exactly as the server does
  return { civil, finish, subtotal, interiors, oh, cont, total: subtotal + interiors + oh + cont };
}

export function compliance(M, t, RULE) {
  const P = M.plot, out = [];
  const add = (title, ok, why, sev="BLOCKER") => out.push({ title, ok, why, sev,
    outcome: ok === null ? "UNDETERMINED" : ok ? "LIKELY_PASS" : "LIKELY_FAIL" });

  add("Floor Space Index", t.fsi <= RULE.max_fsi,
      `FSI ${t.fsi.toFixed(2)} against a permitted ${RULE.max_fsi.toFixed(2)}.`);
  add("Ground coverage", t.cover <= RULE.max_cover,
      `${(t.cover*100).toFixed(0)}% of the plot covered, limit ${(RULE.max_cover*100).toFixed(0)}%.`);

  const g = M.rooms.filter(r => r.floor === 0);
  if (g.length) {
    const front = Math.min(...g.map(r=>r.y));
    const rear  = P.h - Math.max(...g.map(r=>r.y + r.h));
    const side  = Math.min(Math.min(...g.map(r=>r.x)), P.w - Math.max(...g.map(r=>r.x + r.w)));
    add("Front setback", front >= RULE.front - .01, `${front.toFixed(1)} ft provided, ${RULE.front} ft required.`);
    add("Rear setback",  rear  >= RULE.rear  - .01, `${rear.toFixed(1)} ft provided, ${RULE.rear} ft required.`);
    add("Side setback",  side  >= RULE.side  - .01, `${side.toFixed(1)} ft provided, ${RULE.side} ft required.`);
  } else add("Setbacks", null, "No ground-floor rooms placed yet.");

  add("Parking", t.parking >= RULE.min_parking,
      `${t.parking} bay(s); ${RULE.min_parking} required.`, "WARNING");
  const height = t.floors * FLOOR_H;
  add("Building height", height <= RULE.max_height,
      `${t.floors} floor(s) at ${FLOOR_H} ft is roughly ${height} ft, against a permitted `
      + `${RULE.max_height} ft. Parapets and stair headroom are not modelled here.`, "WARNING");
  if (t.floors > 1 && t.stairs === 0)
    add("Vertical access", false,
        "More than one floor with no staircase placed. Add one — it also lets you walk upstairs in 3D.",
        "WARNING");
  if (t.overlaps.length)
    add("Overlapping rooms", false,
        `${t.overlaps.length} pair(s) share the same space — quantities above are double-counting.`);
  if (t.outside.length)
    add("Rooms outside the plot", false, `${t.outside.length} room(s) cross the boundary.`);
  return out;
}

export function readiness(M, t, c, f) {
  const budget = M.budget * 100000, over = c.total - budget;
  const bFit = over <= 0 ? clamp(100 - (Math.abs(over)/budget)*20, 82, 100)
                         : clamp(100 - (over/budget)*320, 0, 100);
  const graded = f.filter(x => x.outcome !== "UNDETERMINED");
  const failed = graded.filter(x => !x.ok);
  const comp = graded.length ? clamp(100 - (failed.length/graded.length)*100, 0, 100) : 100;
  let build = 100 - (t.floors-1)*8 - Math.max(0,t.bedrooms-4)*7 - Math.max(0,t.baths-3)*5;
  if (t.overlaps.length) build -= 25;
  const slivers = M.rooms.filter(r => r.type !== "stairs" &&
    Math.max(r.w/r.h, r.h/r.w) > 3.2).length;
  build = clamp(build - slivers*4, 35, 100);
  let sus = 70 + (t.cover <= .5 ? 12 : 0)
              + (t.bedrooms && t.built/t.bedrooms <= 520 ? 12 : 0)
              - (t.built > 2600 ? 14 : 0);
  sus = clamp(sus, 30, 100);
  const composite = Math.round(WEIGHTS.budget*bFit + WEIGHTS.compliance*comp
                             + WEIGHTS.buildability*build + WEIGHTS.sustainability*sus);
  return { bFit:Math.round(bFit), comp:Math.round(comp), build:Math.round(build),
           sus:Math.round(sus), composite, over,
           verdict: composite >= 80 ? "ready to detail" : composite >= 55 ? "needs decisions" : "not yet viable" };
}

/* The rate card and bylaw ruleset for a model's region. */
export function ratesFor(M) {
  const name = (M && M.brief && M.brief.region) || "Chennai";
  const R = REGIONS[name] || REGIONS.Chennai;
  return { par: R.par, source: R.source, rule: R.rule, region: name,
           overhead_pct: 0, contingency_pct: 5, tier: "pwd" };
}
export const ruleFor = M => ratesFor(M).rule;

/* A model the engines can measure, built from a brief alone: the landing page
   configurator produces one of these so its numbers come from the same code
   the studio and the API use, instead of a second set of formulas. */
export function layoutFromBrief(b) {
  const plot = { w: b.plot_w || 40, h: b.plot_h || 50, facing: b.facing };
  const R = REGIONS[b.region] || REGIONS.Chennai;
  const rooms = [];
  const floors = Math.max(1, Math.min(3, b.floors || 1));
  let cursor = [R.rule.side, R.rule.front, 0];        // x, y, floor
  let rowH = 0;
  const place = (type, id, name, size) => {
    const [w, h] = size || DEFAULT_SIZE[type] || [10, 10];
    let [x, y, f] = cursor;
    if (x + w > plot.w - R.rule.side) { x = R.rule.side; y += rowH + 1; rowH = 0; }
    if (y + h > plot.h - R.rule.rear) { f += 1; x = R.rule.side; y = R.rule.front; rowH = 0; }
    if (f >= floors) return false;
    rooms.push({ id, name, type, floor: f, x, y, w, h });
    cursor = [x + w + 1, y, f];
    rowH = Math.max(rowH, h);
    return true;
  };
  if (b.parking) place("parking", "parking", "Parking", [15, 10]);
  place("living", "living", "Living room", [b.living_w || 18, b.living_h || 12]);
  place("kitchen", "kitchen", "Kitchen");
  place("dining", "dining", "Dining");
  for (let i = 0; i < (b.bedrooms || 3); i++)
    place("bedroom", `bed_${i + 1}`, i === 0 ? "Master bedroom" : `Bedroom ${i + 1}`,
          [b.bed_w || 13, b.bed_h || 10]);
  for (let i = 0; i < (b.bathrooms || 2); i++)
    place("bath", `bath_${i + 1}`, `Bathroom ${i + 1}`);
  if (floors > 1)
    for (let f = 0; f < floors; f++)
      rooms.push({ id: `stair_${f}`, name: "Stairs", type: "stairs", floor: f,
                   x: plot.w - R.rule.side - 4, y: plot.h - R.rule.rear - 11, w: 4, h: 11 });
  return { rooms, plot, interiors: {}, budget: b.budget || 45,
           brief: { ...DEFAULT_BRIEF, ...(b.brief || {}), region: b.region || "Chennai" } };
}

export const DEFAULT_BRIEF = { family_members: 4, elderly_residents: 0, children: 0,
  theme: "", region: "Chennai", coastal: "inland", notes: "",
  sbc: 150, concrete: "M25", steel: "Fe500" };

/* Finishes live ON the room, so a PATCH carries them and the server prices
   them identically. */
export function setFinish(r, kind, id) { r.finish = { ...(r.finish || {}), [kind]: id }; }
export const finishOf = r => {
  const d = DEFAULT_FINISH[r.type] || DEFAULT_FINISH.living;
  const f = r.finish || {};
  return { wall: f.wall || d.wall, floor: f.floor || d.floor, ceiling: f.ceiling || d.ceiling };
};
