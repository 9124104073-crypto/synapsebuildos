import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import * as E from "@engine";
import { createBuilder } from "@scene3d";
import type { Model } from "../model";

/* The house, in three dimensions.

   The geometry is not written here — it comes from web/scene3d.js, the same
   builder the original page uses, so the two cannot drift. What lives here is
   the part React owns: a renderer tied to the element's size, a camera you
   can orbit, a sun you can move through the day, and rebuilding the group
   when the model changes.

   The scene is set up once. A model change replaces one group; it does not
   tear down the renderer, which is what makes dragging a wall feel immediate
   rather than like a page load. */
export default function View3D({ m, furniture, roof, hour }:
  { m: Model; furniture: boolean; roof: boolean; hour: number }) {
  const host = useRef<HTMLDivElement>(null);
  const world = useRef<{
    renderer: THREE.WebGLRenderer; scene: THREE.Scene; camera: THREE.PerspectiveCamera;
    controls: OrbitControls; sun: THREE.DirectionalLight; shell: THREE.Group | null;
    spinners: THREE.Object3D[]; frame: number;
  } | null>(null);
  const [err, setErr] = useState("");

  // ---- set the world up once -------------------------------------------
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch {
      setErr("This browser or machine has no WebGL, so the 3D view cannot draw. "
           + "The plan, the costs and the exports all still work.");
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const css = getComputedStyle(document.documentElement).getPropertyValue("--background").trim();
    scene.background = new THREE.Color(css || "#fafaf8");

    const camera = new THREE.PerspectiveCamera(52, 1, 0.5, 900);
    camera.position.set(60, 52, 78);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.maxPolarAngle = Math.PI / 2.05;     // never underneath the site
    controls.target.set(0, 6, 0);

    scene.add(new THREE.HemisphereLight(0xdfe7f2, 0x6b6a5f, 1.25));
    scene.add(new THREE.AmbientLight(0xffffff, 0.25));
    const sun = new THREE.DirectionalLight(0xfff2dc, 1.5);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    const cam = sun.shadow.camera as THREE.OrthographicCamera;
    cam.left = -90; cam.right = 90; cam.top = 90; cam.bottom = -90; cam.far = 320;
    scene.add(sun, sun.target);

    const resize = () => {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      renderer.setSize(r.width, r.height, false);
      camera.aspect = r.width / r.height;
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    const state = { renderer, scene, camera, controls, sun, shell: null as THREE.Group | null,
                    spinners: [] as THREE.Object3D[], frame: 0 };
    world.current = state;

    let last = 0;
    const loop = (now: number) => {
      state.frame = requestAnimationFrame(loop);
      const dt = Math.min((now - last) / 1000, 0.05); last = now;
      for (const f of state.spinners) f.rotation.y += dt * 2.2;   // the ceiling fans
      controls.update();
      renderer.render(scene, camera);
    };
    state.frame = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(state.frame);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
      world.current = null;
    };
  }, []);

  // ---- rebuild the house when the model or the toggles change ----------
  useEffect(() => {
    const w = world.current;
    if (!w || !m.rooms.length) return;
    let built;
    try {
      built = createBuilder(THREE, E).build(m, { furniture, roof, walking: false });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      return;
    }
    setErr("");
    if (w.shell) {
      w.scene.remove(w.shell);
      w.shell.traverse((n: any) => {
        n.geometry?.dispose?.();
        const mats = Array.isArray(n.material) ? n.material : [n.material];
        mats.forEach((mat: any) => mat?.dispose?.());
      });
    }
    w.shell = built.group;
    w.spinners = built.spinners || [];
    w.scene.add(built.group);

    // frame the plot the first time something is built
    const span = Math.max(m.plot.w, m.plot.h) || 50;
    w.controls.target.set(0, 5, 0);
    if (!w.controls.enabled || w.camera.position.length() > span * 4)
      w.camera.position.set(span * 0.9, span * 0.8, span * 1.15);
  }, [m, furniture, roof]);

  // ---- the sun, which is a real bearing, not a slider over a picture ---
  useEffect(() => {
    const w = world.current;
    if (!w) return;
    // 6am east, noon overhead, 6pm west; height follows a simple arc
    const angle = ((hour - 6) / 12) * Math.PI;
    const height = Math.max(Math.sin(angle), 0.08);
    w.sun.position.set(Math.cos(angle) * 120, height * 130, 40);
    w.sun.intensity = 0.6 + height * 1.1;
    w.sun.target.position.set(0, 0, 0);
    w.sun.target.updateMatrixWorld();
  }, [hour]);

  return (
    <div ref={host} style={{ position: "absolute", inset: 0 }}>
      {err && <div className="blank" style={{ position: "absolute", inset: 0 }}>
        <h2>The 3D view stopped</h2>
        <p>{err}</p>
      </div>}
    </div>
  );
}
