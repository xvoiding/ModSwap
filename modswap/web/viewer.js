// 3D fit viewport: the original character as a cyan outline, your model on top. Everything arrives in the character frame
// (X = its left, Y = forward, Z = up) and is shown in three.js axes (x = left, y = up, z = forward).
import * as THREE from 'three';
import { OrbitControls } from '/vendor/OrbitControls.js';

const dec = (s, T) => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new T(u.buffer); };

function toThree(a, ox = 0, oy = 0, oz = 0) {            // canonical (X,Y,Z) -> three (X,Z,Y), minus an origin given in three coords
  const n = a.length / 3, o = new Float32Array(a.length);
  for (let i = 0; i < n; i++) { o[3 * i] = a[3 * i] - ox; o[3 * i + 1] = a[3 * i + 2] - oy; o[3 * i + 2] = a[3 * i + 1] - oz; }
  return o;
}

export class Viewer {
  constructor(host) {
    this.host = host;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(32, 1, 1, 5000);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true; this.controls.dampingFactor = 0.09; this.controls.rotateSpeed = 0.8;
    this.scene.add(new THREE.HemisphereLight(0xdfe6ff, 0x20203a, 1.15));
    this.key = new THREE.DirectionalLight(0xffffff, 1.9); this.camera.add(this.key); this.key.position.set(0.6, 0.9, 1); this.scene.add(this.camera);
    this.grid = new THREE.GridHelper(400, 40, 0x3a4060, 0x1d2033); this.grid.material.transparent = true; this.grid.material.opacity = 0.7; this.scene.add(this.grid);
    this.ghost = new THREE.Group(); this.scene.add(this.ghost);
    this.outer = new THREE.Group(); this.inner = new THREE.Group(); this.outer.add(this.inner); this.scene.add(this.outer);
    this.p3 = new THREE.Vector3(); this.h = 170; this.ground = 0; this.framed = false;
    this.show = { outline: true, model: true, wire: false };
    this.t0 = performance.now(); this.alive = true;
    new ResizeObserver(() => this.resize()).observe(host); this.resize();
    const loop = () => { if (!this.alive) return; this.controls.update(); this.renderer.render(this.scene, this.camera); requestAnimationFrame(loop); };
    loop();
  }

  resize() {
    const w = this.host.clientWidth || 300, h = this.host.clientHeight || 300;
    this.renderer.setSize(w, h, false); this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
  }

  _clear(g) { while (g.children.length) { const c = g.children.pop(); c.geometry?.dispose(); if (c.material) { c.material.map?.dispose(); c.material.dispose(); } } }

  setFit(r) {
    const [cx, cy, z0] = r.info.pivot; this.p3.set(cx, z0, cy);           // pivot in three coords
    this.h = r.height || 170;
    // original outline
    this._clear(this.ghost);
    const op = toThree(dec(r.orig.pos, Float32Array)), oi = dec(r.orig.idx, Uint32Array);
    const og = new THREE.BufferGeometry(); og.setAttribute('position', new THREE.BufferAttribute(op, 3)); og.setIndex(new THREE.BufferAttribute(oi, 1));
    let ymin = 1e9; for (let i = 1; i < op.length; i += 3) ymin = Math.min(ymin, op[i]); this.ground = ymin; this.grid.position.y = ymin;
    this.fill = new THREE.Mesh(og, new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false }));
    this.edges = new THREE.LineSegments(new THREE.EdgesGeometry(og, 26), new THREE.LineBasicMaterial({ color: 0x35e0ff, transparent: true, opacity: 0.85 }));
    this.arrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(cx, ymin + 0.6, cy + this.h * 0.22), this.h * 0.2, 0x34d399, this.h * 0.06, this.h * 0.035);
    this.ghost.add(this.fill, this.edges, this.arrow);
    // your model, positioned relative to the pivot so live scale/rotate act around the pelvis/feet
    this._clear(this.inner);
    const np = toThree(dec(r.new.pos, Float32Array), this.p3.x, this.p3.y, this.p3.z), ni = dec(r.new.idx, Uint32Array), nu = dec(r.new.uv, Float32Array);
    const ng = new THREE.BufferGeometry(); ng.setAttribute('position', new THREE.BufferAttribute(np, 3)); ng.setAttribute('uv', new THREE.BufferAttribute(nu, 2)); ng.setIndex(new THREE.BufferAttribute(ni, 1));
    ng.computeVertexNormals();
    const tex = new THREE.TextureLoader().load('data:image/jpeg;base64,' + r.atlas, () => {}); tex.colorSpace = THREE.SRGBColorSpace; tex.flipY = false; tex.anisotropy = 8;
    this.mesh = new THREE.Mesh(ng, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.82, metalness: 0.02, side: THREE.DoubleSide, wireframe: this.show.wire }));
    this.inner.add(this.mesh);
    this.live({ sx: 1, sy: 1, sz: 1, yaw: 0, dx: 0, dy: 0, dz: 0 });
    this.apply();
    if (!this.framed) { this.setView('front'); this.framed = true; }
  }

  live(r) {   // r: relative change since the last real fit
    this.outer.scale.set(r.sx, r.sy, r.sz);
    this.outer.position.set(this.p3.x + r.dx, this.p3.y + r.dz, this.p3.z + r.dy);
    this.inner.rotation.y = -r.yaw * Math.PI / 180;
  }

  apply() {
    if (this.ghost) this.ghost.visible = this.show.outline;
    this.outer.visible = this.show.model;
    if (this.mesh) this.mesh.material.wireframe = this.show.wire;
  }
  toggle(k, v) { this.show[k] = v; this.apply(); }

  setView(name) {
    const h = this.h, c = new THREE.Vector3(this.p3.x, this.ground + h * 0.5, this.p3.z), d = h * 2.9;
    const pos = { front: [0, 0.04, 1], side: [-1, 0.04, 0], top: [0, 1, -0.001], orbit: [0.72, 0.28, 0.9] }[name] || [0, 0, 1];
    const v = new THREE.Vector3(...pos).normalize().multiplyScalar(d).add(c);
    this._tween(v, c);
  }

  _tween(pos, target) {
    const p0 = this.camera.position.clone(), t0 = this.controls.target.clone(), s = performance.now(), D = 520;
    const step = () => {
      const k = Math.min(1, (performance.now() - s) / D), e = 1 - Math.pow(1 - k, 3);
      this.camera.position.lerpVectors(p0, pos, e); this.controls.target.lerpVectors(t0, target, e);
      this.camera.up.set(0, 1, 0); if (k < 1) requestAnimationFrame(step);
    };
    step();
  }
  dispose() { this.alive = false; this.renderer.dispose(); this.renderer.domElement.remove(); }
}
