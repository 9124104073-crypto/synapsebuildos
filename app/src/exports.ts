/* Getting the design out of the tool.

   Four formats, four audiences: IFC for the architect's BIM software, DXF for
   the draughtsman, OBJ for anyone with a 3D viewer, and a bill of quantities
   for whoever is pricing it.

   The writers themselves are in web/exports.js — the same ones the original
   page uses, kept because they were written against what the receiving
   software actually accepts. They are handed the model and the wall plan the
   3D view drew, so an export describes the building that was on screen. */
import * as THREE from "three";
import * as E from "@engine";
import { createBuilder } from "@scene3d";
import * as W from "@exports";
import type { Model } from "./model";

export function download(name: string, text: string, mime = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/** The wall segments the 3D view draws, openings included. */
const walls = (m: Model) => createBuilder(THREE, E).wallPlan(m);

export const buildIfc = (m: Model) => W.buildIfc(m, walls);
export const buildDxf = (m: Model) => W.buildDxf(m, walls);
export const buildBoq = (m: Model) => W.buildBoq(m, walls);
export const buildObj = (m: Model) => W.buildObj(m, walls);

export const exporters = [
  { id: "ifc", label: ".ifc", title: "IFC4 for BIM software",
    run: (m: Model) => download(`${m.name}.ifc`, buildIfc(m)) },
  { id: "dxf", label: ".dxf", title: "DXF R12 plan for CAD",
    run: (m: Model) => download(`${m.name}.dxf`, buildDxf(m)) },
  { id: "obj", label: ".obj", title: "OBJ massing for any 3D viewer",
    run: (m: Model) => download(`${m.name}.obj`, buildObj(m)) },
  { id: "boq", label: "BOQ", title: "Bill of quantities as a spreadsheet",
    run: (m: Model) => download(`${m.name} BOQ.csv`, buildBoq(m), "text/csv") },
  { id: "json", label: ".json", title: "The model itself, to reopen or hand over",
    run: (m: Model) => download(`${m.name}.json`, JSON.stringify(m, null, 2), "application/json") },
];
