/* Readable buttons for the tar1090 live map.
 * Loaded by tar1090's config.js (TAR1090_CONFIGJS_APPEND). Each single-letter button
 * gets an icon and a short word; the original tooltip is kept and the
 * keyboard shortcut is added to it. tar1090's own logic is untouched.
 */
(function () {
  "use strict";

  const P = 'fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"';
  const ICONS = {
    tag: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.3"/>',
    tagplus: '<path d="M3 12V4h8l10 10-8 8z"/><path d="M8 6v5M5.5 8.5h5"/>',
    trk: '<path d="M3 18c4 0 4-6 8-6s4 6 8 6"/><path d="M14 5h7M17.5 2v6"/>',
    multi: '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/><path d="M5 6.5l2 2 3-3"/>',
    persist: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3" fill="currentColor"/>',
    isolate: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    random: '<path d="M3 7h4l10 10h4M3 17h4l3-3M14 10l3-3h4M18 4l3 3-3 3M18 14l3 3-3 3"/>',
    follow: '<path d="M4 20l7-16 7 16-7-4z"/>',
    tracks: '<path d="M3 17c3-6 6 2 9-4s6-6 9-8"/><circle cx="3" cy="17" r="1.5"/><circle cx="21" cy="5" r="1.5"/>',
    reset: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    military: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    dim: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    view: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    replay: '<path d="M7 4v16l13-8z"/>',
  };
  const BUTTONS = {
    L: ["Labels", "tag"],
    O: ["Details", "tagplus"],
    K: ["Track lbl", "trk"],
    M: ["Multi", "multi"],
    P: ["Persist", "persist"],
    I: ["Isolate", "isolate"],
    R: ["Random", "random"],
    F: ["Follow", "follow"],
    T: ["Tracks", "tracks"],
    H: ["Reset", "reset"],
    U: ["Military", "military"],
    B: ["Dim", "dim"],
    V: ["In view", "view"],
    RP: ["Replay", "replay"],
  };

  function decorate() {
    let done = 0;
    for (const [id, [word, icon]] of Object.entries(BUTTONS)) {
      const el = document.getElementById(id);
      if (!el || el.dataset.k4) continue;
      const title = el.getAttribute("title") || word;
      const key = id.length === 1 ? id : "Y";
      el.dataset.k4 = "1";
      el.innerHTML =
        '<svg class="k4m-ico" viewBox="0 0 24 24" ' + P + ' aria-hidden="true">' + ICONS[icon] + "</svg>" +
        '<span class="k4m-word">' + word + "</span>";
      el.setAttribute("title", title + "  -  keyboard shortcut: " + key);
      el.setAttribute("aria-label", word);
      el.setAttribute("role", "button");
      done++;
    }
    if (done) document.documentElement.classList.add("k4m");
  }

  // follow tar1090's own Dark Mode setting (it sets --BGCOLOR1 inline on <html>)
  function syncTheme() {
    const root = document.documentElement;
    const bg = root.style.getPropertyValue("--BGCOLOR1").trim().toLowerCase();
    const dark = bg === "" || bg === "#313131";
    root.classList.add("k4m");
    root.classList.toggle("k4m-dark", dark);
    root.classList.toggle("k4m-light", !dark);
  }
  syncTheme();
  new MutationObserver(syncTheme).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["style"],
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
  // tar1090 can re-render parts of the header after loading; decorate again then
  window.addEventListener("load", () => setTimeout(decorate, 500));
})();
