import { Viewer } from '/viewer.js';

const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ENG = { unreal: ['#e9ebf3', 'UE'], unity: ['#b9bfcc', 'U'], godot: ['#6cb2ec', 'G'], source: ['#f59e0b', 'S'], source2: ['#fb923c', 'S2'], gamemaker: ['#34d399', 'GM'], rpgmaker: ['#a78bfa', 'RM'], cryengine: ['#f87171', 'CE'], unknown: ['#6b7280', '?'] };
const IMG_EXT = /\.(png|jpe?g|tga|bmp|tiff?|webp|dds)$/i;

const S = {
  games: [], cur: null, chars: null, fam: 0, target: 0, sid: Math.random().toString(36).slice(2, 12), files: [], info: null, parts: null,
  up: '', fwd: '', adj: { scale: 1, width: 1, height: 1, depth: 1, yaw: 0, dx: 0, dy: 0, dz: 0 }, last: null, fit: null, filter: 'all', q: '', installed: null, fseq: 0, busy: 0, vp: null, viewer: null,
};
const DEF = { scale: 1, width: 1, height: 1, depth: 1, yaw: 0, dx: 0, dy: 0, dz: 0 };

async function api(path, body, method) {
  const r = await fetch(path, { method: method || (body ? 'POST' : 'GET'), body: body ? JSON.stringify(body) : undefined });
  const j = await r.json(); if (j.error) throw new Error(j.error); return j;
}
function toast(msg, ok) { const t = document.createElement('div'); t.className = 'toast' + (ok ? ' ok' : ''); t.textContent = msg; $('#toasts').appendChild(t); setTimeout(() => { t.style.transition = '.4s'; t.style.opacity = 0; setTimeout(() => t.remove(), 400); }, 5200); }
function countTo(el, n) { const s = performance.now(), D = 700; const f = t => { const k = Math.min(1, (t - s) / D); el.textContent = Math.round(n * (1 - Math.pow(1 - k, 3))).toLocaleString(); if (k < 1) requestAnimationFrame(f); }; requestAnimationFrame(f); }
async function poll(id, onlog) { for (;;) { const j = await api('/api/job?id=' + id); onlog && onlog(j.log); if (j.done) { if (j.error) throw new Error(j.error); return j.result; } await sleep(600); } }

/* ---------------------------------------------------------------- library */
async function loadGames() { S.games = (await api('/api/games')).games; renderGames(); }
function filtered() {
  const q = S.q.trim().toLowerCase();
  return S.games.filter(g => (!q || g.name.toLowerCase().includes(q)) && (S.filter === 'all' || (S.filter === 'swap' ? g.supported : g.engine === S.filter)))
    .sort((a, b) => (b.supported - a.supported) || a.name.localeCompare(b.name));
}
function renderGames() {
  const engines = [...new Set(S.games.map(g => g.engine))];
  $('#chips').innerHTML = [['all', 'All'], ['swap', 'Swappable'], ...engines.map(e => [e, (ENG[e] ? { unreal: 'Unreal', unity: 'Unity', godot: 'Godot', source: 'Source', source2: 'Source 2', gamemaker: 'GameMaker', rpgmaker: 'RPG Maker', cryengine: 'CryEngine', unknown: 'Unknown' }[e] : e)])]
    .map(([k, l]) => `<button class="chip ${S.filter === k ? 'on' : ''}" data-f="${k}">${l}</button>`).join('');
  $$('#chips .chip').forEach(c => c.onclick = () => { S.filter = c.dataset.f; renderGames(); });
  const list = filtered();
  $('#games').innerHTML = list.map((g, i) => {
    const [col] = ENG[g.engine] || ENG.unknown;
    return `<div class="game ${S.cur && S.cur.id === g.id ? 'sel' : ''}" data-id="${esc(g.id)}" style="--i:${Math.min(i, 14)};--ec:${col}">
      <div class="tile">${esc(g.name[0] || '?').toUpperCase()}</div>
      <div style="min-width:0"><div class="gname">${esc(g.name)}</div>
      <div class="gsub"><span class="dot ${g.supported ? '' : 'off'}"></span>${esc(g.label)}</div></div></div>`;
  }).join('') || (S.games.length ? '<p class="mut" style="padding:10px">No match.</p>' : '<p class="mut" style="padding:10px;line-height:1.5">No games yet. Scan Steam or add a game by its .exe.</p>');
  $$('#games .game').forEach(e => e.onclick = () => selectGame(e.dataset.id));
  $('#foot').textContent = S.games.length ? `${S.games.length} games · ${S.games.filter(g => g.supported).length} swappable` : 'Runs entirely on your PC.';
}
async function scanSteam(btn) {
  const b = btn || $('#scan'); const lab = $('span', b); const old = lab && lab.textContent; b.disabled = true; if (lab) lab.textContent = 'Scanning...';
  try { const r = await api('/api/scan_steam', {}); S.games = r.games; renderGames(); toast(r.new ? `Found ${r.new} new game${r.new > 1 ? 's' : ''}` : 'Library is up to date', true); }
  catch (e) { toast(e.message); } finally { b.disabled = false; if (lab) lab.textContent = old; }
}
async function addExe() {
  let p = ''; try { p = (await api('/api/pick_exe', {})).path; } catch (e) { }
  if (!p) p = prompt('Paste the path to the game .exe'); if (!p) return;
  try { const r = await api('/api/add', { exe: p }); S.games = r.games; renderGames(); toast(`Added ${r.game.name} (${r.game.label})`, true); selectGame(r.game.id); } catch (e) { toast(e.message); }
}
$('#scan').onclick = () => scanSteam(); $('#scan2').onclick = () => scanSteam($('#scan2')); $('#addbtn').onclick = addExe; $('#add2').onclick = addExe;
$('#q').oninput = e => { S.q = e.target.value; renderGames(); };

/* ---------------------------------------------------------------- workspace */
function selectGame(id) {
  S.cur = S.games.find(g => g.id === id); S.chars = null; S.fam = 0; S.target = 0; S.last = null; S.fit = null; S.installed = null;
  renderGames(); $('#empty').classList.add('hidden'); buildWork();
}

function engineBadge(g) {
  const [col, ico] = ENG[g.engine] || ENG.unknown;
  return `<div class="engine ${g.supported ? 'ok' : ''}" style="--ec:${col}"><div class="ico">${ico}</div><div><b>${esc(g.label)}</b><br><span>${esc(g.detail || 'detected from the game files')}</span></div></div>
    ${g.supported ? '<span class="tag ok">swappable</span>' : '<span class="tag warn">detected, support coming soon</span>'}`;
}

function buildWork() {
  const g = S.cur, w = $('#work'); w.classList.remove('hidden'); w.innerHTML = '';
  w.innerHTML = `<div class="ghead"><div style="flex:1;min-width:0"><h2>${esc(g.name)}</h2><div class="path">${esc(g.root)}</div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap" id="eng">${engineBadge(g)}</div></div>
      <div style="display:flex;gap:8px"><button class="btn sm ghost" id="redet">Re-detect engine</button><button class="btn sm ghost danger" id="rmgame">Remove</button></div></div>
    <div class="cols"><div class="steps" id="steps"></div><div class="viewcol" id="vcol"></div></div>`;
  $('#redet').onclick = async () => { try { const r = await api('/api/redetect', { game: g.id }); Object.assign(g, r.game); $('#eng').innerHTML = engineBadge(g); renderGames(); toast('Engine: ' + g.label, true); } catch (e) { toast(e.message); } };
  $('#rmgame').onclick = async () => { S.games = (await api('/api/remove', { game: g.id })).games; S.cur = null; w.classList.add('hidden'); $('#empty').classList.remove('hidden'); renderGames(); };
  if (!g.supported) {
    $('#steps').innerHTML = `<section class="step active"><div class="sh"><div class="num">!</div><h3>${esc(g.label)} isn't supported yet</h3></div>
      <p class="mut" style="margin:0 0 8px">ModSwap detected the engine, but can only write Unreal Engine mods right now. Unity and Godot adapters are next. You can still use this game's entry to keep track of it.</p></section>`;
    return;
  }
  $('#steps').innerHTML = [['Character', 'Pick who to replace'], ['Your model', 'Drop a file + textures'], ['Fit it', 'Size, rotate, line it up'], ['Install', 'Build + put it in the game']]
    .map(([t, s], i) => `<section class="step locked" id="st${i + 1}" style="--i:${i}"><div class="sh"><div class="num">${i + 1}</div><h3>${t}</h3><small>${s}</small></div><div id="b${i + 1}"></div></section>`).join('');
  mountViewport(); renderChars(); renderModel(); renderFit(); renderInstall(); setSteps();
}

function setSteps() {
  if (!$('#st1')) return;
  const st = [true, !!S.chars, !!(S.chars && S.info), !!(S.chars && S.info && S.fit)];
  const done = [!!S.chars, !!S.info, !!S.fit, !!S.installed];
  st.forEach((open, i) => { const el = $('#st' + (i + 1)); el.classList.toggle('locked', !open); el.classList.toggle('done', done[i]); el.classList.toggle('active', open && !done[i] && (i === 0 || done[i - 1])); });
  $('#st4') && $('#st4').classList.toggle('done', !!S.installed);
}

/* step 1: characters */
function renderChars(state) {
  const b = $('#b1'); if (!b) return;
  if (state === 'loading') { b.innerHTML = `<p class="mut" style="margin:0">Reading the game's files and checking every mesh...</p><div class="scan"><i></i></div><div class="skel"></div><div class="skel" style="animation-delay:.2s"></div><pre class="logbox" id="log1"></pre>`; return; }
  if (!S.chars) { b.innerHTML = `<p class="mut" style="margin:0 0 12px">ModSwap opens the game's files, finds every character mesh you can swap (and the props), and groups them by skeleton.</p><button class="btn pri" id="det">Detect characters &amp; items</button>`; $('#det').onclick = detect; return; }
  b.innerHTML = S.chars.characters.map((c, i) => `<div class="opt ${c.index === S.fam ? 'sel' : ''}" data-i="${c.index}" style="--i:${i}"><div class="radio"></div><div style="flex:1;min-width:0"><b>${esc(c.label)}</b><small>${c.meshes} meshes · body: ${esc(c.body.slice(0, 3).join(', '))}${c.layered ? ` · ${c.layered} layered pieces hidden` : ''}</small></div></div>`).join('')
    + `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px"><small class="mut">${S.chars.items.length} props detected (swapping props comes later)</small><button class="btn sm ghost" id="redo">Re-scan</button></div>`;
  $$('#b1 .opt').forEach(e => e.onclick = () => { S.fam = +e.dataset.i; S.target = 0; S.last = null; S.fit = null; renderChars(); renderInstall(); if (S.info) requestFit(true); });
  $('#redo').onclick = () => { S.chars = null; renderChars(); setSteps(); };
}
async function detect() {
  renderChars('loading'); const b = $('#b1');
  try { const r = await api('/api/characters', { game: S.cur.id }); S.chars = await poll(r.job, l => { const e = $('#log1'); if (e) { e.textContent = l.join('\n'); e.scrollTop = 1e9; } }); S.fam = 0; renderChars(); renderFit(); setSteps(); if (S.info) requestFit(true); }
  catch (e) { S.chars = null; renderChars(); toast(e.message); }
}

/* step 2: model maker */
async function uploadFiles(fl) {
  fl = [...fl]; if (!fl.length) return;
  const drop = $('#drop'); drop && drop.classList.add('over');
  try {
    for (const f of fl) {
      const r = await (await fetch(`/api/upload?sid=${S.sid}&name=${encodeURIComponent(f.name)}`, { method: 'PUT', body: f })).json(); if (r.error) throw new Error(r.error);
      r.names.forEach(n => { if (!S.files.includes(n)) S.files.push(n); });
    }
    S.info = await api('/api/inspect', { upload: S.sid }); S.parts = S.info.parts.length ? S.info.parts.map(p => p.i) : [0]; S.up = ''; S.fwd = '';
    renderModel(); setSteps(); renderFit(); if (S.chars) requestFit(true);
    toast('Loaded ' + S.info.file, true);
  } catch (e) { toast(e.message); if (!S.info) { S.files = []; } renderModel(); }
  finally { drop && drop.classList.remove('over'); }
}
async function renderModel() {
  const b = $('#b2'); if (!b) return;
  if (!S.fmts) { try { S.fmts = await api('/api/formats'); } catch (e) { S.fmts = { formats: [] }; } }
  const i = S.info;
  b.innerHTML = `<div class="drop" id="drop"><div class="big"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg></div>
      <div><b style="color:var(--tx)">${i ? 'Add more files' : 'Drop your model here'}</b></div><div style="font-size:12.5px;margin-top:2px">${i ? 'textures, or another model' : 'FBX, OBJ, GLB, DAE, PLY... plus textures, or a .zip'}</div><input type="file" id="fi" multiple hidden></div>
    <div class="files">${S.files.map(f => `<span class="file ${IMG_EXT.test(f) ? 't' : 'm'}">${IMG_EXT.test(f) ? '🖼' : '▣'} ${esc(f)}</span>`).join('')}</div>`
    + (i ? `<div class="stats"><div class="stat"><b data-n="${i.verts}">0</b><small>vertices</small></div><div class="stat"><b data-n="${i.tris}">0</b><small>triangles</small></div><div class="stat"><b data-n="${i.materials}">0</b><small>materials</small></div><div class="stat"><b data-n="${i.textured}">0</b><small>textured</small></div></div>
      <div class="thumbs">${i.thumbs.map(t => t ? `<img src="data:image/jpeg;base64,${t}">` : '<div class="nt" title="no texture found"></div>').join('')}</div>
      ${i.parts.length > 1 ? `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px"><b style="font-size:13px">Model parts <span class="mut" style="font-weight:400">(untick anything you don't want)</span></b><span><button class="btn sm ghost" id="pall">all</button> <button class="btn sm ghost" id="pnone">none</button></span></div>
        <div class="parts">${i.parts.map(p => `<div class="part ${S.parts.includes(p.i) ? 'on' : ''}" data-i="${p.i}"><div class="sw"></div><span title="${esc(p.name)}">${esc(p.name)}</span><small>${p.tris.toLocaleString()} tris</small></div>`).join('')}</div>` : ''}
      <div class="row2" style="margin-top:10px"><div><label class="f">Up axis ${S.up ? '' : `<span class="auto">auto: ${esc(i.up)}</span>`}</label><select id="upsel">${['', '+Y', '+Z', '-Y', '-Z', '+X', '-X'].map(v => `<option value="${v}" ${S.up === v ? 'selected' : ''}>${v || 'Auto (' + i.up + ')'}</option>`).join('')}</select></div>
      <div><label class="f">Faces ${S.fwd ? '' : `<span class="auto">auto: ${esc(i.forward)}</span>`}</label><select id="fwsel">${['', '+X', '-X', '+Y', '-Y', '+Z', '-Z'].map(v => `<option value="${v}" ${S.fwd === v ? 'selected' : ''}>${v || 'Auto (' + i.forward + ')'}</option>`).join('')}</select></div></div>` : '')
    + `<div class="fmtstrip" style="margin-top:12px;justify-content:flex-start">${(S.fmts.formats || []).map(f => `<span class="fmt ${f.how !== 'built in' ? 'need' : ''}" title="${esc(f.ext)} · ${esc(f.how)}${f.how !== 'built in' && !S.fmts.blender ? ' (Blender not found)' : ''}">${esc(f.name)}</span>`).join('')}</div>`;
  const drop = $('#drop'), fi = $('#fi');
  drop.onclick = () => fi.click(); fi.onchange = () => uploadFiles(fi.files);
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); }; drop.ondragleave = () => drop.classList.remove('over');
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); uploadFiles(e.dataTransfer.files); };
  $$('#b2 [data-n]').forEach(el => countTo(el, +el.dataset.n));
  $$('#b2 .part').forEach(p => p.onclick = () => { const k = +p.dataset.i; S.parts = S.parts.includes(k) ? S.parts.filter(x => x !== k) : [...S.parts, k]; p.classList.toggle('on'); if (!S.parts.length) return toast('Keep at least one part'); requestFit(); });
  $('#pall') && ($('#pall').onclick = () => { S.parts = i.parts.map(p => p.i); renderModel(); requestFit(); });
  $('#pnone') && ($('#pnone').onclick = () => { S.parts = []; renderModel(); });
  $('#upsel') && ($('#upsel').onchange = e => { S.up = e.target.value; renderModel(); requestFit(); });
  $('#fwsel') && ($('#fwsel').onchange = e => { S.fwd = e.target.value; renderModel(); requestFit(); });
}

/* step 3: fit */
const SL = [['scale', 'Size', 40, 200, '%', 100], ['width', 'Width', 50, 200, '%', 100], ['height', 'Height', 50, 200, '%', 100], ['depth', 'Depth (front to back)', 50, 200, '%', 100],
  ['yaw', 'Rotation', -180, 180, '°', 1], ['dx', 'Left / right', -40, 40, ' cm', 1], ['dy', 'Forward / back', -40, 40, ' cm', 1], ['dz', 'Up / down', -30, 30, ' cm', 1]];
const fmtv = (k, v, u, m) => (m === 100 ? Math.round(v * 100) : Math.round(v * 10) / 10) + u;
function renderFit() {
  const b = $('#b3'); if (!b) return;
  if (!S.info) { b.innerHTML = '<p class="mut" style="margin:0">Load a model first, then line it up against the original outline in the 3D view.</p>'; return; }
  const tg = S.fit && S.fit.targets && S.fit.targets.length > 1 ? `<div style="margin-bottom:8px"><label class="f">Preview body (your settings apply to all ${S.fit.targets.length})</label><div class="seg" id="tg" style="display:inline-flex">${S.fit.targets.map((t, i) => `<button data-i="${i}" class="${i === S.target ? 'on' : ''}">${esc(String(t).replace(/^.*SK_NPC_|^.*SK_/, ''))}</button>`).join('')}</div></div>` : '';
  b.innerHTML = `${tg}<div class="quick"><button class="btn sm" data-q="-90">⟲ 90°</button><button class="btn sm" data-q="90">⟳ 90°</button><button class="btn sm" data-q="180">Turn around</button><button class="btn sm ghost" data-q="reset">Reset</button></div>`
    + SL.map(([k, l, mn, mx, u, m]) => `<div class="sl"><div class="top"><span>${l}</span><span id="v_${k}">${fmtv(k, S.adj[k], u, m)}</span></div><input type="range" id="r_${k}" min="${mn}" max="${mx}" step="${m === 100 ? 1 : 0.5}" value="${S.adj[k] * m}"></div>`).join('');
  SL.forEach(([k, l, mn, mx, u, m]) => { const r = $('#r_' + k); const paint = () => r.style.setProperty('--p', ((r.value - mn) / (mx - mn) * 100) + '%'); paint();
    r.oninput = () => { S.adj[k] = +r.value / m; $('#v_' + k).textContent = fmtv(k, S.adj[k], u, m); paint(); liveUpdate(); }; });
  $$('#b3 [data-q]').forEach(bt => bt.onclick = () => { const q = bt.dataset.q; if (q === 'reset') Object.assign(S.adj, DEF); else { let y = S.adj.yaw + +q; y = ((y + 180) % 360 + 360) % 360 - 180; S.adj.yaw = y; } renderFit(); liveUpdate(); });
  $$('#tg button').forEach(bt => bt.onclick = () => { S.target = +bt.dataset.i; S.last = null; renderFit(); requestFit(true); });
}
function liveUpdate() {
  const a = S.adj, l = S.last || DEF;
  if (S.viewer && S.fit) S.viewer.live({ sx: a.scale * a.width / (l.scale * l.width), sy: a.scale * a.height / (l.scale * l.height), sz: a.scale * a.depth / (l.scale * l.depth), yaw: a.yaw - l.yaw, dx: a.dx - l.dx, dy: a.dy - l.dy, dz: a.dz - l.dz });
  clearTimeout(S.ft); S.ft = setTimeout(() => requestFit(), 380);
}
function payload() { return { game: S.cur.id, family: S.fam, target: S.target, upload: S.sid, parts: S.parts, up: S.up, forward: S.fwd, scale: S.adj.scale, ...S.adj }; }
async function requestFit(first) {
  if (!S.chars || !S.info || !S.parts || !S.parts.length) return;
  const seq = ++S.fseq; setBusy(1, first ? 'Rigging your model...' : 'Updating...');
  try {
    const r = await api('/api/fit', payload()); if (seq !== S.fseq) return;
    S.fit = r; S.last = { ...S.adj }; S.viewer.setFit(r); $('#ph') && $('#ph').classList.add('hide'); setSteps(); if (!$('#go')) renderInstall();
    if ($('#tg') === null && r.targets.length > 1 || (r.targets.length > 1 && $$('#tg button').length !== r.targets.length)) renderFit();
    const fl = $('#fwinfo'); if (fl) fl.textContent = 'faces ' + r.info.forward;
  } catch (e) { if (seq === S.fseq) toast(e.message); } finally { if (seq === S.fseq) setBusy(0); }
}
function setBusy(on, txt) { const el = $('#busy'); if (!el) return; if (txt) $('#busyt').textContent = txt; el.classList.toggle('on', !!on); }

/* viewport */
function mountViewport() {
  if (!S.vp) {
    const vp = document.createElement('div'); vp.className = 'vp';
    vp.innerHTML = `<div class="ph" id="ph"><div><svg class="silh" viewBox="0 0 100 130" fill="none" stroke="#35e0ff" stroke-width="1.6" stroke-linejoin="round"><circle cx="50" cy="16" r="10"/><path d="M36 32h28l8 30-7 3-5-18v30l4 38h-9l-5-36-5 36h-9l4-38V47l-5 18-7-3z"/></svg><b style="color:var(--tx)">Your 3D fit view</b><br><span>Load a model and it shows up here,<br>lined up over the original outline.</span></div></div>
      <div class="hud tl"><div class="seg" id="views"><button data-v="front" class="on">Front</button><button data-v="side">Side</button><button data-v="top">Top</button><button data-v="orbit">3D</button></div></div>
      <div class="hud tr"><div class="seg" id="tgl"><button data-t="outline" class="on">Outline</button><button data-t="model" class="on">Model</button><button data-t="wire">Wire</button></div></div>
      <div class="busy" id="busy"><div class="spin"></div><span id="busyt">Working...</span></div>
      <div class="hud bl"><span class="leg"><i style="background:#35e0ff"></i>original outline</span><span class="leg"><i style="background:#ff9d57"></i>your model</span><span class="leg"><i style="background:#34d399"></i><span id="fwinfo">forward</span></span></div>
      <div class="hint">drag to orbit · scroll to zoom</div>`;
    S.vp = vp; S.viewer = new Viewer(vp);
    $$('#views button', vp).forEach(b => b.onclick = () => { $$('#views button', vp).forEach(x => x.classList.toggle('on', x === b)); S.viewer.setView(b.dataset.v); });
    $$('#tgl button', vp).forEach(b => b.onclick = () => { const on = !b.classList.contains('on'); b.classList.toggle('on', on); S.viewer.toggle(b.dataset.t, on); });
  }
  $('#vcol').appendChild(S.vp); S.viewer.resize();
  if (!S.fit) $('#ph').classList.remove('hide');
}

/* step 4: install */
function renderInstall(state, log) {
  const b = $('#b4'); if (!b) return;
  if (!S.fit) { b.innerHTML = '<p class="mut" style="margin:0">When the fit looks right, hit install. ModSwap builds the mod and drops it into the game for you.</p>'; return; }
  const nm = ($('#modname') && $('#modname').value) || (S.info.file.replace(/\.[^.]+$/, '') || 'my-mod');
  b.innerHTML = `<label class="f">Mod name</label><input type="text" id="modname" value="${esc(nm)}" style="margin-bottom:12px">
    <button class="btn pri big" id="go">${state === 'busy' ? '<div class="spin"></div> Building...' : 'Install into the game'}</button>
    ${state === 'busy' ? `<div class="stages" id="stages">${[0, 1, 2, 3].map(() => '<div class="stage"></div>').join('')}</div><pre class="logbox" id="log4">${esc((log || []).join('\n'))}</pre>` : ''}
    ${S.installed ? `<div class="done-card"><div class="check"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg></div><div style="flex:1;min-width:0"><b>Installed</b><div class="mut" style="font-size:12.5px;word-break:break-all">Launch the game and your model is in. Delete it any time with Undo.</div></div><button class="btn sm danger" id="undo">Undo</button></div>` : ''}`;
  $('#go').onclick = install; $('#undo') && ($('#undo').onclick = undo);
}
async function install() {
  renderInstall('busy', ['starting...']); $('#go').disabled = true;
  const name = $('#modname').value; let stage = 0;
  const marks = [/reading|scan|mesh layout|character group/i, /rigging|autorig|swapped|texture/i, /pack|built/i, /install/i];
  try {
    const r = await api('/api/apply', { ...payload(), name });
    await poll(r.job, l => { const e = $('#log4'); if (e) { e.textContent = l.join('\n'); e.scrollTop = 1e9; } const txt = l.join('\n'); marks.forEach((m, i) => { if (m.test(txt)) stage = Math.max(stage, i); });
      $$('#stages .stage').forEach((s, i) => { s.className = 'stage ' + (i < stage ? 'ok' : i === stage ? 'on' : ''); }); });
    S.installed = true; renderInstall(); setSteps(); toast('Installed. Launch the game!', true);
  } catch (e) { renderInstall(); toast(e.message); }
}
async function undo() { try { const r = await api('/api/restore', { game: S.cur.id }); S.installed = null; renderInstall(); setSteps(); toast(r.removed.length ? 'Mod removed' : 'Nothing to remove', true); } catch (e) { toast(e.message); } }

/* boot */
(async () => {
  try { const f = await api('/api/formats'); S.fmts = f; $('#fmts').innerHTML = f.formats.map(x => `<span class="fmt ${x.how !== 'built in' ? 'need' : ''}" title="${esc(x.ext)} · ${esc(x.how)}">${esc(x.name)}</span>`).join(''); } catch (e) { }
  await loadGames();
  window.__S = S;
})();
