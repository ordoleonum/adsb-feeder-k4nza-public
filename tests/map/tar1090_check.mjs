// tar1090 compatibility check for the K4NZA live map (k4nza/map/map.js + map.css).
//
// The live map is an unmodified tar1090; map.js rearranges its buttons and
// uses a few of its internals (the selected aircraft, its photo functions, the
// dark-mode toggle, ...). tar1090 updates itself, so this check loads the
// NEWEST tar1090 with our map.js, sample aircraft and stand-in photo services,
// and fails if anything map.js relies on is gone or no longer works.
//
// Usage: node tests/map/tar1090_check.mjs <tar1090 html dir> <k4nza map dir>
// Needs Node 22+ and Chrome / Chromium / Edge (CHROME=/path/to/browser to choose).
import { spawn } from 'node:child_process';
import http from 'node:http';
import { readFileSync, existsSync, mkdtempSync } from 'node:fs';
import { join, extname, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const [HTML_ARG, MAP_ARG] = process.argv.slice(2);
const HTML = HTML_ARG && resolve(HTML_ARG);
const MAP = MAP_ARG && resolve(MAP_ARG);
if (!HTML || !MAP || !existsSync(join(HTML, 'index.html')) || !existsSync(join(MAP, 'map.js'))) {
  console.error('usage: node tar1090_check.mjs <tar1090 html dir> <k4nza map dir>');
  process.exit(2);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- sample data: a station at O'Hare and a few aircraft ----------
const RX = { lat: 41.978, lon: -87.904 };
const PLANES = [
  { hex: 'a1b2c3', flight: 'DAL1423 ', r: 'N812DN', t: 'B739', desc: 'BOEING 737-900', alt_baro: 31000, dlat: 0.20, dlon: 0.30 },
  { hex: 'a54321', flight: 'N54321  ', r: 'N54321', t: 'C172', desc: 'CESSNA 172 Skyhawk', alt_baro: 3500, dlat: -0.10, dlon: 0.05 },
  { hex: 'ae1234', flight: 'RCH123  ', r: '07-7178', t: 'C17', desc: 'BOEING C-17 Globemaster 3', alt_baro: 24000, dlat: 0.40, dlon: -0.25, dbFlags: 1 },
  { hex: 'a0f00d', flight: 'SWA2039 ', r: 'N8631A', t: 'B38M', desc: 'BOEING 737 MAX 8', alt_baro: 12000, dlat: -0.30, dlon: -0.20 },
];
const PHOTO_HEX = 'A1B2C3'; // planespotters "has" a photo of this one only
let messages = 100000;
function aircraftJson() {
  messages += 300;
  const now = Date.now() / 1000;
  return {
    now, messages,
    aircraft: PLANES.map((p) => ({
      hex: p.hex, flight: p.flight, r: p.r, t: p.t, desc: p.desc, dbFlags: p.dbFlags || 0,
      alt_baro: p.alt_baro, gs: 300, track: 90, lat: RX.lat + p.dlat, lon: RX.lon + p.dlon,
      seen_pos: 0.4, seen: 0.2, messages: 500, rssi: -20, type: 'adsb_icao',
    })),
  };
}

// ---------- the web server: tar1090 + our files, as on the feeder ----------
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json', '.ico': 'image/x-icon', '.gif': 'image/gif', '.woff2': 'font/woff2' };
const PNG = existsSync(join(HTML, 'images/sprites.png')) ? readFileSync(join(HTML, 'images/sprites.png')) : Buffer.from([]);
let port;
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const send = (code, type, body) => { res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store', 'Access-Control-Allow-Origin': '*' }); res.end(body); };
  const p = url.pathname;
  if (p === '/data/receiver.json') return send(200, 'application/json', JSON.stringify({ version: 'check', refresh: 1000, history: 0, lat: RX.lat, lon: RX.lon }));
  if (p === '/data/aircraft.json') return send(200, 'application/json', JSON.stringify(aircraftJson()));
  if (p === '/config.js') {
    // tar1090's own config.js plus what the feeder appends (TAR1090_CONFIGJS_APPEND)
    const base = readFileSync(join(HTML, 'config.js'), 'utf8');
    const append = `\n(function(){var b='/api/k4nza/map/';var d=document,l=d.createElement('link');l.rel='stylesheet';l.href=b+'map.css';d.head.appendChild(l);var s=d.createElement('script');s.src=b+'map.js';d.head.appendChild(s);})();\n`;
    return send(200, 'application/javascript', base + append);
  }
  if (p.startsWith('/api/k4nza/map/')) {
    const name = p.slice('/api/k4nza/map/'.length);
    const f = join(MAP, name);
    if (!/^[\w.-]+$/.test(name) || !existsSync(f)) return send(404, 'text/plain', 'not found');
    return send(200, TYPES[extname(f)] || 'application/octet-stream', readFileSync(f));
  }
  if (p === '/mock/photo.jpg') return send(200, 'image/png', PNG);
  const f = resolve(HTML, '.' + (p === '/' ? '/index.html' : decodeURIComponent(p)));
  if (!f.startsWith(HTML) || !existsSync(f)) return send(404, 'text/plain', 'not found');
  return send(200, TYPES[extname(f)] || 'application/octet-stream', readFileSync(f));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
port = server.address().port;
const ORIGIN = `http://127.0.0.1:${port}`;

// stand-ins for planespotters.net and Wikipedia (no internet needed)
function mockExternal(url) {
  if (/planespotters\.net\/pub\/photos\/(?:\/)?hex\//i.test(url)) {
    const hex = (url.match(/hex\/([0-9a-f]{6})/i) || [])[1] || '';
    const photos = hex.toUpperCase() === PHOTO_HEX
      ? [{ thumbnail: { src: `${ORIGIN}/mock/photo.jpg` }, thumbnail_large: { src: `${ORIGIN}/mock/photo.jpg` }, link: 'https://example.invalid/photo', photographer: 'Check Photographer' }]
      : [];
    return { type: 'application/json', body: JSON.stringify({ photos }) };
  }
  if (/en\.wikipedia\.org\/w\/api\.php/.test(url)) {
    return { type: 'application/json', body: JSON.stringify({ query: { pages: { 1: { index: 1, title: 'Cessna 172', description: 'American four-seat light aircraft', thumbnail: { source: `${ORIGIN}/mock/photo.jpg` } } } } }) };
  }
  return null;
}

// ---------- the browser ----------
const CANDIDATES = [process.env.CHROME, 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].filter(Boolean);
const BROWSER = CANDIDATES.find((c) => existsSync(c));
if (!BROWSER) { console.error('no Chrome/Chromium/Edge found (set CHROME=...)'); process.exit(2); }
const debugPort = 9500 + Math.floor(Math.random() * 400);
const browser = spawn(BROWSER, ['--headless=new', `--remote-debugging-port=${debugPort}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'k4map-'))}`,
  '--no-first-run', '--no-sandbox', '--disable-gpu', '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 80 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json()).find((t) => t.type === 'page'); } catch (e) { /* starting */ }
  if (!target) await sleep(250);
}
if (!target) { console.error('browser did not start'); process.exit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r));
let id = 0;
const pending = new Map();
const errors = [];
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
ws.addEventListener('message', (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); return; }
  const p = d.params || {};
  if (d.method === 'Runtime.exceptionThrown') {
    const ex = p.exceptionDetails;
    errors.push(((ex.exception && ex.exception.description) || ex.text).split('\n')[0] + ' @ ' + (ex.url || '').split('/').pop());
  }
  if (d.method === 'Fetch.requestPaused') {
    const mock = mockExternal(p.request.url);
    if (mock) {
      ws.send(JSON.stringify({ id: ++id, method: 'Fetch.fulfillRequest', params: { requestId: p.requestId, responseCode: 200,
        responseHeaders: [{ name: 'Content-Type', value: mock.type }, { name: 'Access-Control-Allow-Origin', value: '*' }],
        body: Buffer.from(mock.body).toString('base64') } }));
    } else {
      // anything else on the internet (map tiles, ...): not needed for the check
      ws.send(JSON.stringify({ id: ++id, method: 'Fetch.failRequest', params: { requestId: p.requestId, errorReason: 'BlockedByClient' } }));
    }
  }
});
await send('Runtime.enable');
await send('Page.enable');
// only outside (https) requests are paused; our own http server answers directly
await send('Fetch.enable', { patterns: [{ urlPattern: 'https://*' }] });
const ev = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result && r.result.exceptionDetails) return { error: r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text };
  return r.result ? r.result.result.value : undefined;
};
const waitFor = async (expr, ms = 15000) => {
  const end = Date.now() + ms;
  while (Date.now() < end) { if ((await ev(`!!(${expr})`)) === true) return true; await sleep(250); }
  return false;
};

// ---------- the checks ----------
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail }); };

await send('Page.navigate', { url: `${ORIGIN}/?k4theme=light` });
const built = await waitFor(`document.documentElement.classList.contains('k4m-built')`, 30000);
if (process.env.DEBUG) console.log('page:', await ev(`JSON.stringify({href: location.href, title: document.title, html: document.documentElement.outerHTML.length, ready: document.readyState})`), errors);
check('map.js loads and builds its layout', built, built ? '' : 'html.k4m-built never set (map.js gave up or crashed)');
await waitFor(`typeof g !== 'undefined' && g.planesOrdered && g.planesOrdered.length >= ${PLANES.length}`, 20000);

// what map.js uses from tar1090
const GLOBALS = {
  'toggles.darkMode (state, toggle)': `typeof toggles !== 'undefined' && toggles.darkMode && typeof toggles.darkMode.toggle === 'function' && 'state' in toggles.darkMode`,
  'SelectedPlane': `typeof SelectedPlane !== 'undefined'`,
  'displayPhoto()': `typeof displayPhoto === 'function'`,
  'setPhotoHtml()': `typeof setPhotoHtml === 'function'`,
  'selectPlaneByHex()': `typeof selectPlaneByHex === 'function'`,
  'toggleIsolation()': `typeof toggleIsolation === 'function'`,
  'toggleFollow()': `typeof toggleFollow === 'function'`,
  'onlySelected': `typeof onlySelected !== 'undefined'`,
  'FollowSelected': `typeof FollowSelected !== 'undefined'`,
  'g.planesOrdered': `typeof g !== 'undefined' && Array.isArray(g.planesOrdered)`,
  'g.route_cache': `typeof g !== 'undefined' && 'route_cache' in g`,
  'PlaneObject.prototype.routeCheck()': `typeof PlaneObject !== 'undefined' && typeof PlaneObject.prototype.routeCheck === 'function'`,
  'loadFinished': `typeof loadFinished !== 'undefined'`,
  'planespottersAPIurl': `typeof planespottersAPIurl === 'string'`,
  'showPictures': `typeof showPictures !== 'undefined'`,
};
for (const [name, expr] of Object.entries(GLOBALS)) check('tar1090 has ' + name, (await ev(expr)) === true);

// tar1090's own page parts that map.js moves, labels or measures
const IDS = ['H', 'L', 'O', 'T', 'U', 'K', 'B', 'I', 'F', 'V', 'M', 'P', 'R', 'RP', 'settingsCog', 'toggle_sidebar_button', 'fullscreenButton',
  'expand_sidebar_button', 'header_top', 'header_side', 'selected_infoblock', 'selected_photo', 'settings_infoblock', 'sidebar_container',
  'map_container', 'map_canvas', 'replayBar', 'altitude_chart', 'search_form', 'search_input'];
const missing = await ev(`JSON.stringify(${JSON.stringify(IDS)}.filter((i) => !document.getElementById(i)))`);
check('tar1090 page has every element map.js uses', missing === '[]', missing === '[]' ? '' : 'missing: ' + missing);
for (const sel of ['.layer-switcher', '.ol-zoom', '.ol-scale-line']) check(`tar1090 page has ${sel}`, (await ev(`!!document.querySelector('${sel}')`)) === true);

// the layout map.js builds
const where = await ev(`JSON.stringify({
  top: ['H','L','O','K','T','U'].filter((i) => document.getElementById(i)?.closest('#header_top')),
  side: ['k4layers','toggle_sidebar_button','settingsCog','k4theme'].filter((i) => document.getElementById(i)?.closest('#header_side')),
  dock: ['F','I','B','RP','k4more'].filter((i) => document.getElementById(i)?.closest('#k4m-dock')),
  feeder: !!document.getElementById('k4feeder'),
  labels: [...document.querySelectorAll('[data-k4]')].filter((b) => b.querySelector('.k4m-word')).length,
})`);
const w = JSON.parse(where || '{}');
check('top bar: Home, Labels, Details, Track lbl, Tracks, Military', (w.top || []).length === 6, JSON.stringify(w.top));
check('right column: Layers, List, Settings, light/dark', (w.side || []).length === 4, JSON.stringify(w.side));
check('bottom dock: Follow, Isolate, Dim, Replay, More', (w.dock || []).length === 5, JSON.stringify(w.dock));
check('Feeder button and labelled buttons', w.feeder && w.labels >= 15, `feeder=${w.feeder} labelled=${w.labels}`);

// buttons still do their job
const lBefore = await ev(`document.getElementById('L').classList.contains('activeButton')`);
await ev(`document.getElementById('L').click()`); await sleep(800);
const lAfter = await ev(`document.getElementById('L').classList.contains('activeButton')`);
check('Labels button toggles', typeof lBefore === 'boolean' && lBefore !== lAfter, `before=${lBefore} after=${lAfter}`);
await ev(`document.getElementById('L').click()`);

await ev(`document.getElementById('k4layers').click()`); await sleep(800);
check('Layers button opens the layer list', (await ev(`document.querySelector('.layer-switcher').classList.contains('shown')`)) === true);
await ev(`document.getElementById('k4layers').click()`); await sleep(500);

const dark0 = await ev(`toggles.darkMode.state`);
await ev(`document.getElementById('k4theme').click()`); await sleep(800);
const dark1 = await ev(`toggles.darkMode.state`);
check('light/dark button switches tar1090 dark mode', typeof dark0 === 'boolean' && dark0 !== dark1 && (await ev(`document.documentElement.classList.contains('k4m-dark')`)) === dark1, `${dark0} -> ${dark1}`);
await ev(`document.getElementById('k4theme').click()`); await sleep(500);

// selected aircraft: pane, photo from planespotters, and isolate/follow functions
await ev(`selectPlaneByHex('${PHOTO_HEX.toLowerCase()}', { noDeselect: true })`);
const paneShown = await waitFor(`SelectedPlane && SelectedPlane.icao === '${PHOTO_HEX.toLowerCase()}' && getComputedStyle(document.getElementById('selected_infoblock')).display !== 'none'`, 8000);
check('selecting an aircraft shows its pane', paneShown);
const photo = await waitFor(`document.querySelector('#selected_photo img') && document.querySelector('#selected_photo img').naturalWidth > 0`, 15000);
check('aircraft photo shows (planespotters)', photo, photo ? '' : 'pane photo: ' + (await ev(`document.getElementById('selected_photo').innerHTML.slice(0, 120)`)));

// no photo of its own: map.js shows a type photo instead of an empty space
await ev(`selectPlaneByHex('a54321', { noDeselect: true })`);
const typePhoto = await waitFor(`SelectedPlane && SelectedPlane.icao === 'a54321' && SelectedPlane.psAPIresponse && SelectedPlane.psAPIresponse.k4type && document.querySelector('#selected_photo img')`, 20000);
check('type photo when there is no photo of the aircraft', typePhoto, typePhoto ? '' : 'response: ' + JSON.stringify(await ev(`SelectedPlane && SelectedPlane.psAPIresponse`)));

const iso0 = await ev(`onlySelected`);
await ev(`toggleIsolation('on')`); await sleep(400);
check('toggleIsolation("on") isolates the selected aircraft', (await ev(`onlySelected`)) === true, `before=${iso0}`);
await ev(`toggleFollow(true)`); await sleep(400);
check('toggleFollow(true) follows it', (await ev(`FollowSelected`)) === true);

const own = errors.filter((e) => !/favicon|db2|Failed to load resource/i.test(e));
check('no script errors', own.length === 0, own.slice(0, 5).join(' | '));

// ---------- report ----------
const version = existsSync(join(HTML, '..', 'version')) ? readFileSync(join(HTML, '..', 'version'), 'utf8').trim() : '?';
console.log(`tar1090 ${version} + K4NZA map.js`);
for (const r of results) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.name}${r.detail ? '  (' + r.detail + ')' : ''}`);
const failed = results.filter((r) => !r.ok).length;
console.log(failed ? `\n${failed} of ${results.length} checks FAILED` : `\nall ${results.length} checks passed`);
ws.close(); browser.kill(); server.close();
process.exit(failed ? 1 : 0);
