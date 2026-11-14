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

  function updateStatus() {
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
      });
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
      window.open("/skystats/?q=" + encodeURIComponent(q), "_blank", "noopener");
    };
    button.addEventListener("click", go);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        go();
      }
    });
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

    if ($id("k4-health-tiles")) {
      updateHealth();
      updateTemperatures();
      setInterval(() => { if (!document.hidden) updateHealth(); }, 60000);
      setInterval(() => { if (!document.hidden) updateTemperatures(); }, 15000);
    }

    initSearch();

    if ($id("k4-status-pill") || $id("k4-tiles")) {
      updateStatus();
      setInterval(() => { if (!document.hidden) updateStatus(); }, 15000);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
