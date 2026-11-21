/* K4NZA live map: layout, labels, tooltips, one search box and route checks
 * for the tar1090 map. Loaded by tar1090's config.js (TAR1090_CONFIGJS_APPEND).
 * tar1090's own buttons are kept (same ids, same click handlers) and only
 * moved, labelled and given a tooltip; nothing in tar1090 is replaced.
 *
 *   top left     Feeder (back); the selected aircraft below it
 *   top bar      Home (H), Labels (L), Details (O), Track lbl (K), Tracks (T), Military (U)
 *                (centred over the map, clear of the panels on the left)
 *   right column Layers, List, Settings, light / dark
 *   search       tar1090's own search box, in the aircraft list
 *   bottom dock  Follow (F), Isolate (I), Dim (B), Replay (Y), More
 *   More panel   In view (V), Multi (M), Persist (P), Random (R), Full screen, Wide list
 *   phones       icons only; the aircraft list starts hidden
 */
(function () {
  "use strict";

  // the feeder's address: this script is served by its setup app
  const FEEDER = (() => {
    try {
      return new URL("/", document.currentScript.src).href;
    } catch (e) {
      return location.protocol + "//" + location.hostname + "/";
    }
  })();

  const P = 'fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"';
  const ICONS = {
    feeder: '<path d="M15 6l-6 6 6 6"/><path d="M9 12h12"/>',
    layers: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    home: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    tag: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.3"/>',
    tagplus: '<path d="M3 12V4h8l10 10-8 8z"/><path d="M8 6v5M5.5 8.5h5"/>',
    tracks: '<path d="M3 17c3-6 6 2 9-4s6-6 9-8"/><circle cx="3" cy="17" r="1.5"/><circle cx="21" cy="5" r="1.5"/>',
    military: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    replay: '<path d="M7 4v16l13-8z"/>',
    list: '<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    trk: '<path d="M3 18c4 0 4-6 8-6s4 6 8 6"/><path d="M14 5h7M17.5 2v6"/>',
    dim: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    isolate: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    follow: '<path d="M4 20l7-16 7 16-7-4z"/>',
    moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
    view: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    multi: '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/><path d="M5 6.5l2 2 3-3"/>',
    persist: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3" fill="currentColor"/>',
    random: '<path d="M3 7h4l10 10h4M3 17h4l3-3M14 10l3-3h4M18 4l3 3-3 3M18 14l3 3-3 3"/>',
    full: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    wide: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M12 5v14"/>',
  };

  // id: [label, icon, shortcut key or "", tooltip]
  const BUTTONS = {
    k4feeder: ["Feeder", "feeder", "", "Back to the feeder"],
    k4layers: ["Layers", "layers", "", "Choose the map background and overlays"],
    H: ["Home", "home", "H", "Center the map on your station"],
    L: ["Labels", "tag", "L", "Show callsigns next to aircraft"],
    O: ["Details", "tagplus", "O", "Add altitude and speed to the labels"],
    T: ["Tracks", "tracks", "T", "Show the flight path of every aircraft"],
    U: ["Military", "military", "U", "Show only military aircraft"],
    RP: ["Replay", "replay", "Y", "Play back earlier traffic"],
    toggle_sidebar_button: ["List", "list", "", "Show or hide the aircraft list"],
    settingsCog: ["Settings", "settings", "", "Map options: units, colours, layers"],
    K: ["Track lbl", "trk", "K", "Show altitude and speed along the selected aircraft's track"],
    B: ["Dim", "dim", "B", "Darken the map so aircraft stand out"],
    I: ["Isolate", "isolate", "I", "Show only the selected aircraft"],
    F: ["Follow", "follow", "F", "Keep the map centred on the selected aircraft"],
    k4more: ["More", "more", "", "More map options"],
    k4theme: ["Theme", "moon", "", "Switch between light and dark"],
    V: ["In view", "view", "V", "List only aircraft visible on the map"],
    M: ["Multi", "multi", "M", "Select several aircraft at once"],
    P: ["Persist", "persist", "P", "Keep aircraft on the map after they go out of range"],
    R: ["Random", "random", "R", "Follow a random aircraft"],
    fullscreenButton: ["Full screen", "full", "", "Use the whole screen for the map"],
    expand_sidebar_button: ["Wide list", "wide", "", "Make the aircraft list wider"],
  };
  const TOP = ["H", "L", "O", "K", "T", "U"];
  const RIGHT = ["k4layers", "toggle_sidebar_control", "settingsCog", "k4theme"];
  const DOCK = ["F", "I", "B", "RP", "k4more"];
  const MORE = ["V", "M", "P", "R", "fullscreenButton", "expand_sidebar_control"];
  const PHONE = window.matchMedia("(max-width: 700px)");

  const $ = (id) => document.getElementById(id);
  // on screen (offsetParent is null for fixed panels, so it can't be used)
  const shown = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).display !== "none" &&
    getComputedStyle(el).visibility !== "hidden";

  function label(el, id) {
    const [word, icon, key, tip] = BUTTONS[id];
    if (!el || el.dataset.k4) return;
    el.dataset.k4 = "1";
    el.innerHTML =
      '<svg class="k4m-ico" viewBox="0 0 24 24" ' + P + ' aria-hidden="true">' + ICONS[icon] + "</svg>" +
      '<span class="k4m-word">' + word + (key ? ' <span class="k4m-key">(' + key + ")</span>" : "") + "</span>";
    el.removeAttribute("title"); // our own tooltip shows faster
    el.dataset.k4tip = tip + (key ? "  ·  shortcut: " + key : "");
    el.setAttribute("aria-label", word + (key ? " (" + key + ")" : "") + ": " + tip);
    if (el.tagName !== "BUTTON" && el.tagName !== "A") el.setAttribute("role", "button");
  }

  function makeButton(id, tag) {
    let el = $(id);
    if (el) return el;
    el = document.createElement(tag || "div");
    el.id = id;
    el.className = "button inActiveButton k4m-own";
    return el;
  }

  let morePanel, dock, topLeft;
  function build() {
    const top = document.querySelector("#header_top .buttonContainer");
    const side = document.querySelector("#header_side .buttonContainer");
    if (!top || !side || !$("L")) return false;
    if (document.documentElement.classList.contains("k4m-built")) return true;
    const host = $("header_top").parentNode;

    const feeder = makeButton("k4feeder", "a");
    feeder.href = FEEDER;
    feeder.addEventListener("click", backToFeeder);
    const more = makeButton("k4more");
    more.setAttribute("aria-expanded", "false");
    const theme = makeButton("k4theme", "button");
    theme.type = "button";
    theme.addEventListener("click", toggleTheme);
    const layers = makeButton("k4layers", "button");
    layers.type = "button";
    layers.setAttribute("aria-expanded", "false");
    layers.addEventListener("click", toggleLayers);

    // top left: Feeder (the search box stays in the aircraft list, where tar1090 has it)
    topLeft = document.createElement("div");
    topLeft.id = "k4m-topleft";
    topLeft.appendChild(feeder);
    host.appendChild(topLeft);

    // bottom dock with the More panel above it
    dock = document.createElement("div");
    dock.id = "k4m-dock";
    morePanel = document.createElement("div");
    morePanel.id = "k4m-more";
    morePanel.hidden = true;
    const dockBar = document.createElement("div");
    dockBar.className = "k4m-dockbar buttonContainer";
    dockBar.setAttribute("role", "toolbar");
    dockBar.setAttribute("aria-label", "Aircraft tools");
    dock.append(morePanel, dockBar);
    host.appendChild(dock);

    for (const id of TOP) if ($(id)) top.appendChild($(id));
    for (const id of RIGHT) {
      const el = id === "k4theme" ? theme : id === "k4layers" ? layers : $(id);
      if (el) side.appendChild(el);
    }
    for (const id of DOCK) {
      const el = id === "k4more" ? more : $(id);
      if (el) dockBar.appendChild(el);
    }
    for (const id of MORE) if ($(id)) morePanel.appendChild($(id));
    // leftovers tar1090 put in the column (spacers, the old wide-list wrapper) stay out of sight
    for (const id of Object.keys(BUTTONS)) label($(id), id);

    more.addEventListener("click", (e) => {
      e.stopPropagation();
      setMore(morePanel.hidden);
    });
    document.addEventListener("click", (e) => {
      if (!morePanel.hidden && !morePanel.contains(e.target) && e.target !== more && !more.contains(e.target)) setMore(false);
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMore(false); });

    document.documentElement.classList.add("k4m-built");
    initFullscreen();
    watchSettings();
    watchLayers();
    syncThemeButton();
    themeFromFeeder();
    placeTopBar();
    window.addEventListener("resize", placeTopBar);
    // the map area changes size when the list opens or closes
    if (window.ResizeObserver) {
      const ro = new ResizeObserver(() => placeTopBar());
      for (const el of [host, $("map_canvas"), $("sidebar_container"), $("selected_infoblock")]) if (el) ro.observe(el);
    }
    for (const id of ["toggle_sidebar_button", "expand_sidebar_button"]) {
      const b = $(id);
      if (b) b.addEventListener("click", () => { setTimeout(placeTopBar, 60); setTimeout(placeTopBar, 400); });
    }
    PHONE.addEventListener("change", placeTopBar);
    // fonts, tar1090's own panels and the selected aircraft settle after load:
    // keep the bars clear of them (cheap: a few rectangle reads a second)
    setInterval(placeTopBar, 1000);
    hideListOnPhone();
    initSearch();
    replayFocus();
    setInterval(checkPhoto, 2000);
    return true;
  }

  // Layers: tar1090's layer chooser, opened from our button in the column
  // (its own round button is hidden; its panel opens beside the column)
  function layerSwitcher() {
    return document.querySelector(".layer-switcher");
  }
  function toggleLayers(e) {
    if (e) e.preventDefault();
    const ls = layerSwitcher();
    const b = ls && ls.querySelector(":scope > button");
    if (b) b.click();
  }
  function watchLayers() {
    const ls = layerSwitcher();
    const btn = $("k4layers");
    if (!ls || !btn) return;
    const sync = () => {
      const open = ls.classList.contains("shown");
      btn.classList.toggle("activeButton", open);
      btn.classList.toggle("inActiveButton", !open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    };
    new MutationObserver(sync).observe(ls, { attributes: true, attributeFilter: ["class"] });
    sync();
  }

  // Replay links from SkyStats (?replay=...&icao=...): tar1090 selects the
  // aircraft but leaves Follow and Isolate off in replays. Switch both on once
  // the aircraft has a position, so the replay shows just that aircraft.
  function replayFocus() {
    const q = new URLSearchParams(location.search);
    if (!q.has("replay") || !q.has("icao") || q.has("noIsolation")) return;
    const hex = q.get("icao").toLowerCase().split(",")[0];
    let tries = 0;
    const t = setInterval(() => {
      try {
        if (typeof SelectedPlane !== "undefined" && SelectedPlane && SelectedPlane.icao === hex && SelectedPlane.position) {
          clearInterval(t);
          if (!onlySelected) toggleIsolation("on");
          if (!FollowSelected) toggleFollow(true);
        } else if (++tries > 120) {
          clearInterval(t);
        }
      } catch (e) {
        clearInterval(t);
      }
    }, 500);
  }

  // Aircraft photo: tar1090 asks planespotters.net once and has no error
  // handling, so a failed or slow request leaves "Loading image..." for good.
  // After 8 s, ask again ourselves; if that fails too, show the outline.
  let photoWait = null; // {hex, since, asked}
  function checkPhoto() {
    try {
      const box = $("selected_photo");
      const sel = typeof SelectedPlane !== "undefined" ? SelectedPlane : null;
      if (!box || !sel || !/Loading image/i.test(box.textContent)) { photoWait = null; return; }
      if (!photoWait || photoWait.hex !== sel.icao) { photoWait = { hex: sel.icao, since: Date.now(), asked: false }; return; }
      if (photoWait.asked || Date.now() - photoWait.since < 8000) return;
      photoWait.asked = true;
      const plane = sel;
      const base = typeof planespottersAPIurl !== "undefined" ? planespottersAPIurl : "https://api.planespotters.net/pub/photos/";
      const ctl = window.AbortController ? new AbortController() : null;
      const timer = setTimeout(() => ctl && ctl.abort(), 10000);
      fetch(base + "hex/" + plane.icao.toUpperCase(), ctl ? { signal: ctl.signal } : {})
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null)
        .then((data) => {
          clearTimeout(timer);
          plane.psAPIresponse = data && (data.photos || data.images) ? data : { photos: [] };
          if (SelectedPlane === plane && typeof displayPhoto === "function") displayPhoto();
        });
    } catch (e) { /* never break the map */ }
  }

  // light / dark: tar1090's own Dark Mode setting (kept in the browser like its other settings)
  function darkOn() {
    return typeof toggles !== "undefined" && toggles.darkMode ? !!toggles.darkMode.state : document.documentElement.classList.contains("k4m-dark");
  }
  function toggleTheme(e) {
    if (e) e.preventDefault();
    if (typeof toggles !== "undefined" && toggles.darkMode) toggles.darkMode.toggle(!toggles.darkMode.state);
    syncThemeButton();
  }
  function syncThemeButton() {
    const b = $("k4theme");
    if (!b) return;
    const dark = darkOn();
    const word = dark ? "Light" : "Dark";
    b.innerHTML = '<svg class="k4m-ico" viewBox="0 0 24 24" ' + P + ' aria-hidden="true">' + ICONS[dark ? "sun" : "moon"] + "</svg>" +
      '<span class="k4m-word">' + word + "</span>";
    b.dataset.k4tip = dark ? "Switch to light mode" : "Switch to dark mode";
    b.setAttribute("aria-label", b.dataset.k4tip);
  }
  // the feeder passes its own choice when it opens the map (?k4theme=dark|light)
  function themeFromFeeder() {
    const want = new URLSearchParams(location.search).get("k4theme");
    if ((want === "dark" || want === "light") && (want === "dark") !== darkOn()) toggleTheme();
  }

  function setMore(open) {
    if (!morePanel) return;
    morePanel.hidden = !open;
    const more = $("k4more");
    more.setAttribute("aria-expanded", open ? "true" : "false");
    more.classList.toggle("activeButton", open);
    more.classList.toggle("inActiveButton", !open);
  }

  // Feeder button = the browser's Back button: back to the feeder page the map
  // was opened from. The feeder opens the map in a tab of its own (by script, so
  // this tab may close itself): close it and the feeder's tab is showing again.
  // Opened some other way (bookmark, typed address): go back if there's a page
  // to go back to, else open the feeder here, at the address used for the map.
  function backToFeeder(e) {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) return; // new tab / window: follow the link
    e.preventDefault();
    let opener = null;
    try { opener = window.opener && !window.opener.closed ? window.opener : null; } catch (err) { /* cross-origin */ }
    if (opener) {
      try { opener.focus(); } catch (err) { /* not allowed: closing still returns to it */ }
      window.close();
    } else if (history.length > 1) {
      history.back();
      return;
    }
    // still here (the browser wouldn't close the tab): open the feeder in it
    setTimeout(() => { if (!window.closed) location.href = FEEDER; }, 300);
  }

  // Full screen: tar1090 only wires this up on phones and hides it elsewhere
  function initFullscreen() {
    const btn = $("fullscreenButton");
    if (!btn) return;
    const root = document.documentElement;
    if (!document.fullscreenEnabled || !root.requestFullscreen) {
      btn.classList.add("hidden");
      return;
    }
    btn.classList.remove("hidden");
    btn.style.removeProperty("display");
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (document.fullscreenElement) document.exitFullscreen();
      else root.requestFullscreen().catch(() => {});
      setMore(false);
    }, true);
    document.addEventListener("fullscreenchange", () => {
      const on = !!document.fullscreenElement;
      btn.classList.toggle("activeButton", on);
      btn.classList.toggle("inActiveButton", !on);
    });
  }

  // Settings button lit while the settings panel is open
  function watchSettings() {
    const panel = $("settings_infoblock");
    const btn = $("settingsCog");
    if (!panel || !btn) return;
    const sync = () => {
      const open = shown(panel);
      btn.classList.toggle("activeButton", open);
      btn.classList.toggle("inActiveButton", !open);
      placeTopBar();
    };
    new MutationObserver(sync).observe(panel, { attributes: true, attributeFilter: ["style", "class"] });
    sync();
  }

  // top bar and bottom dock: centred over the map, but never over the panels on
  // the left (selected aircraft, settings), the tools at the top right or the
  // altitude key at the bottom right
  // The free stretch of map beside the panels, for a bar at its current height.
  function freeSpan(bar, rightLimits) {
    const host = bar.offsetParent.getBoundingClientRect();
    // the dock's own row only (not the More panel open above it)
    const r0 = (bar.querySelector(".k4m-dockbar") || bar).getBoundingClientRect();
    let left = 8;
    for (const id of ["selected_infoblock", "settings_infoblock", "k4m-topleft"]) {
      const el = $(id);
      if (!shown(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.width && r.top < r0.bottom && r.bottom > r0.top) left = Math.max(left, r.right - host.left + 10);
    }
    let right = host.width - 8;
    for (const el of rightLimits) {
      if (!shown(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.top < r0.bottom && r.bottom > r0.top) right = Math.min(right, r.left - host.left - 10);
    }
    return [left, right];
  }
  // Centre a bar in that stretch. When the labelled bar doesn't fit (aircraft
  // selected and the list open on a smaller screen) it shows icons only.
  function centreBar(bar, rightLimits) {
    if (!bar || !bar.offsetParent) return;
    let [left, right] = freeSpan(bar, rightLimits);
    if (bar.classList.contains("k4m-compact")) {
      if ((Number(bar.dataset.fullWidth) || Infinity) <= right - left) bar.classList.remove("k4m-compact");
    } else if (bar.offsetWidth > right - left) {
      bar.dataset.fullWidth = bar.offsetWidth;
      bar.classList.add("k4m-compact");
    }
    const w = bar.offsetWidth;
    const centred = (left + right) / 2 - w / 2;
    let x = Math.max(left, centred);
    if (x + w > right) x = Math.max(8, right - w);
    bar.style.setProperty("left", Math.round(x) + "px", "important");
  }
  function placeTopBar() {
    // replay: tar1090 shortens the map for its replay bar at the bottom; lift
    // the dock, the altitude key and the selected aircraft above it
    const mc = $("map_container"), canvas = $("map_canvas");
    const lift = mc && canvas ? Math.max(0, mc.clientHeight - canvas.clientHeight) : 0;
    document.documentElement.style.setProperty("--k4m-lift", lift + "px");
    // Replay lit while its bar is open (tar1090 doesn't mark it)
    const rp = $("RP");
    if (rp) {
      const on = shown($("replayBar"));
      rp.classList.toggle("activeButton", on);
      rp.classList.toggle("inActiveButton", !on);
    }
    centreBar($("header_top"), [$("header_side"), document.querySelector(".layer-switcher")]);
    if (dock) {
      // phones: the selected aircraft sits at the bottom, so the dock goes above it
      const info = $("selected_infoblock");
      let bottom = 14;
      if (PHONE.matches && shown(info) && dock.offsetParent) {
        const host = dock.offsetParent.getBoundingClientRect();
        bottom = Math.max(14, Math.round(host.bottom - info.getBoundingClientRect().top + 8));
      }
      dock.style.setProperty("bottom", bottom + lift + "px", "important");
      centreBar(dock, [$("altitude_chart"), document.querySelector(".ol-zoom")]);
    }
    // tar1090 puts the distance scale beside its own (narrower) aircraft pane
    const scale = document.querySelector(".ol-scale-line");
    if (scale && scale.offsetParent) {
      const pane = $("selected_infoblock");
      let x = 8;
      if (shown(pane) && !PHONE.matches) x = Math.round(pane.getBoundingClientRect().right - scale.offsetParent.getBoundingClientRect().left + 8);
      scale.style.setProperty("left", x + "px", "important");
    }
  }

  // phones start with the map, not the list (only once, when the page opens)
  function hideListOnPhone() {
    if (!PHONE.matches) return;
    let tries = 0;
    const t = setInterval(() => {
      const list = $("sidebar_container");
      const btn = $("toggle_sidebar_button");
      if (typeof loadFinished !== "undefined" && loadFinished && list && btn) {
        clearInterval(t);
        if (list.style.display !== "none" && list.offsetWidth > 0) btn.click();
      } else if (++tries > 40) {
        clearInterval(t);
      }
    }, 250);
  }

  // ---------- one search box: aircraft first, then airport or coordinates ----------
  function initSearch() {
    const form = $("search_form");
    const input = $("search_input");
    if (!form || !input || form.dataset.k4) return;
    form.dataset.k4 = "1";
    input.placeholder = "Callsign, hex, registration, type or airport";
    input.title = "Find an aircraft, or jump to an airport code (MCI, KMCI) or latitude, longitude";
    form.addEventListener("submit", (e) => {
      const term = input.value.trim();
      if (!term) return;
      const jump = () => {
        const j = $("jump_input");
        if (!j || !window.jQuery) return;
        j.value = term;
        window.jQuery("#jump_form").trigger("submit");
      };
      if (term.includes(",")) {
        // coordinates: straight to the map position
        e.preventDefault();
        e.stopImmediatePropagation();
        input.value = "";
        jump();
        return;
      }
      // let tar1090 look for aircraft; if none match and it looks like an airport code, jump there
      if (/^[A-Za-z]{3,4}$/.test(term)) {
        setTimeout(() => {
          const w = $("search_warning");
          if (w && w.style.display !== "none" && /no match/i.test(w.textContent)) jump();
        }, 150);
      }
    }, true);
  }

  // ---------- tooltips (hover; press and hold on touch screens) ----------
  let tipEl;
  function showTip(el) {
    if (!el || !el.dataset.k4tip) return;
    if (!tipEl) {
      tipEl = document.createElement("div");
      tipEl.id = "k4m-tip";
      tipEl.setAttribute("role", "tooltip");
      document.body.appendChild(tipEl);
    }
    tipEl.textContent = el.dataset.k4tip;
    tipEl.style.display = "block";
    const r = el.getBoundingClientRect();
    const t = tipEl.getBoundingClientRect();
    const inColumn = !!el.closest("#header_side");
    let x = inColumn ? r.left - t.width - 10 : r.left + r.width / 2 - t.width / 2;
    let y = inColumn ? r.top + r.height / 2 - t.height / 2 : r.bottom + 8;
    x = Math.max(6, Math.min(window.innerWidth - t.width - 6, x));
    y = Math.max(6, Math.min(window.innerHeight - t.height - 6, y));
    tipEl.style.left = x + "px";
    tipEl.style.top = y + "px";
  }
  function hideTip() {
    if (tipEl) tipEl.style.display = "none";
  }
  document.addEventListener("mouseover", (e) => {
    const el = e.target.closest && e.target.closest("[data-k4tip]");
    if (el) showTip(el);
  });
  document.addEventListener("mouseout", (e) => {
    const el = e.target.closest && e.target.closest("[data-k4tip]");
    if (el && !el.contains(e.relatedTarget)) hideTip();
  });
  let pressTimer = null;
  let pressShown = false;
  document.addEventListener("pointerdown", (e) => {
    if (e.pointerType !== "touch") return;
    const el = e.target.closest && e.target.closest("[data-k4tip]");
    if (!el) return;
    pressShown = false;
    clearTimeout(pressTimer);
    pressTimer = setTimeout(() => {
      pressShown = true;
      showTip(el);
    }, 450);
  });
  const endPress = () => {
    clearTimeout(pressTimer);
    if (pressShown) setTimeout(hideTip, 1800);
  };
  document.addEventListener("pointerup", endPress);
  document.addEventListener("pointercancel", endPress);
  // a press-and-hold only shows the tooltip; it doesn't also press the button
  document.addEventListener("click", (e) => {
    if (!pressShown) return;
    pressShown = false;
    e.preventDefault();
    e.stopPropagation();
  }, true);

  // ---------- routes: replace "??" (unconfirmed) routes ----------
  // tar1090 shows "?? " before a route the route service couldn't match to the
  // aircraft's position; often it's another leg of a reused flight number.
  // Ask SkyStats (through the feeder) for the route it looked up and use it if
  // it fits where the aircraft is; otherwise mark the route unverified and let
  // tar1090 look it up again a few minutes later.
  const routeCache = {}; // callsign -> {t, data|null}
  const RETRY_S = 5 * 60;

  function distKm(a, b) {
    const R = 6371, rad = Math.PI / 180;
    const dLat = (b[0] - a[0]) * rad, dLon = (b[1] - a[1]) * rad;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * rad) * Math.cos(b[0] * rad) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  // close enough to the line between the two airports (and not far beyond them)
  function fits(pos, route) {
    const o = route.origin, d = route.destination;
    if (!pos || o.lat == null || d.lat == null) return false;
    const p = [pos[1], pos[0]];
    const od = distKm([o.lat, o.lon], [d.lat, d.lon]);
    const via = distKm([o.lat, o.lon], p) + distKm(p, [d.lat, d.lon]);
    return via - od < Math.max(80, od * 0.15);
  }
  function routeText(route) {
    const a = (x) => x.iata || x.icao || "?";
    return a(route.origin) + " - " + a(route.destination);
  }
  function lookup(cs) {
    const c = routeCache[cs];
    if (c && Date.now() - c.t < 5 * 60 * 1000) return c.data;
    if (c && c.pending) return null;
    routeCache[cs] = { t: Date.now(), data: c ? c.data : null, pending: true };
    fetch(FEEDER + "api/k4nza/route/" + encodeURIComponent(cs))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { routeCache[cs] = { t: Date.now(), data: data && data.origin ? data : null }; })
      .catch(() => { routeCache[cs] = { t: Date.now(), data: null }; });
    return null;
  }
  function patchRoutes() {
    if (typeof PlaneObject === "undefined" || !PlaneObject.prototype.routeCheck || PlaneObject.prototype.k4route) return !!(typeof PlaneObject !== "undefined" && PlaneObject.prototype.k4route);
    const original = PlaneObject.prototype.routeCheck;
    PlaneObject.prototype.k4route = true;
    PlaneObject.prototype.routeCheck = function () {
      original.apply(this, arguments);
      try {
        if (!this.routeString || !this.routeString.startsWith("?? ")) return;
        const cs = (this.name || "").trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
        if (!cs) return;
        const sky = lookup(cs);
        if (sky && fits(this.position, sky)) {
          this.routeString = routeText(sky);
          this.routeColumn = this.routeString;
          return;
        }
        this.routeString = "route unverified";
        this.routeColumn = "unverified";
        // ask the route service again later (the aircraft may be clearly on its leg by then)
        if (typeof g !== "undefined" && g.route_cache) {
          const r = g.route_cache[cs];
          const now = Date.now() / 1000;
          if (r && r.tarNextUpdate > now + RETRY_S) r.tarNextUpdate = now + RETRY_S;
        }
      } catch (e) { /* never break the map */ }
    };
    return true;
  }

  // ---------- tab icon: the K4NZA antenna mark, as on the feeder and SkyStats ----------
  const MARK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="13" fill="#3B4FE0"/><path d="M24 20V38M18 38h12M24 26l-4 12M24 26l4 12" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="24" cy="18" r="2.8" fill="#fff"/><path d="M17.5 12.5a9 9 0 0 0 0 11M30.5 12.5a9 9 0 0 1 0 11" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><path d="M13 9a14 14 0 0 0 0 18M35 9a14 14 0 0 1 0 18" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2.2" stroke-linecap="round"/></svg>';
  function setTabIcon() {
    try {
      document.querySelectorAll('link[rel~="icon"]').forEach((l) => l.remove());
      const link = document.createElement("link");
      link.rel = "icon";
      link.type = "image/svg+xml";
      link.href = "data:image/svg+xml," + encodeURIComponent(MARK);
      document.head.appendChild(link);
    } catch (e) { /* keep tar1090's icon */ }
  }
  setTabIcon();

  // ---------- theme: follow tar1090's own Dark Mode setting ----------
  function syncTheme() {
    const root = document.documentElement;
    const bg = root.style.getPropertyValue("--BGCOLOR1").trim().toLowerCase();
    const dark = bg === "" || bg === "#313131";
    root.classList.add("k4m");
    root.classList.toggle("k4m-dark", dark);
    root.classList.toggle("k4m-light", !dark);
    syncThemeButton(); // also when Dark Mode is switched in tar1090's own settings
  }
  syncTheme();
  new MutationObserver(syncTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });

  function start() {
    let tries = 0;
    const t = setInterval(() => {
      const built = build();
      const routes = patchRoutes();
      if ((built && routes) || ++tries > 60) clearInterval(t);
    }, 250);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
