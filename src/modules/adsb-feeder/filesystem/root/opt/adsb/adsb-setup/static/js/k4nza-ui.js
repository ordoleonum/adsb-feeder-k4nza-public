/* Behaviour for the dashboard shell (see templates/_k4nza_nav.html).
 *  - light/dark toggle (remembered per browser)
 *  - phone menu (sidebar slides in)
 *  - live receiver status in the top bar and the home page tiles
 *  - Pi health tiles and the aircraft search box on the home page
 */
(function () {
  "use strict";

  // ---------- theme ----------
  const THEME_KEY = "k4-theme";
  function storedTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }
  function applyTheme(t) {
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-mdb-theme", t);
  }
  applyTheme(storedTheme()); // as early as possible

  function currentTheme() {
    return document.documentElement.getAttribute("data-mdb-theme") === "dark" ? "dark" : "light";
  }

  // ---------- helpers ----------
  const $id = (id) => document.getElementById(id);
  function fmt(n) {
    if (n === undefined || n === null || isNaN(n)) return "–";
    n = Number(n);
    return n >= 1000 ? n.toLocaleString() : String(Math.round(n * 10) / 10);
  }

  // ---------- live status ----------
  function setTile(id, value) {
    const el = $id(id);
    if (el) el.textContent = value;
  }

  // refreshed every 5 s; skip a round while the previous request is still
  // waiting so a slow link can't pile up requests
  let statusBusy = false;
  let statusOkAt = 0;

  // "Updated 10 s ago" under the aircraft tiles; amber when the numbers are
  // more than a minute old (the feeder isn't answering), so frozen numbers
  // never look current
  function showUpdated() {
    const tiles = $id("k4-tiles");
    if (!tiles) return;
    let el = $id("k4-tiles-updated");
    if (!el) {
      el = document.createElement("div");
      el.id = "k4-tiles-updated";
      el.className = "k4-tiles-updated";
      el.setAttribute("aria-live", "polite");
      tiles.insertAdjacentElement("afterend", el);
    }
    if (!statusOkAt) {
      el.textContent = "";
      return;
    }
    const s = Math.round((Date.now() - statusOkAt) / 1000);
    const stale = s > 60;
    el.classList.toggle("k4-stale", stale);
    if (s < 10) el.textContent = "Updated just now";
    else if (s < 120) el.textContent = `Updated ${s} s ago${stale ? " - the feeder isn't answering" : ""}`;
    else el.textContent = `Updated ${Math.round(s / 60)} min ago - the feeder isn't answering`;
  }

  // tap (or click) a tile to read its advice: tooltips don't show on phones
  function initTileNotes() {
    document.querySelectorAll(".k4-tiles").forEach((group) => {
      group.addEventListener("click", (e) => {
        const tile = e.target.closest(".k4-tile");
        if (!tile || !tile.title) return;
        let note = group.nextElementSibling;
        if (note && note.id === "k4-tiles-updated") note = note.nextElementSibling;
        if (!note || !note.classList.contains("k4-tile-note")) {
          note = document.createElement("div");
          note.className = "k4-tile-note";
          note.setAttribute("role", "status");
          const after = group.nextElementSibling && group.nextElementSibling.id === "k4-tiles-updated"
            ? group.nextElementSibling : group;
          after.insertAdjacentElement("afterend", note);
        }
        const same = note.dataset.for === (tile.id || tile.title) && !note.hidden;
        group.querySelectorAll(".k4-tile.k4-tile-open").forEach((t) => t.classList.remove("k4-tile-open"));
        if (same) {
          note.hidden = true;
          return;
        }
        note.dataset.for = tile.id || tile.title;
        note.textContent = tile.title;
        note.hidden = false;
        tile.classList.add("k4-tile-open");
      });
    });
  }

  function updateStatus() {
    if (statusBusy) return;
    statusBusy = true;
    fetch("/api/stage2_stats", { signal: AbortSignal.timeout(12000) })
      .then((r) => r.json())
      .then((data) => {
        const d = Array.isArray(data) && data.length ? data[0] : null;
        const pill = $id("k4-status-pill");
        const text = $id("k4-status-text");
        let state = "bad";
        let label = "no data";
        let unit = false; // "msg/s" after the number (hidden on phones)
        if (d) {
          if (d.nosdr == 1) {
            label = "no radio set up";
          } else if (d.pps > 0) {
            state = "good";
            label = fmt(d.mps);
            unit = true;
          } else if (d.uptime > 60) {
            state = "warn";
            label = fmt(d.mps);
            unit = true;
          } else {
            state = "warn";
            label = "starting…";
          }
          setTile("k4-tile-planes", fmt(d.planes));
          setTile("k4-tile-mps", fmt(d.mps));
          setTile("k4-tile-pps", fmt(d.pps));
          setTile("k4-tile-today", fmt(d.tplanes));
          statusOkAt = Date.now();
          showUpdated();
        }
        if (pill) {
          pill.dataset.state = state;
          if (text) text.textContent = label;
          pill.dataset.unit = unit ? "1" : "";
        }
        const tiles = $id("k4-tiles");
        if (tiles) tiles.dataset.state = state;
      })
      .catch(() => {
        const pill = $id("k4-status-pill");
        if (pill) {
          pill.dataset.state = "bad";
          pill.dataset.unit = "";
          const text = $id("k4-status-text");
          if (text) text.textContent = "offline?";
        }
      })
      .finally(() => { statusBusy = false; });
  }

  // ---------- Pi health tiles (Home page) ----------
  const GB = 1024 * 1024 * 1024;
  function fmtBytes(b) {
    if (b === null || b === undefined) return "–";
    if (b >= 100 * GB) return Math.round(b / GB) + " GB";
    if (b >= GB) return (Math.round((b / GB) * 10) / 10) + " GB";
    return Math.max(1, Math.round(b / (1024 * 1024))) + " MB";
  }
  function fmtClock(epoch) {
    const d = new Date(epoch * 1000);
    const today = new Date().toDateString() === d.toDateString();
    return (today ? "today " : d.toLocaleDateString() + " ") +
      d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  function setHealth(id, value, state, tip) {
    const el = $id(id);
    if (!el) return;
    el.querySelector(".k4-tile-value").textContent = value;
    if (state) el.dataset.state = state; else delete el.dataset.state;
    el.title = tip;
    el.setAttribute("aria-label", tip);
    el.classList.remove("d-none");
  }

  function fmtTemp(c) {
    const tiles = $id("k4-health-tiles");
    const freedom = tiles && tiles.dataset.freedomUnits === "1";
    return freedom ? Math.round(c * 1.8 + 32) + "°F" : Math.round(c) + "°C";
  }

  function updateTemperatures() {
    fetch("/api/get_temperatures.json", { signal: AbortSignal.timeout(15000) })
      .then((r) => r.json())
      .then((t) => {
        if (t.cpu !== undefined && t.cpu !== null && !isNaN(t.cpu)) {
          const c = Number(t.cpu);
          let state = "good", tip = `CPU temperature: ${fmtTemp(c)}, normal`;
          if (c >= 80) {
            state = "bad";
            tip = `CPU temperature: ${fmtTemp(c)}, too hot. The Pi slows itself down; add a heatsink or a case with a fan and give it air`;
          } else if (c >= 55) {
            state = "warn";
            tip = `CPU temperature: ${fmtTemp(c)}, warm. The Pi slows down at 80°C; a heatsink or fan helps`;
          }
          setHealth("k4-t-cpu", fmtTemp(c), state, tip);
        }
        if (t.ext !== undefined && t.ext !== null && !isNaN(t.ext)) {
          setHealth("k4-t-ext", fmtTemp(Number(t.ext)), "", `Temperature from the external sensor: ${fmtTemp(Number(t.ext))}`);
        }
      })
      .catch(() => { /* keep the last readings */ });
  }

  function updateHealth() {
    fetch("/api/k4nza/health", { signal: AbortSignal.timeout(15000) })
      .then((r) => r.json())
      .then((h) => {
        const sd = h.sd || {};
        if (sd.free_bytes !== null && sd.free_bytes !== undefined && sd.total_bytes) {
          const pct = Math.round((sd.free_bytes * 100) / sd.total_bytes);
          let tip = `Disk space: ${fmtBytes(sd.free_bytes)} free of ${fmtBytes(sd.total_bytes)} (${pct}%)`;
          if (sd.state === "bad") tip += ". Almost full: the feeder and SkyStats can stop working. Shorten SkyStats history or use a bigger card or drive.";
          else if (sd.state === "warn") tip += ". Getting full: consider limiting SkyStats history (Setup > Advanced).";
          setHealth("k4-t-sd", fmtBytes(sd.free_bytes), sd.state === "ok" ? "good" : sd.state, tip);
        }

        const db = h.skystats || {};
        if (db.bytes !== null && db.bytes !== undefined) {
          let tip = `SkyStats history: ${fmtBytes(db.bytes)}`;
          let state = "good";
          const g = db.growth_per_month_bytes;
          if (g !== null && g !== undefined) {
            tip += g > 0 ? `, growing about ${fmtBytes(g)} a month` : ", not growing";
            if (g > 0 && sd.free_bytes) {
              const months = sd.free_bytes / g;
              if (months < 3) {
                state = "warn";
                tip += `. At this rate the disk is full in about ${Math.max(1, Math.round(months))} month(s); limit SkyStats history (Setup > Advanced)`;
              }
            }
          } else {
            tip += " (monthly growth is shown after a week)";
          }
          setHealth("k4-t-data", fmtBytes(db.bytes), state, tip);
        }

        const p = h.power || {};
        if (p.state && p.state !== "unknown") {
          let value = "OK", tip = "Power supply: no low-voltage warnings";
          if (p.state === "bad") {
            value = "LOW";
            tip = "Power supply: the voltage is too low right now. Use the official Raspberry Pi power supply; weak power causes dropped USB radios and SD card errors";
          } else if (p.state === "warn") {
            value = "LOW";
            tip = "Power supply: low voltage was seen" + (p.last_epoch ? ` ${fmtClock(p.last_epoch)}` : " since the last restart") +
              ". Use the official Raspberry Pi power supply; weak power causes dropped USB radios and SD card errors";
          } else if (p.since_boot) {
            tip = "Power supply: OK now (low voltage was seen earlier, more than a day ago)";
          }
          if (p.throttled && p.state !== "ok") tip += ". The Pi slowed itself down to cope";
          setHealth("k4-t-pwr", value, p.state === "ok" ? "good" : p.state, tip);
        }
      })
      .catch(() => { /* keep the last readings */ });
  }

  // ---------- aircraft search box (Home page) ----------
  // Opens the SkyStats Search tab in a new tab; the box stays as it is for
  // the next search.
  function initSearch() {
    const input = $id("k4-search-input");
    const button = $id("k4-search-btn");
    if (!input || !button) return;
    const go = () => {
      const q = input.value.trim();
      if (q.replace(/[^a-z0-9]/gi, "").length < 2) {
        input.focus();
        return;
      }
      // opened by this page (no noopener) so SkyStats' Feeder button can close the tab
      window.open("/skystats/?q=" + encodeURIComponent(q) + "&k4theme=" + currentTheme(), "_blank");
    };
    button.addEventListener("click", go);
    // narrow screens: a placeholder that fits instead of one cut off mid-word
    const longPh = input.placeholder;
    const shortPh = input.dataset.shortPlaceholder || "Search your history";
    const fitPlaceholder = () => {
      if (!shortPh) return;
      input.placeholder = input.clientWidth && input.clientWidth < 420 ? shortPh : longPh;
    };
    fitPlaceholder();
    window.addEventListener("resize", fitPlaceholder);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        go();
      }
    });
  }

  // ---------- Daylight home: hero line, today's hours, highlights, closest aircraft ----------
  const UNIT = () => (($id("k4-closest") || {}).dataset || {}).units || "imperial";
  function fmtDist(nm) {
    if (nm === null || nm === undefined) return "–";
    const u = UNIT();
    if (u === "metric") return Math.round(nm * 1.852) + " km";
    if (u === "nautical") return (nm < 10 ? Math.round(nm * 10) / 10 : Math.round(nm)) + " nm";
    const mi = nm * 1.15078;
    return (mi < 10 ? Math.round(mi * 10) / 10 : Math.round(mi)) + " mi";
  }
  function fmtAlt(ft) {
    if (ft === "ground") return "on the ground";
    if (ft === null || ft === undefined || isNaN(ft)) return "";
    return UNIT() === "metric" ? Math.round(ft * 0.3048).toLocaleString() + " m" : Math.round(ft).toLocaleString() + " ft";
  }
  function fmtHour(h) {
    return (h % 12 || 12) + (h < 12 ? " AM" : " PM");
  }
  function fmtLocal(s) { // "2026-11-20T13:12" (station time) -> "1:12 PM"
    const m = /T(\d\d):(\d\d)/.exec(s || "");
    if (!m) return "";
    const h = Number(m[1]);
    return (h % 12 || 12) + ":" + m[2] + (h < 12 ? " AM" : " PM");
  }
  const DIRS = { N: "north", NNE: "north-northeast", NE: "northeast", ENE: "east-northeast", E: "east", ESE: "east-southeast",
    SE: "southeast", SSE: "south-southeast", S: "south", SSW: "south-southwest", SW: "southwest", WSW: "west-southwest",
    W: "west", WNW: "west-northwest", NW: "northwest", NNW: "north-northwest" };
  // the aircraft databases shout ("BOEING 737 MAX 8", "CESSNA 172 Skyhawk"): every
  // all-capitals word gets title case. Words with lower case, digits (E-6B, PA-28)
  // and short abbreviations (USAF, FAA) are left as they are.
  const SMALL = new Set(["of", "and", "the", "for", "de", "du"]);
  const KEEP = new Set(["USAF", "USN", "USMC", "USCG", "FAA", "NASA", "UPS", "LLC", "INC", "US", "UK", "DHL", "PHI", "MAX", "II", "III", "IV"]);
  function titleCase(s) {
    s = String(s || "").trim();
    if (!s) return s;
    return s.split(/(\s+|\/)/).map((w, i) => {
      if (/[a-z]/.test(w) || /\d/.test(w) || KEEP.has(w) || !/[A-Z]/.test(w)) return w;
      const lw = w.toLowerCase();
      return i > 0 && SMALL.has(lw) ? lw : lw.charAt(0).toUpperCase() + lw.slice(1);
    }).join("");
  }
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function heroWhen() {
    const out = $id("k4-hero-when");
    if (!out) return;
    const d = new Date();
    const h = d.getHours();
    const part = h < 5 ? "night" : h < 12 ? "morning" : h < 17 ? "afternoon" : h < 21 ? "evening" : "night";
    out.textContent = d.toLocaleDateString(undefined, { weekday: "long" }) + " " + part + ", " +
      d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }

  function drawHours(hours) {
    const box = $id("k4-hours");
    if (!box || !Array.isArray(hours)) return;
    const now = new Date().getHours();
    const shown = hours.slice(0, now + 1);
    const max = Math.max(1, ...shown);
    box.textContent = "";
    hours.forEach((n, h) => {
      const bar = el("span", "k4-hour" + (h === now ? " k4-hour-now" : "") + (n === max && h <= now ? " k4-hour-max" : "") + (h > now ? " k4-hour-later" : ""));
      bar.style.height = h > now ? "0" : Math.max(2, Math.round((n / max) * 100)) + "%";
      bar.title = fmtHour(h) + ": " + n.toLocaleString() + " aircraft";
      box.appendChild(bar);
    });
    let busiest = 0, quiet = 0;
    shown.forEach((n, h) => { if (n > shown[busiest]) busiest = h; if (n < shown[quiet]) quiet = h; });
    const note = $id("k4-hours-note");
    if (note && shown.some((n) => n > 0)) note.textContent = "Busiest at " + fmtHour(busiest) + (now >= 3 ? " · quietest at " + fmtHour(quiet) : "");
    box.setAttribute("aria-label", "Aircraft heard each hour today; busiest at " + fmtHour(busiest));
  }

  function highlightCard(kind, tag, title, body) {
    const card = el("div", "k4-card k4-highlight");
    card.appendChild(el("span", "k4-tag k4-tag-" + kind, tag));
    card.appendChild(el("div", "k4-highlight-title", title));
    card.appendChild(el("div", "k4-highlight-body", body));
    return card;
  }
  function drawHighlights(d) {
    const box = $id("k4-highlights");
    if (!box) return;
    const cards = [];
    const name = (a) => titleCase(a.model) || a.type || a.registration || a.callsign || a.hex.toUpperCase();
    const who = (a) => a.registration || a.callsign || a.hex.toUpperCase();
    if (d.military) {
      const m = d.military;
      const bits = [];
      if (m.distance_nm !== undefined) bits.push("passed " + fmtDist(m.distance_nm) + " away");
      if (m.altitude_ft) bits.push("at " + fmtAlt(m.altitude_ft));
      cards.push(highlightCard("mil", "Military", name(m),
        [m.operator ? titleCase(m.operator) : who(m), bits.join(" "), m.when ? fmtLocal(m.when) : ""].filter(Boolean).join(", ") + "." +
        (d.military_today > 1 ? " " + d.military_today + " military aircraft today." : "")));
    } else {
      cards.push(highlightCard("mil", "Military", "None yet today", "Military aircraft show up here as soon as one is heard."));
    }
    if (d.highest) {
      const h = d.highest;
      cards.push(highlightCard("accent", "Highest", name(h) + " at " + fmtAlt(h.altitude_ft),
        [who(h), h.operator ? titleCase(h.operator) : "", h.when ? fmtLocal(h.when) : ""].filter(Boolean).join(", ") + "."));
    }
    if (d.rarest) {
      const r = d.rarest;
      const n = r.times_ever || 0;
      cards.push(highlightCard("civ", "Rarest type", name(r) + (r.model && r.type ? " (" + r.type + ")" : ""),
        n <= 1 ? "The first one your station has ever recorded: " + who(r) + "." : "Only " + n + " of these ever recorded at your station."));
    }
    if (d.farthest) {
      const f = d.farthest;
      cards.push(highlightCard("neu", "Farthest", fmtDist(f.distance_nm) + " away",
        who(f) + (f.model || f.type ? " (" + (titleCase(f.model) || f.type) + ")" : "") + " to the " + (DIRS[f.direction] || f.direction) + "."));
    }
    box.textContent = "";
    cards.forEach((c) => box.appendChild(c));
    box.hidden = cards.length === 0;
  }

  function updateHome() {
    if (!$id("k4-highlights") && !$id("k4-hours")) return;
    fetch("/api/k4nza/home", { signal: AbortSignal.timeout(20000) })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        drawHours(d.hours);
        drawHighlights(d);
        if (d.farthest) {
          setTile("k4-n-far", fmtDist(d.farthest.distance_nm));
          setTile("k4-n-far-sub", "To the " + (DIRS[d.farthest.direction] || d.farthest.direction));
        }
        if (d.new_today !== undefined) {
          setTile("k4-n-new", fmt(d.new_today));
          setTile("k4-n-new-sub", "Out of " + fmt(d.aircraft_today) + " today");
        }
      })
      .catch(() => { /* SkyStats starting or off: the cards keep their last values */ });
  }

  const ALT_COLORS = [[5000, "#f59e0b"], [12000, "#84cc16"], [20000, "#10b981"], [30000, "#0ea5e9"], [Infinity, "#6366f1"]];
  function updateClosest() {
    const box = $id("k4-closest");
    if (!box) return;
    fetch("/api/k4nza/closest", { signal: AbortSignal.timeout(8000) })
      .then((r) => r.json())
      .then((data) => {
        const list = data.aircraft || []; // already the nearest few, closest first
        box.textContent = "";
        if (!list.length) {
          box.appendChild(el("div", "k4-muted", "No aircraft with a position right now."));
          return;
        }
        list.forEach((a) => {
          const row = el("div", "k4-closest-row");
          const alt = a.alt_baro;
          const dot = el("span", "k4-dot-alt");
          dot.style.background = alt === "ground" ? "#94a3b8" : (ALT_COLORS.find((c) => (alt || 0) < c[0]) || ALT_COLORS[4])[1];
          const mid = el("div", "k4-closest-main");
          mid.appendChild(el("div", "k4-closest-name", (a.flight || "").trim() || a.r || a.hex.toUpperCase()));
          const what = [titleCase(a.desc) || a.t, (a.dbFlags & 1) ? "military" : ""].filter(Boolean).join(" · ");
          mid.appendChild(el("div", "k4-closest-what", what || "Unknown type"));
          const right = el("div", "k4-closest-num", fmtDist(a.r_dst));
          right.appendChild(el("div", "k4-closest-alt", fmtAlt(alt)));
          row.append(dot, mid, right);
          box.appendChild(row);
        });
      })
      .catch(() => { /* map not answering: keep the last list */ });
  }

  function initHome() {
    if (!$id("k4-hero-when") && !$id("k4-closest")) return;
    heroWhen();
    setInterval(heroWhen, 30000);
    updateHome();
    setInterval(() => { if (!document.hidden) updateHome(); }, 60000);
    updateClosest();
    setInterval(() => { if (!document.hidden) updateClosest(); }, 10000);
  }

  // ---------- init ----------
  function init() {
    const toggle = $id("k4-theme-toggle");
    if (toggle) {
      toggle.addEventListener("click", () => {
        const next = currentTheme() === "dark" ? "light" : "dark";
        applyTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* private mode */ }
      });
    }

    // top menu: one dropdown open at a time; a click elsewhere or Escape closes it
    const menus = Array.from(document.querySelectorAll(".k4-tn-menu"));
    menus.forEach((m) => m.addEventListener("toggle", () => {
      if (m.open) menus.forEach((o) => { if (o !== m) o.open = false; });
    }));
    document.addEventListener("click", (e) => {
      menus.forEach((m) => { if (m.open && !m.contains(e.target)) m.open = false; });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") menus.forEach((m) => { m.open = false; });
    });

    const sidebar = $id("k4-sidebar");
    const backdrop = $id("k4-backdrop");
    const openMenu = () => document.body.classList.add("k4-menu-open");
    const closeMenu = () => document.body.classList.remove("k4-menu-open");
    ["k4-menu-toggle", "k4-tab-menu"].forEach((id) => {
      const b = $id(id);
      if (b) b.addEventListener("click", () =>
        document.body.classList.contains("k4-menu-open") ? closeMenu() : openMenu());
    });
    if (backdrop) backdrop.addEventListener("click", closeMenu);
    if (sidebar) sidebar.addEventListener("click", (e) => { if (e.target.closest("a")) closeMenu(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

    // screens outside the settings app (maps, graphs, SkyStats, logs, other
    // decoders) always open in a new tab, wherever they are linked from
    const external = /^\/(map(_\d+)?|stats(_\d+)?|skystats|acarshub|aiscatcher|radiosonde|logs|graphs1090|dump978|fa|fr24|planefinder|radarbox)(\/|\?|$)/;
    document.querySelectorAll("a[href]").forEach((a) => {
      const href = a.getAttribute("href");
      if (href && external.test(href) && !a.target) {
        a.target = "_blank";
        a.rel = "noopener";
      }
    });

    // the live map and SkyStats open in a tab this page opens itself, so their
    // Feeder buttons can close that tab and land back here (browsers only let a
    // page close a tab that a script opened). Ctrl/middle click still opens normally.
    const mapPath = /^\/(map(_\d+)?|skystats)(\/|\?|$)/;
    document.addEventListener("click", (e) => {
      const a = e.target.closest && e.target.closest("a[href]");
      if (!a || a.target !== "_blank" || e.defaultPrevented) return;
      if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      let url;
      try { url = new URL(a.href, location.href); } catch (err) { return; }
      if (url.host !== location.host || !mapPath.test(url.pathname)) return;
      // the page starts in the same light / dark look; appended as text so flags like
      // "?heatmap" keep their exact form
      const href = url.href.replace(/#.*$/, "") + (url.search ? "&" : "?") + "k4theme=" + currentTheme() + url.hash;
      const w = window.open(href, "_blank");
      if (w) e.preventDefault(); // blocked: let the link open the usual way
    });

    if ($id("k4-health-tiles")) {
      updateHealth();
      updateTemperatures();
      setInterval(() => { if (!document.hidden) updateHealth(); }, 60000);
      setInterval(() => { if (!document.hidden) updateTemperatures(); }, 15000);
    }

    initSearch();
    initTileNotes();
    initHome();

    if ($id("k4-status-pill") || $id("k4-tiles")) {
      updateStatus();
      setInterval(() => { if (!document.hidden) updateStatus(); }, 5000);
      if ($id("k4-tiles")) setInterval(showUpdated, 5000);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
