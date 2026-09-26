/* Reading the brief the client actually sent.

   Nobody hands an architect a form. They hand over a PDF, a Word file, or a
   photograph of a page from a notebook. All of it is read here, in the
   browser — the document never leaves the machine, which matters when it is
   somebody's house and somebody's budget.

   Text PDFs are read directly. A scan has no text layer, so those pages are
   rendered and put through OCR, which is slower and worth saying out loud. */
import { clamp, REGIONS } from "./model";

const CDN = {
  pdf: "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.0.379/build/pdf.min.mjs",
  pdfWorker: "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.0.379/build/pdf.worker.min.mjs",
  tesseract: "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.0/dist/tesseract.min.js",
  jszip: "https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js",
};

type Step = (message: string) => void;

const loadScript = (src: string) => new Promise<void>((ok, no) => {
  if (document.querySelector(`script[src="${src}"]`)) return ok();
  const el = document.createElement("script");
  el.src = src;
  el.onload = () => ok();
  el.onerror = () => no(new Error("Could not load " + src + " — check the connection."));
  document.head.appendChild(el);
});

let pdfjs: any = null;
async function pdfLib() {
  if (!pdfjs) {
    pdfjs = await import(/* @vite-ignore */ CDN.pdf);
    pdfjs.GlobalWorkerOptions.workerSrc = CDN.pdfWorker;
  }
  return pdfjs;
}

export type ReadResult = { text: string; how: string };

export async function readDocument(file: File, onStep?: Step): Promise<ReadResult> {
  const name = file.name.toLowerCase();
  if (/\.(txt|md|csv)$/.test(name)) return { text: await file.text(), how: "text file" };
  if (/\.docx$/.test(name)) return { text: await readDocx(file), how: "Word document" };
  if (/\.(png|jpe?g|webp|bmp)$/.test(name)) {
    onStep?.("Reading the image with OCR — this takes a few seconds.");
    return { text: await ocr(URL.createObjectURL(file), onStep), how: "image, read by OCR" };
  }
  if (/\.pdf$/.test(name)) return readPdf(file, onStep);
  if (/\.doc$/.test(name))
    throw new Error("Old .doc files cannot be read in a browser. Save it as .docx or PDF.");
  throw new Error(`Cannot read ${file.name}. Use a PDF, .docx, .txt or an image.`);
}

async function readDocx(file: File) {
  await loadScript(CDN.jszip);
  const zip = await (window as any).JSZip.loadAsync(await file.arrayBuffer());
  const xml: string | undefined = await zip.file("word/document.xml")?.async("string");
  if (!xml) throw new Error("That .docx has no document body.");
  return xml.replace(/<\/w:p>/g, "\n").replace(/<[^>]+>/g, " ")
            .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
            .replace(/[ \t]+/g, " ");
}

async function readPdf(file: File, onStep?: Step): Promise<ReadResult> {
  const lib = await pdfLib();
  const pdf = await lib.getDocument({ data: await file.arrayBuffer() }).promise;
  let text = "";
  for (let p = 1; p <= pdf.numPages; p++) {
    const page = await pdf.getPage(p);
    const content = await page.getTextContent();
    text += content.items.map((i: any) => i.str).join(" ") + "\n";
  }
  // A scan has pages and almost no text. That is the tell.
  if (text.replace(/\s/g, "").length >= 40) return { text, how: `PDF, ${pdf.numPages} page(s)` };

  onStep?.("No text layer — this looks like a scan. Running OCR, a few seconds per page.");
  const pages = Math.min(pdf.numPages, 5);
  let out = "";
  for (let p = 1; p <= pages; p++) {
    const page = await pdf.getPage(p);
    const viewport = page.getViewport({ scale: 2 });          // OCR likes the pixels
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width; canvas.height = viewport.height;
    await page.render({ canvasContext: canvas.getContext("2d")!, viewport }).promise;
    onStep?.(`Reading page ${p} of ${pages}…`);
    out += await ocr(canvas.toDataURL("image/png"), onStep) + "\n";
  }
  return { text: out, how: `scanned PDF, ${pdf.numPages} page(s), read by OCR` };
}

async function ocr(src: string, onStep?: Step) {
  await loadScript(CDN.tesseract);
  const worker = await (window as any).Tesseract.createWorker("eng", 1, {
    logger: (msg: any) => msg.status === "recognizing text"
      && onStep?.(`OCR ${Math.round(msg.progress * 100)}%`),
  });
  try {
    const { data } = await worker.recognize(src);
    return data.text as string;
  } finally { await worker.terminate(); }
}

/* ---------- pulling a brief out of prose ----------
   Deliberately conservative. Anything it is not confident about is left
   alone and reported, because a wrong plot size applied silently is worse
   than a question asked out loud. */
export type FoundBrief = {
  plot_w?: number; plot_h?: number; bedrooms?: number; bathrooms?: number;
  budget?: number; floors?: number; region?: string; coastal?: string;
  facing?: number; extras: string[]; family?: number; elderly?: number; children?: number;
  rooms: { type: string; w: number; h: number; label: string }[];
};

const WORD_NUM: Record<string, number> = { one: 1, two: 2, three: 3, four: 4, five: 5,
  six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
const numAt = (w: string) => WORD_NUM[w] ?? Number(w);
const M_PER_FT = 3.28084;

const ROOM_WORDS: [string, string[]][] = [
  ["bedroom", ["bedroom", "bed room", "master bedroom"]],
  ["bath", ["bathroom", "toilet", "wc", "bath"]],
  ["living", ["living room", "hall", "drawing room"]],
  ["kitchen", ["kitchen"]],
  ["dining", ["dining"]],
  ["office", ["study", "home office", "office"]],
  ["pooja", ["pooja", "puja", "prayer room"]],
  ["utility", ["utility", "wash area", "laundry"]],
  ["balcony", ["balcony", "sit out", "sitout"]],
  ["parking", ["car park", "parking", "garage", "porch"]],
];

export function parseBrief(raw: string): { found: FoundBrief; notes: string[] } {
  const t = " " + raw.toLowerCase().replace(/[‘’]/g, "'")
                     .replace(/[“”]/g, '"').replace(/\s+/g, " ") + " ";
  const found: FoundBrief = { extras: [], rooms: [] };
  const notes: string[] = [];

  // plot — "40 x 60", "40ft x 60ft", "12m by 18m", "2400 sq ft plot"
  const dim = t.match(/(\d+(?:\.\d+)?)\s*(?:ft|feet|')?\s*(?:x|×|by)\s*(\d+(?:\.\d+)?)\s*(ft|feet|'|m|metres?|meters?)?/);
  if (dim) {
    const metric = /^m/.test(dim[3] || "");
    found.plot_w = Math.round(Number(dim[1]) * (metric ? M_PER_FT : 1));
    found.plot_h = Math.round(Number(dim[2]) * (metric ? M_PER_FT : 1));
    notes.push(`Plot ${found.plot_w} × ${found.plot_h} ft${metric ? " (converted from metres)" : ""}`);
  } else {
    const area = t.match(/(\d[\d,]{2,})\s*(?:sq\.?\s*ft|sqft|square feet|sft)\s*(?:plot|site|land)/);
    if (area) {
      const a = Number(area[1].replace(/,/g, "")), w = Math.round(Math.sqrt(a * 0.66));
      found.plot_w = w; found.plot_h = Math.round(a / w);
      notes.push(`Plot area ${a} sq ft with no dimensions — assumed ${w} × ${found.plot_h} ft`);
    }
  }

  const bhk = t.match(/(\d|one|two|three|four|five|six)\s*[- ]?\s*(?:bhk|bedrooms?|bed\b)/);
  if (bhk) { found.bedrooms = clamp(numAt(bhk[1]), 1, 8); notes.push(`${found.bedrooms} bedroom(s)`); }

  const bath = t.match(/(\d|one|two|three|four|five)\s*[- ]?\s*(?:bathrooms?|baths?|toilets?|wc)/);
  if (bath) { found.bathrooms = clamp(numAt(bath[1]), 1, 6); notes.push(`${found.bathrooms} bathroom(s)`); }

  const cr = t.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:cr|crores?)/);
  const lk = t.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?)/);
  const rup = t.match(/(?:₹|rs\.?|inr)\s*([\d,]{6,})/);
  if (cr) found.budget = Math.round(Number(cr[1]) * 100);
  else if (lk) found.budget = Math.round(Number(lk[1]));
  else if (rup) found.budget = Math.round(Number(rup[1].replace(/,/g, "")) / 100000);
  if (found.budget) notes.push(`Budget ₹${found.budget}L`);

  const fl = t.match(/(\d|one|two|three)\s*(?:floors?|storey|story|storeys|stories|levels?)/);
  if (fl) { found.floors = clamp(numAt(fl[1]), 1, 3); notes.push(`${found.floors} floor(s)`); }
  else if (/\b(g\+1|ground \+ 1|duplex)\b/.test(t)) { found.floors = 2; notes.push("2 floors (G+1)"); }
  else if (/\b(single storey|single floor|ground floor only|g\+0)\b/.test(t))
    { found.floors = 1; notes.push("1 floor"); }

  for (const name of Object.keys(REGIONS)) {
    const key = name.split(" ")[0].toLowerCase();
    if (t.includes(" " + key)) { found.region = name; notes.push(`Region ${name}`); break; }
  }
  if (!found.region && /\b(tamil nadu|chennai|madras)\b/.test(t)) {
    found.region = "Chennai"; notes.push("Region Chennai");
  }

  // "nothing coastal applies" is not a coastal site, and the coastal extra
  // is real money on the estimate.
  const coastalSaid = /\b(coastal|sea facing|beach|ecr|shoreline|near the sea)\b/.test(t);
  const coastalDenied = /\b(inland|not coastal|nothing coastal|non-coastal)\b/.test(t)
                     || /\b(not|nothing|no)\b[^.]{0,24}\bcoastal\b/.test(t);
  if (coastalSaid && !coastalDenied) {
    found.coastal = "coastal"; notes.push("Coastal site — the PWD coastal extra applies");
  } else if (coastalDenied) { found.coastal = "inland"; notes.push("Inland site"); }

  const face = t.match(/\b(north|south|east|west|north[- ]east|north[- ]west|south[- ]east|south[- ]west)\s*(?:facing|face|frontage|road)/)
            || t.match(/\broad (?:is (?:on|to) the |on the |to the )(north|south|east|west)/);
  if (face) {
    const deg: Record<string, number> = { north: 0, "north-east": 45, east: 90, "south-east": 135,
      south: 180, "south-west": 225, west: 270, "north-west": 315 };
    const key = face[1].replace(/\s/g, "-");
    if (deg[key] !== undefined) { found.facing = deg[key]; notes.push(`Road faces ${face[1]}`); }
  }

  // sizes stated against a room — "bedroom 12 x 14", "kitchen of 10 by 8 ft"
  for (const [type, words] of ROOM_WORDS) {
    for (const w of words) {
      const re = new RegExp(w + "[^.\\n]{0,24}?(\\d{1,2}(?:\\.\\d)?)\\s*(?:ft|feet|')?\\s*(?:x|×|by)\\s*(\\d{1,2}(?:\\.\\d)?)");
      const hit = t.match(re);
      if (hit) {
        found.rooms.push({ type, w: Number(hit[1]), h: Number(hit[2]), label: w });
        notes.push(`${w} stated as ${hit[1]} × ${hit[2]} ft`);
        break;
      }
    }
    if (words.some(x => t.includes(" " + x)) && ["pooja", "office", "utility", "balcony", "parking"].includes(type))
      found.extras.push(type);
  }

  const fam = t.match(/(?:family of|household of)\s*(\d|one|two|three|four|five|six|seven|eight)/);
  if (fam) found.family = numAt(fam[1]);
  if (/\b(elderly|parents|grandparent|senior)\b/.test(t)) found.elderly = 1;
  if (/\b(children|kids|daughter|son)\b/.test(t)) found.children = 2;
  if (found.extras.length) notes.push("Also asked for: " + found.extras.join(", "));

  return { found, notes };
}
