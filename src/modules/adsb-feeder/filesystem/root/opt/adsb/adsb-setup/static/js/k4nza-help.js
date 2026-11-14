/* Plain-English help for the feeder web UI.
 *
 * Runs on every page (loaded from base.html). It
 *   1. adds a short explanation under known section titles,
 *   2. gives every known button a tooltip saying what it does,
 *   3. asks for confirmation before buttons that restart, shut down or remove
 *      something (unless the button already asks),
 *   4. turns any element with class "k4-help" into a tap/hover tooltip.
 *
 * Unknown buttons and sections are left alone.
 */
(function () {
  "use strict";

  // ---- 1. section explanations, keyed by the start of the <h5>/<h4> text ----
  const SECTIONS = {
    // System > Management
    "install ssh credentials": "Paste your computer's public SSH key here so you can log in to the Pi from a terminal (ssh root@<feeder-address>) without a password.",
    "generate new root password": "Creates a new random password for the Pi's root account and shows it once. Only needed if you want password-based SSH logins.",
    "secure feeder system": "Makes the Pi harder to get into from your local network and turns off the setup WiFi hotspot. It is switched on from the command line, as described below.",
    "the feeder system is secured": "The system has been locked down. Settings can still be changed here in the web interface.",
    "web authentication": "Require a username and password before anyone on your network can open these settings pages.",
    "wifi hotspot": "If the Pi can't reach a known WiFi network it creates its own hotspot so you can connect and set up WiFi. This controls that behaviour.",
    "shutdown/reboot": "Shut down before unplugging power (prevents SD-card corruption), or reboot to recover from a problem. Feeding stops while the Pi restarts.",
    "system log persistence toggle": "Keep system logs on the SD card across reboots. Helpful for diagnosing crashes, but adds SD card writes. Off by default.",
    "system update settings": "Operating-system security updates for the Pi (Raspberry Pi OS packages). The quickest way is the Updates page.",
    "update feeder software": "Feeder and Pi OS updates now have their own page: System > Updates.",
    "restart / recreate containers": "Each feeder program (decoder, map, SkyStats, data-sharing clients) runs in its own container. Restart if something looks stuck; recreate if a setting doesn't take effect.",
    "add zerotier": "ZeroTier is a free private network so you can reach your feeder from anywhere without opening router ports.",
    "add tailscale": "Tailscale is a free private network so you can reach your feeder from anywhere without opening router ports.",
    "add netbird": "Netbird is a private network so you can reach your feeder from anywhere without opening router ports.",
    "reconfigure wifi": "Change the WiFi network the Pi connects to. A wired network cable is always more reliable for a feeder.",
    "connect to wifi": "Pick the WiFi network the Pi should connect to. A wired network cable is always more reliable for a feeder.",
    // Setup > Advanced / Expert
    "skystats": "SkyStats records every aircraft visit in a local database and shows statistics: busiest times, routes, records and interesting aircraft. Open it from the menu (System > SkyStats) or the home page. Use its Export button to download your data.",
    "healthcheck": "Optional: the feeder can ping a monitoring URL (e.g. healthchecks.io) while it is healthy, so you get an alert if it stops.",
    "temperature sensor": "Show CPU or an external sensor's temperature in the top bar. A Pi that runs hot throttles and becomes unstable - a case fan or heatsink helps.",
    "temperature information": "Show CPU or an external sensor's temperature in the top bar.",
    "reboot on missing sdr": "If the USB radio disappears (loose cable, power glitch), reboot automatically to bring it back.",
    "docker bridge network ipv6": "Advanced network option for the containers. Leave as is unless you know you need IPv6 inside containers.",
    "docker pull": "How container updates are downloaded. Concurrent downloads are faster; sequential is gentler on slow connections.",
    "css theme": "Light, dark, or follow your device's setting.",
    "gps based location": "Use a USB GPS receiver to set the feeder's location automatically (and keep accurate time for MLAT).",
    "prometheus / grafana / influx / telegraf": "Send feeder statistics to your own monitoring system. Not needed for normal use.",
    "add additional ultrafeeder arguments": "Expert option: extra command-line flags for the decoder. Wrong values can stop reception - leave empty unless following a guide.",
    "add environment variables to containers": "Expert option: extra settings passed to individual containers.",
    "add arguments to map urls": "Default options for the live map link, for example a default zoom or which aircraft labels to show.",
    "additional aggregator links": "Expert option: send data to extra destinations that are not in the Data Sharing list.",
    "add additional acars feeds": "Expert option: extra destinations for ACARS/VDL2/HFDL messages.",
    "enable non-ads-b containers": "Run extra decoders (ACARS, VDL2, HFDL, AIS ships, weather balloons). Each one needs its own extra USB radio and antenna.",
    "acars / vdl2 / hfdl": "Decoders for text messages sent by aircraft. Each needs its own USB radio and suitable antenna.",
    "ais": "Decode ship positions on marine VHF. Needs a separate USB radio and a VHF antenna.",
    // SDR page
    "lsusb output": "Raw list of USB devices the Pi can see. Your ADS-B radio usually shows up as 'Realtek RTL2838' (ID 0bda:2838).",
    // Stage 2
    "add micro feeder": "Stage 2 combines several remote receivers (micro feeders) into one map and feeds aggregators on their behalf.",
    "feeder sites": "The remote receivers this Stage 2 system collects data from.",
    // Home
    "you are feeding": "Flight-tracking sites receiving your data. Green = working, yellow = degraded, red = disconnected. MLAT lets sites locate aircraft that don't broadcast GPS positions.",
    "updates": "One click installs the newest Raspberry Pi OS packages or the newest K4NZA feeder release.",
  };

  // ---- 2. button tooltips, keyed by the button's name attribute ----
  const BUTTONS = {
    "shutdown": "Safely power the Pi off. Unplug the power only after the green light stops blinking.",
    "reboot": "Restart the Pi. Feeding pauses for about a minute.",
    "restart_containers": "Restart the feeder programs without rebooting the Pi.",
    "recreate_containers": "Remove and re-create the feeder programs from their images - use when a setting won't take effect. Your data and settings are kept.",
    "os_update": "Install the latest Raspberry Pi OS security and bug-fix updates now. Can take several minutes.",
    "nightly_update": "Save the automatic-update choice above.",
    "ssh": "Save this SSH public key so you can log in from your computer.",
    "rpw": "Generate a new random root password and show it once.",
    "web_auth_setup": "Turn on password protection for this web interface.",
    "web_auth_disable": "Turn off password protection - anyone on your network will be able to change settings.",
    "toggle_hotspot": "Turn the fallback WiFi hotspot behaviour on or off.",
    "log_persistence_toggle": "Switch between keeping logs on the SD card (survive reboots) and in memory only (fewer SD writes).",
    "wifi": "Connect to the selected WiFi network.",
    "zerotier": "Join the ZeroTier network with the ID entered here.",
    "tailscale": "Connect this feeder to your Tailscale account.",
    "tailscale_disable_go": "Disconnect this feeder from Tailscale.",
    "netbird": "Connect this feeder to Netbird.",
    "netbird_down": "Disconnect from Netbird for now (keeps registration).",
    "netbird_deregister": "Remove this feeder from your Netbird network.",
    "skystats--enable": "Start SkyStats and its database. The first start takes a minute or two.",
    "skystats--disable": "Stop SkyStats. Recorded data stays on the SD card and comes back when re-enabled.",
    "skystats--update": "Save the SkyStats settings below and restart SkyStats.",
    "healthcheck--submit": "Save the healthcheck URL.",
    "temp_sensor_enable": "Show temperature in the top bar.",
    "temp_sensor_disable": "Hide the temperature display.",
    "reboot_on_missing_sdr--enable": "Reboot automatically when the USB radio disappears.",
    "reboot_on_missing_sdr--disable": "Don't reboot when the USB radio disappears.",
    "enable_parallel_docker": "Download container updates in parallel (faster).",
    "disable_parallel_docker": "Download container updates one at a time (gentler on slow connections).",
    "css_theme--submit": "Apply the selected colour theme.",
    "turn_on_gpsd": "Use the connected GPS receiver for location.",
    "turn_off_gpsd": "Stop using the GPS receiver.",
    "update_sdr_info": "Save the radio assignment and gain for this SDR.",
    "sdr_setup": "Save radio settings and continue.",
    "aggregators": "Save which flight-tracking sites you share data with.",
    "submit": "Save these settings.",
    "upload": "Upload the selected backup file to restore it.",
    "showmap": "Open the live map.",
    "change_serial": "Write a new serial number to the radio so several radios can be told apart. Unplug and replug it afterwards.",
    "allow_config_link": "Show a link back to these settings on the map page.",
    "no_config_link": "Hide the settings link on the map page.",
    "turn_off_stage2": "Leave Stage 2 mode and go back to being a normal single feeder.",
    "flightaware--submit": "Save FlightAware settings (requires a FlightAware feeder ID).",
    "flightradar--submit": "Save Flightradar24 settings (requires a sharing key).",
    "radarbox--submit": "Save RadarBox settings (requires a sharing key).",
    "opensky--submit": "Save OpenSky Network settings.",
  };

  // buttons that interrupt feeding or remove something: confirm first
  const CONFIRM = {
    "shutdown": "Shut the feeder down now? It will stop feeding until you unplug and replug the power.",
    "reboot": "Reboot the feeder now? Feeding pauses for about a minute.",
    "recreate_containers": "Re-create all feeder containers? Feeding pauses for a minute or two. Settings and data are kept.",
    "os_update": "Run an operating system update now? This can take several minutes and the feeder may restart.",
    "web_auth_disable": "Turn off password protection for this web interface?",
    "tailscale_disable_go": "Disconnect this feeder from Tailscale? You may lose remote access.",
    "netbird_deregister": "Remove this feeder from your Netbird network? You may lose remote access.",
    "turn_off_stage2": "Leave Stage 2 mode? Micro feeder configuration will no longer be used.",
    "skystats--disable": "Stop SkyStats? Your recorded data is kept and returns when you enable it again.",
    "change_serial": "Change the radio's serial number?",
    "upload": "Restore this backup? Current settings will be replaced.",
  };
  const DANGER_STYLE = ["shutdown", "web_auth_disable", "netbird_deregister"];

  // ---- tooltip implementation (works with mouse, keyboard and touch) ----
  let tipEl = null;
  function showTip(target, text) {
    hideTip();
    tipEl = document.createElement("div");
    tipEl.className = "k4-tip";
    tipEl.textContent = text;
    document.body.appendChild(tipEl);
    const r = target.getBoundingClientRect();
    const w = tipEl.offsetWidth;
    let left = window.scrollX + r.left + r.width / 2 - w / 2;
    left = Math.max(window.scrollX + 8, Math.min(left, window.scrollX + document.documentElement.clientWidth - w - 8));
    let top = window.scrollY + r.bottom + 8;
    if (r.bottom + tipEl.offsetHeight + 16 > window.innerHeight) {
      top = window.scrollY + r.top - tipEl.offsetHeight - 8;
    }
    tipEl.style.left = left + "px";
    tipEl.style.top = top + "px";
  }
  function hideTip() {
    if (tipEl) { tipEl.remove(); tipEl = null; }
  }
  function attachHelpBubble(el) {
    const text = el.getAttribute("data-k4-tip") || el.getAttribute("title");
    if (!text) return;
    el.setAttribute("data-k4-tip", text);
    el.removeAttribute("title"); // avoid double tooltip
    el.setAttribute("role", "button");
    el.setAttribute("aria-label", text);
    if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
    el.addEventListener("mouseenter", () => showTip(el, text));
    el.addEventListener("mouseleave", hideTip);
    el.addEventListener("focus", () => showTip(el, text));
    el.addEventListener("blur", hideTip);
    el.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); tipEl ? hideTip() : showTip(el, text); });
  }

  function normalize(s) {
    return (s || "").replace(/\s+/g, " ").trim().toLowerCase();
  }

  function addSectionHelp() {
    document.querySelectorAll(".container h5, .container h4").forEach((h) => {
      if (h.closest(".modal") || h.nextElementSibling?.classList?.contains("k4-section-help")) return;
      const text = normalize(h.textContent);
      for (const key of Object.keys(SECTIONS)) {
        if (text.startsWith(key)) {
          const p = document.createElement("div");
          p.className = "k4-section-help";
          p.textContent = SECTIONS[key];
          h.insertAdjacentElement("afterend", p);
          break;
        }
      }
    });
  }

  function addButtonHelp() {
    document.querySelectorAll("button[name], input[type=submit][name]").forEach((b) => {
      const name = b.getAttribute("name");
      if (BUTTONS[name] && !b.getAttribute("title")) {
        b.setAttribute("title", BUTTONS[name]);
      }
      if (DANGER_STYLE.includes(name)) {
        b.setAttribute("data-k4-danger", "");
      }
      const formAsks = (b.form && (b.form.getAttribute("onsubmit") || "").includes("confirm("));
      if (CONFIRM[name] && !b.getAttribute("onclick") && !formAsks) {
        b.addEventListener("click", (e) => {
          if (!window.confirm(CONFIRM[name])) {
            e.preventDefault();
            e.stopImmediatePropagation();
          }
        });
      }
    });
  }

  function init() {
    try {
      addSectionHelp();
      addButtonHelp();
      document.querySelectorAll(".k4-help").forEach(attachHelpBubble);
      document.addEventListener("scroll", hideTip, { passive: true });
      document.addEventListener("click", hideTip);
    } catch (err) {
      // help text must never break a page
      console.warn("k4nza-help:", err);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
