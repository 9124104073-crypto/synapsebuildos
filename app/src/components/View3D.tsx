import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { PointerLockControls } from "three/examples/jsm/controls/PointerLockControls.js";
import * as E from "@engine";
import { createBuilder } from "@scene3d";
import { update, type Model } from "../model";

/* The house, in three dimensions.

   The geometry is not written here — it comes from web/scene3d.js, the same
   builder the original page uses, so the two cannot drift. What lives here is
   the part React owns: a renderer tied to the element's size, a camera you
   can orbit, a sun you can move through the day, and rebuilding the group
   when the model changes.

   The scene is set up once. A model change replaces one group; it does not
   tear down the renderer, which is what makes dragging a wall feel immediate
   rather than like a page load.

   The walkthrough is the original page's too: pointer-lock look, WASD to
   move, walls from the builder's collider list, stairs as ramps the eye
   climbs. */

type Collider = { x: number; z: number; hw: number; hd: number; y0: number; y1: number };
type StairZone = { x0: number; y0: number; x1: number; y1: number; from: number;
                   len: number; base: number; alongZ: boolean };

const RADIUS = 1.1;
const { EYE, FLOOR_H } = E as { EYE: number; FLOOR_H: number };

export default function View3D({ m, furniture, roof, hour, walking, onWalking }:
  { m: Model; furniture: boolean; roof: boolean; hour: number;
    walking: boolean; onWalking: (on: boolean) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const world = useRef<{
    renderer: THREE.WebGLRenderer; scene: THREE.Scene; camera: THREE.PerspectiveCamera;
    controls: OrbitControls; walk: PointerLockControls; sun: THREE.DirectionalLight;
    shell: THREE.Group | null; spinners: THREE.Object3D[]; frame: number;
    colliders: Collider[]; stairZones: StairZone[]; keys: Record<string, boolean>;
    walking: boolean; framed: boolean;
  } | null>(null);
  const [err, setErr] = useState("");
  const mRef = useRef(m);
  mRef.current = m;
  const walkRef = useRef(onWalking);
  walkRef.current = onWalking;

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
    // PCFSoftShadowMap was removed in three r186; PCF is the softest that remains.
    renderer.shadowMap.type = THREE.PCFShadowMap;
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

    const walk = new PointerLockControls(camera, renderer.domElement);
    walk.addEventListener("unlock", () => walkRef.current(false));
    /* A refused lock (no user gesture, browser policy) must not strand the
       visitor in walk mode with mouse-look dead and Esc doing nothing. */
    const onLockError = () => walkRef.current(false);
    document.addEventListener("pointerlockerror", onLockError);

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

    const keys: Record<string, boolean> = {};
    const onKey = (e: KeyboardEvent) => { keys[e.code] = e.type === "keydown"; };
    addEventListener("keydown", onKey);
    addEventListener("keyup", onKey);

    const state = { renderer, scene, camera, controls, walk, sun, shell: null as THREE.Group | null,
                    spinners: [] as THREE.Object3D[], frame: 0,
                    colliders: [] as Collider[], stairZones: [] as StairZone[],
                    keys, walking: false, framed: false };
    world.current = state;

    /* Axis-separated collision: try X, then Z. Sliding along a wall feels
       right and stops the player shooting through a 6-inch partition. */
    const fwd = new THREE.Vector3(), sideV = new THREE.Vector3();
    const blocked = (x: number, z: number, y: number) =>
      state.colliders.some(c =>
        y >= c.y0 - .5 && y <= c.y1 + .5 &&
        Math.abs(x - c.x) < c.hw + RADIUS && Math.abs(z - c.z) < c.hd + RADIUS);

    const walkStep = (dt: number) => {
      const speed = (state.keys.ShiftLeft || state.keys.ShiftRight ? 17 : 9) * dt;
      camera.getWorldDirection(fwd); fwd.y = 0; fwd.normalize();
      sideV.crossVectors(fwd, camera.up).normalize();
      let dx = 0, dz = 0;
      if (state.keys.KeyW) { dx += fwd.x * speed; dz += fwd.z * speed; }
      if (state.keys.KeyS) { dx -= fwd.x * speed; dz -= fwd.z * speed; }
      if (state.keys.KeyD) { dx += sideV.x * speed; dz += sideV.z * speed; }
      if (state.keys.KeyA) { dx -= sideV.x * speed; dz -= sideV.z * speed; }
      if (!dx && !dz) return;

      const mm = mRef.current;
      const cx = mm.plot.w / 2, cz = mm.plot.h / 2;
      const y = camera.position.y;
      const nx = camera.position.x + dx, nz = camera.position.z + dz;
      if (!blocked(nx, camera.position.z, y)) camera.position.x = nx;
      if (!blocked(camera.position.x, nz, y)) camera.position.z = nz;

      // stairs: height follows progress along the run
      const px = camera.position.x + cx, pz = camera.position.z + cz;
      let ground: number | null = null;
      for (const s of state.stairZones) {
        if (px >= s.x0 && px <= s.x1 && pz >= s.y0 && pz <= s.y1) {
          const along = (s.alongZ ? pz : px) - s.from;
          ground = s.base + Math.min(Math.max(along / s.len, 0), 1) * FLOOR_H;
          break;
        }
      }
      if (ground === null) {
        // stand on whichever floor slab is under the player
        let best = 0;
        for (const r of mm.rooms) {
          if (px < r.x || px > r.x + r.w || pz < r.y || pz > r.y + r.h) continue;
          const lvl = r.floor * FLOOR_H;
          if (lvl <= camera.position.y - EYE + 2.5 && lvl >= best) best = lvl;
        }
        ground = best;
      }
      camera.position.y += (ground + EYE - camera.position.y) * Math.min(dt * 12, 1);
    };

    let last = 0;
    const loop = (now: number) => {
      state.frame = requestAnimationFrame(loop);
      const dt = Math.min((now - last) / 1000, 0.05); last = now;
      for (const f of state.spinners) f.rotation.y += dt * 2.2;   // the ceiling fans
      if (state.walking) walkStep(dt); else controls.update();
      renderer.render(scene, camera);
    };
    state.frame = requestAnimationFrame(loop);

    let downX = 0, downY = 0;
    const onPointerDown = (e: MouseEvent) => { downX = e.clientX; downY = e.clientY; };
    const onPointerUp = (e: MouseEvent) => {
      if (state.walking || !state.shell) return;
      if (Math.hypot(e.clientX - downX, e.clientY - downY) > 6) return;
      const r = renderer.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - r.left) / r.width) * 2 - 1,
        -((e.clientY - r.top) / r.height) * 2 + 1
      );
      const ray = new THREE.Raycaster();
      ray.setFromCamera(mouse, camera);
      const hits = ray.intersectObjects(state.shell.children, true);
      for (const h of hits) {
        let o: THREE.Object3D | null = h.object;
        while (o && o !== state.shell) {
          if (o.userData && o.userData.id) {
            const roomId = o.userData.id;
            update(mm => {
              mm.selected = roomId;
              const rObj = mm.rooms.find(x => x.id === roomId);
              if (rObj) mm.floor = rObj.floor;
            }, false);
            return;
          }
          o = o.parent;
        }
      }
    };
    renderer.domElement.addEventListener("mousedown", onPointerDown);
    renderer.domElement.addEventListener("mouseup", onPointerUp);

    return () => {
      renderer.domElement.removeEventListener("mousedown", onPointerDown);
      renderer.domElement.removeEventListener("mouseup", onPointerUp);
      cancelAnimationFrame(state.frame);
      removeEventListener("keydown", onKey);
      removeEventListener("keyup", onKey);
      document.removeEventListener("pointerlockerror", onLockError);
      ro.disconnect();
      walk.dispose();
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
      built = createBuilder(THREE, E).build(m, {
        furniture, roof: roof || walking, walking,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      return;
    }
    setErr("");
    w.colliders = built.colliders || [];
    w.stairZones = built.stairZones || [];
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

    // frame the plot the first time something is built — never mid-walk,
    // where resetting the camera would throw the visitor back outside
    const span = Math.max(m.plot.w, m.plot.h) || 50;
    if (!w.framed) {
      w.framed = true;
      w.controls.target.set(0, 5, 0);
      w.camera.position.set(span * 0.9, span * 0.8, span * 1.15);
    }
  }, [m, furniture, roof, walking]);

  // ---- enter and leave the walkthrough ----------------------------------
  useEffect(() => {
    const w = world.current;
    if (!w) return;
    w.walking = walking;
    w.controls.enabled = !walking;
    if (walking) {
      const mm = mRef.current;
      const start = mm.rooms.find(r => r.floor === 0 && r.type === "living")
                 || mm.rooms.find(r => r.floor === 0) || mm.rooms[0];
      if (start) w.camera.position.set(start.x + start.w / 2 - mm.plot.w / 2, EYE,
                                       start.y + start.h / 2 - mm.plot.h / 2);
      w.camera.lookAt(0, EYE, 0);
      w.walk.lock();
    } else {
      if (w.walk.isLocked) w.walk.unlock();
      w.camera.position.set(58, 48, 64);
      w.controls.target.set(0, 5, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [walking]);

  // ---- the sun & sky, which adjusts dynamically across hours ---
  useEffect(() => {
    const w = world.current;
    if (!w) return;
    const angle = ((hour - 6) / 12) * Math.PI;
    const isDay = hour >= 6 && hour <= 18;
    const height = Math.max(Math.sin(angle), 0.02);
    w.sun.position.set(Math.cos(angle) * 120, height * 130, 40);
    w.sun.intensity = isDay ? 0.4 + height * 1.3 : 0.05;
    w.scene.background = new THREE.Color(isDay ? (getComputedStyle(document.documentElement).getPropertyValue("--background").trim() || "#fafaf8") : "#0b0f19");
    w.sun.target.position.set(0, 0, 0);
    w.sun.target.updateMatrixWorld();
  }, [hour]);

  return (
    <div ref={host} style={{ position: "absolute", inset: 0 }}>
      {err && <div className="blank" style={{ position: "absolute", inset: 0 }}>
        <h2>The 3D view stopped</h2>
        <p>{err}</p>
      </div>}
      {walking && <>
        <div className="crosshair" aria-hidden="true" />
        <div className="walkhud">W A S D to move · shift to jog ·
          walk onto the stairs to go up · Esc to exit</div>
      </>}
    </div>
  );
}
