/* engine.js is plain JavaScript, shared with the other pages and mirrored by
   the Python engines. It is imported, never copied, so there is one set of
   rules; this only tells TypeScript that it exists. */
declare module "@engine" {
  const anything: any;
  export = anything;
}

declare module "@scene3d" {
  export function createBuilder(THREE: any, E: any): {
    build(model: any, opts?: any): { group: any; colliders: any[]; stairZones: any[]; spinners: any[] };
    wallPlan(model: any): any[];
  };
}

declare module "@exports" {
  export function buildIfc(model: any, walls: (m: any) => any[]): string;
  export function buildDxf(model: any, walls: (m: any) => any[]): string;
  export function buildBoq(model: any, walls: (m: any) => any[]): string;
  export function buildObj(model: any, walls: (m: any) => any[]): string;
}
