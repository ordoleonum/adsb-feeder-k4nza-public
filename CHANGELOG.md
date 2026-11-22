# Changelog

What changed in each K4NZA ADS-B Feeder release. The newest release is at the top.
The feeder's **Updates** page shows the newest entry as "What's new".

## v3.0.15-38 (2026-11-22)

**SkyStats**
- Fastest aircraft only shows speeds that check out. One bad reading could set a record (an
  airliner at 949 mph); a speed now counts only when two readings in a row agree, match how far
  the aircraft actually moved, come from its own ADS-B (not MLAT or TIS-B) and stay under
  800 knots. The Fastest list starts over after this update, because the old entries can't be
  checked. This bug was in the original SkyStats.
- Fastest, Slowest, Highest and Lowest judge each visit once it is over. They used to judge it
  within 2 minutes of the aircraft appearing and never again, so Slowest listed planes taxiing
  before take-off (an RV-6 at 3 knots that went on to fly at 162) and Lowest planes just after
  take-off. Slowest also leaves out aircraft that never left the ground. Highest, Lowest and
  Slowest are rebuilt from the history already recorded. Also from the original SkyStats.
- A visit seen too briefly for its speed to be checked shows a blank max speed in Search and
  the exports instead of a number that may be wrong.
- Indicated and true airspeed were saved in each other's columns in the Fastest and Slowest
  lists (also from the original).

## v3.0.15-37 (2026-11-22)

**Dashboard**
- "Since midnight" (in the headline and under "Never seen before") is SkyStats' own "today"
  count whenever SkyStats is on, so the dashboard and SkyStats always show the same number
  (aircraft with a position). With SkyStats off it is the receiver's own count, as before
  (every aircraft heard, also those that sent no position).
- "Today, hour by hour" follows the station's clock, also when the page is opened on a device
  set to another time zone.
- The status tooltip on the setup pages said the plane total counts from midnight UTC; it
  counts from local midnight.

**SkyStats**
- Every day starts at the station's midnight (the feeder's time zone in Basic setup), whichever
  time zone the phone or computer viewing it is in: "today", the charts, the Activity tab and
  export ranges. Dates and times in Search, highlights and the record tables are shown on the
  station's clock too.

## v3.0.15-36 (2026-11-22)

**Live map**
- The distance scale stays in the bottom-left corner while an aircraft is open (it kept jumping
  between the corner and the side of the aircraft pane).

**SkyStats**
- The download button is gone from the top bar. Export is still in SkyStats Settings and in the
  feeder backup.

## v3.0.15-35 (2026-11-21)

**Dashboard**
- Phones: the headline breaks after "23 aircraft," like on a computer, so the two numbers sit on
  lines of their own instead of side by side.
- While SkyStats is off, the home page says what it adds (history search, highlights, Week and
  Month, replay links and more) with a **Turn on SkyStats** button. The card goes away once it's on.
- Browser tabs read "station · page", and the home tab says "station · Overview" instead of
  showing the station name twice.

**Photos (dashboard, live map, SkyStats)**
- "Typical type" photos pick the right Wikipedia page more often: a Robinson R44 shows an R44
  (not a crash article or a Cessna), a Cessna 172 and twin-engine helicopters are no longer
  skipped for mentioning an engine, and a UH-60 Black Hawk beats the HH-60 Pave Hawk page.

**Live map**
- The altitude key is about twice as big and runs along the bottom (up to 1000 px wide, beside the
  aircraft pane), so its numbers can be read, also in Plane-Alert screenshots. The Follow / Isolate /
  Dim / Replay bar sits just above it, the aircraft pane ends level with that bar, the distance
  scale sits in the bottom-left corner and zoom in the bottom-right corner.

**Setup**
- Advanced: SkyStats is the first section, and while it's off it lists what needs it and recommends
  turning it on (unless the Pi has 1 GB of memory or less).
- Data sharing: the AirNav Radar privacy shield is labelled "Privacy Policy" (it said "Terms of Use")
  and is as easy to tap on a phone as the others.

**Security and reliability**
- Another website can no longer change the feeder through your browser (for example add an SSH key or
  start an update). Changes are accepted only from the feeder's own pages, at whatever address you
  opened it (IP, `.local`, Tailscale, ZeroTier, NetBird), with nothing to set up.
- With the login turned on, logging in takes you back to the page you were opening (it always went
  to Home), and a link can no longer send you to another website after logging in. Sharing the logs
  (Support) now needs the login too.
- **Shared logs no longer contain secrets they shouldn't:** the WiFi password, the login password and
  login key, the radiosonde password and AIS keys are now blanked out like the aggregator keys were.
  Because older shared logs could contain the login key, -35 makes a new one once: if you use the
  login, you'll be asked to log in again after the update.
- Passwords and keys you type into the settings pages are no longer written to the feeder's log
  (which the log viewer and older shared logs could show).
- The recovery page's Reboot and Roll back links can no longer be set off by another website.
- Share diagnostics only downloads or shows the logs; the old upload to public paste sites is gone.
- SkyStats data backup: if the backup can't be finished, the download now shows as failed in your
  browser instead of saving a cut-off file that only fails when you restore it.
- Each update keeps a dated copy of your settings (the ten newest) instead of overwriting the last one.
- The SkyStats database password no longer shows in the Pi's process list during backups.
- Image builds check the Raspberry Pi OS download against its official checksum and use a fixed
  version of the build tools.

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
