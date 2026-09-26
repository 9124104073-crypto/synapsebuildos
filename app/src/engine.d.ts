/* engine.js is plain JavaScript, shared with the other pages and mirrored by
   the Python engines. It is imported, never copied, so there is one set of
   rules; this only tells TypeScript that it exists. */
declare module "@engine" {
  const anything: any;
  export = anything;
}
