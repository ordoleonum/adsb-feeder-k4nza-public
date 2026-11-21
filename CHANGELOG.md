# Changelog

What changed in each K4NZA ADS-B Feeder release. The newest release is at the top.
The feeder's **Updates** page shows the newest entry as "What's new".

## v3.0.15-35 (unreleased)

**Dashboard**
- Phones: the headline breaks after "23 aircraft," like on a computer, so the two numbers sit on
  lines of their own instead of side by side.
- While SkyStats is off, the home page says what it adds (history search, highlights, Week and
  Month, replay links and more) with a **Turn on SkyStats** button. The card goes away once it's on.

**Setup**
- Advanced: SkyStats is the first section, and while it's off it lists what needs it and recommends
  turning it on (unless the Pi has 1 GB of memory or less).

## v3.0.15-34

The first public release of this history. It is based on adsb.im v3.0.15, and this entry lists
everything the K4NZA build adds or changes. From here on, every change is its own commit and
every release tag is kept (-33 stays too, so a feeder updating from it can go back).

**A new look: Daylight**
- One look across the feeder, the live map and SkyStats, in light and dark, with a light/dark
  switch on every page. Fonts are bundled, nothing is fetched from the internet. The feeder's
  choice carries over when it opens the map or SkyStats.
- A new K4NZA mark (an antenna sending and hearing waves) in the top bar, as the tab icon and as
  the phone home-screen icon.
- Feeder menu: a top bar on a computer (Overview, Live map, SkyStats, Graphs, Setup, System) with
  **k4nza build -34** under the station name. Phones keep their menu.
- Feeder pages tidied up: content lines up with the page titles, normal-sized buttons, clearer
  labels and hints, bigger checkboxes and tap targets on phones.

**Dashboard (feeder home page)**
- "Currently tracking 28 aircraft, 1,064 since midnight", then messages and positions per second,
  the farthest and never-seen-before aircraft today, the closest aircraft right now, and which sites you share with.
  The live numbers show within seconds after a restart and refresh every few seconds.
- Today's busiest and quietest hours, with Week and Month views.
- Highlights (Military, Highest, Rarest type, Farthest) with a photo, each opening in SkyStats.
- Pi health tiles: CPU temperature (amber from 70 °C), power supply, disk space and SkyStats history size, turning
  amber or red with advice. Tap any tile to read its advice.
- An aircraft search box that searches your whole SkyStats history.
- "Your feeds on other sites": a card for every site you feed, with its map and feed status page.
- "Aircraft today" counts from midnight in the feeder's time zone, not midnight UTC.

**Live map**
- A new button layout: view tools in a top bar centred over the map, Layers, List, Settings and
  light/dark at the top right, Follow, Isolate, Dim, Replay and More at the bottom. Every button
  shows its keyboard shortcut and a plain-English tooltip, and buttons that are on are lit.
  Phones get icons only and the map opens without the list covering it.
- The **Feeder** button closes the map's tab and you're back on the feeder (or opens the feeder at
  the address you're using, e.g. over Tailscale).
- Aircraft photos are asked for again when the photo service is slow; aircraft with no photo show
  a photo of their type from Wikipedia, marked "not this aircraft".
- A route the route service couldn't confirm ("??", often another leg of a reused flight number)
  is replaced by the one SkyStats looked up, or marked "route unverified".
- Replay: links from SkyStats open the replay of that moment with the aircraft selected, followed
  and isolated; the buttons, aircraft pane and altitude key move up above the replay bar.
- Full screen works on a computer and is hidden where the browser can't do it.

**SkyStats-K4NZA**
- Its own public repository ([ordoleonum/skystats-k4nza](https://github.com/ordoleonum/skystats-k4nza)),
  still crediting Tom Carman's original SkyStats.
- **Search** every aircraft ever seen by registration, hex, callsign, operator or type (code or
  name: "KC-135", "Stratotanker", "737", "Black Hawk"): every visit with route, closest distance,
  highest altitude and time in view, a photo, a link to ADSBExchange, a link to the map's replay,
  sortable columns and CSV download. Before you search it shows the interesting groups and the
  aircraft seen most recently.
- The Activity tab is a report for Today, Week, Month or All time: four key numbers, when your sky
  is busiest, range by direction, signal vs distance (at each aircraft's closest approach, with
  how-to-read notes), aircraft types, who flew over most, where they were going, and notable
  visitors with photos.
- Interesting aircraft: each group (Military, Government, Police, Civilian) has its own colour,
  and a group heading lists every aircraft of that group ever seen. Aircraft the feeder's own
  database marks as military count as Military even when plane-alert-db doesn't have them.
- Type names in words ("Boeing E-6 Mercury", not "E6") and cleaner operator names.
- Records how close each aircraft came; keeps all-time totals in small summary tables, so they
  stay right and fast however long the history grows.
- Fixed: "today" counts read 0 every evening (UTC midnight), registration lookups stopped at the
  first TIS-B target, and about 40 database deadlocks a day.
- Refuses settings changes that come from other websites.

**Updates and backup**
- Updates come from this project's GitHub releases. The Updates page shows what's new, lets you go
  back to the version you ran before (-33 or later), and shows SkyStats download
  progress, restarting a stalled download.
- Pi OS updates include new kernels, remove packages nothing needs, and offer **Restart now** when
  a kernel was updated. Home checks for them at most once a day.
- Nightly backup to a NAS (System → Backup → Network backup) of your settings, graphs and SkyStats
  database, with **Test connection** and **Back up now**. Off unless you turn it on.

**Privacy and the Pi**
- No check-in with adsb.im: stock adsb.im sent the image name, board, version and the sites you
  feed on page loads and every day. Lookups you start yourself are unchanged.
- The live map container only opens the network ports something uses; the readsb API (30152, no
  password) is closed.
- Container logs stay in memory and the SkyStats rollback copy is stored compressed, for fewer SD
  card writes. WiFi power saving is off (it caused delay spikes).
- The footer shows the feeder's IP address, for devices where `adsb-feeder.local` doesn't work.
- The pages, menu and WiFi setup hotspot (**K4NZA-Feeder-Setup**, still http://192.168.199.1) say
  this is an unofficial K4NZA build and send problem reports to this project, not to adsb.im.

**Behind the scenes**
- Automatic tests for the feeder and SkyStats (including a real database) on every build.
- Every release first checks the live map against the newest tar1090; if tar1090 changes something
  the map relies on, the release isn't built.
