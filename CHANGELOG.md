# Changelog

What changed in each K4NZA ADS-B Feeder release. The newest release is at the top.
The feeder's **Updates** page shows the newest entry as "What's new".

## v3.0.15-33 (unreleased)

- The top bar under the station name just says **k4nza-build** (the version is in the page footer
  and on the Updates page).

## v3.0.15-32 (2026-11-21)

**Clearly this build**
- The page footer, the menu and the WiFi setup pages say this is an unofficial K4NZA build and send
  problem reports to this project's GitHub, not to adsb.im.
- The WiFi setup hotspot is now called **K4NZA-Feeder-Setup** (was "adsb.im-feeder"); the address to
  open is still http://192.168.199.1.

## v3.0.15-31 (2026-11-21)

Fixes from a full review of -30 on a computer and a phone, in light and dark.

**Live map**
- Aircraft photos: when the photo service is slow or doesn't answer, the map asks again (after 8, 15,
  30 and 60 seconds) instead of showing "Loading image..." for good, and a photo that fails to
  download is tried again. Aircraft with no photo of their own show a photo of their type from
  Wikipedia, marked "typical ..., not this aircraft", instead of an empty space.
- Replay links from SkyStats open in the light or dark look you chose (they always used the map's last
  look before).
- Phones: the selected aircraft sits above the replay bar instead of covering its Play button.

**Dashboard**
- One count for today: "Never seen before" now says "out of N since midnight" with the same number as
  the headline.
- Week and Month start at the station's first day of data instead of showing empty days, and the
  first (partial) day is never called the quietest.
- Photos of an aircraft's type are named in words ("Typical Gulfstream G650", not "Typical GLF6").
- "47,025 ft" no longer breaks across two lines; the station name fits in the phone's top bar.

**SkyStats**
- Who flew over most: airline names are no longer cut short.
- Aircraft only known by a type code ("E6", "H60") show the type in words ("Boeing E-6 Mercury") in
  the report, the Interesting lists and on the dashboard.
- Operator names from the feeder's database read better ("Department of the Navy", "McDonnell").
- Notable visitors: when planespotters.net is busy, a photo of the type is shown instead of none.

## v3.0.15-30 (2026-11-21)

**New look**
- A new K4NZA mark, an antenna sending and hearing waves: in the feeder's top bar, as the tab icon
  of the feeder, the live map and SkyStats, and as the phone home-screen icon.

**Dashboard**
- Numbers refresh faster: today's summary every 20 seconds (was a minute), the closest aircraft every
  5 seconds, and everything at once when you come back to the tab.
- Highlights (Military, Highest, Rarest type, Farthest) show a photo of the aircraft (or of its type,
  marked as such) and open it in SkyStats Search.
- The hour-by-hour card has Day, Week and Month views (aircraft per day, busiest and quietest day).
- Aircraft types are named from the ICAO type list ("Boeing 737-800", not "Boeing 737NG 823/W").

**SkyStats**
- The report shows **Aircraft types** before **Who flew over most**, with clean type names.
- Search: **View on ADSBExchange** instead of FlightAware; an aircraft opened from the list of
  recently seen interesting aircraft opens under its row with **Close**, like other results.
- Military aircraft that only the feeder's own aircraft database knows get its operator and type.
- Aircraft without a photo of their own (Search, Notable visitors, the dashboard) show a photo of
  their type from Wikipedia, marked "not this aircraft". Airliner photos were wrongly skipped before.

**Live map**
- Layers, List, Settings and light/dark are one column at the top right again, with Layers at the
  top; the layer list opens beside the column.
- The search box is back in the aircraft list, where tar1090 has it.
- Replay links from SkyStats switch on Follow and Isolate, so the replay shows just that aircraft.
- Replay: the bottom buttons, the aircraft pane and the altitude key move up above the replay bar,
  and Replay is lit while the bar is open.
- Round zoom buttons that match the rest of the map; a bigger altitude key, set higher.
- The aircraft pane is narrower and the photo fills it. A photo that doesn't arrive is asked for
  again, and the outline shows instead of "Loading image..." for good.

## v3.0.15-29 (2026-11-20)

A new look: **Daylight**, across the feeder, the live map and SkyStats, in light and dark.

**New**
- One look everywhere: new fonts (bundled, nothing fetched from the internet), calmer colours and a
  light/dark switch (sun/moon) on every page. The feeder's choice carries over when it opens the
  live map or SkyStats.
- Feeder home page: a dashboard. Planes overhead and aircraft today with the history search, messages
  and positions per second, the farthest and never-seen-before aircraft today, today hour by hour,
  the closest aircraft right now, today's highlights (farthest, highest, latest military, rarest type),
  which sites you share with, and station health. The full feed table is folded under "details".
- Feeder menu: a top bar on a computer (Overview, Live map, SkyStats, Graphs, Setup, System), with
  "k4nza-build" and the version under the station name. Phones keep their menu.
- Live map: reorganised buttons. Feeder button and search top left, view tools top centre, list,
  settings and light/dark top right, Follow, Isolate, Dim, Replay and More at the bottom. The
  selected aircraft shows on the left, the altitude key bottom right. Bars show icons only when a
  small window has no room for the labels.
- SkyStats: new header with a **Feeder** button (closes the tab, back to the feeder), the station
  name and "k4nza-build". The Activity tab is now a report for Today, Week, Month or All time: what
  crossed your sky in one sentence, four key numbers, when your sky is busiest (day by hour), range
  by direction and signal vs distance, who flew over most, aircraft types, where they were going,
  and notable visitors with photos.
- SkyStats: every visit time in **Search**, and each notable visitor, links to the live map's
  **replay** of that moment with the aircraft selected.

**Fixed**
- Updates: the SkyStats download shows its progress every 15 seconds, restarts if it stalls for a
  minute or drops (up to 4 tries), and says clearly when it couldn't finish. It looked hung before.

## v3.0.15-28 (2026-11-18)

Mostly UI fixes: a page-by-page review of the feeder, the live map and SkyStats on a computer and a
phone. Plus one SkyStats data fix: "today" counts no longer read 0 in the evening.

**Fixed**
- Live map: the **Feeder** button now closes the map's tab and you're back on the feeder page you
  opened it from (it went to adsb-feeder.local instead: browsers only let a page close a tab that a
  script opened, so the feeder now opens the map that way). Opened from a bookmark, it goes back,
  or opens the feeder at the address you're using.
- Live map: **Settings** fills blue while its panel is open, like the other buttons (only a faint
  ring showed). On a phone the panel leaves the button column uncovered, so Settings can close it.
- Live map: clicking a button no longer selects its label text.
- Live map: the selected aircraft's details pane fits the window; its top was cut off.
- Live map: the bigger layers button overlapped the top of the button column.
- SkyStats: **Flights / aircraft seen today** read 0 every evening (from 7 PM in Kansas, when it's
  already tomorrow in UTC) until local midnight.
- SkyStats: the page scrolled sideways on a computer (hidden button tooltips stuck out past the edge).
- Feeder pages: content lines up with the page title everywhere (the home page's feeding tables, the
  Advanced page's extra-decoder boxes and help notes, and the Map options / Radio checkboxes sat
  off to the side); the big full-width Apply bars are normal buttons.
- Feeder menu: fits a 900 px high laptop window (Support info and Share diagnostics were below the edge).
- Home page: the history search hint fits on a phone; your station name sits above the links in
  the "Your feeds on other sites" cards instead of being squeezed beside them.
- Corrected hints: SkyStats isn't under System; the temperature shows on the home page, not the top
  bar; Radio's tip points at **messages / sec**. Support info shows "Netdog reboots: none".

**Changed**
- Live map: the Replay controls match the map's look (they were plain white).
- SkyStats: Interesting lists show the type code when the full type is unknown and a dash instead of
  a blank, times read like Search ("Today 7:24 PM"); chart period buttons move under the title on
  narrow screens instead of wrapping into two rows.
- Radio: the bias tee column says "off" instead of being blank; both save buttons say "Save radio
  settings". Map options buttons: "Save and go to the home page" / "Save and open the map".
- Phones: checkboxes are bigger and easier to tap.
- Basic setup: ADS-B gets its own row with the feeder type (Default, Micro, Nano, Stage 2) on one
  line under it; ACARS / VDL2, HFDL, AIS and Sonde share the next row.
- Data sharing: lines up with the other pages (it was indented), the ID boxes fit on a phone, and
  the privacy-policy shields are easier to tap.
- Management: the "Update Feeder Software" card is gone (Updates has its own page), and the Web
  Authentication button just says "Enable Authentication".

## v3.0.15-27 (2026-11-18)

**Changed**
- Live map: button order. Top bar: Feeder, Home, Labels, Details, Track labels, Tracks, Military.
  Right column: List, Settings, Dim, Isolate, Follow, More. **Replay** is now first under More.
  On a phone, Dim, Isolate and Follow are under More.
- Live map: the top bar sits in the middle of the map and moves aside so it never covers the
  selected aircraft's details or the settings panel. On a phone the settings panel opens below it.
- Live map: the **Feeder** button works like the browser's Back button. The map's own tab closes
  (or the feeder opens at the address you're using, e.g. over Tailscale), instead of going to
  adsb-feeder.local.
- Live map: the layers button is half again as big.
- SkyStats Search: **Last seen** shows the time as well as the day.
- SkyStats Search: when there's no photo of the aircraft, a Wikipedia photo of its type is shown,
  clearly labelled "Typical T38 - not this aircraft" and linked to the article.

**Fixed**
- Live map: the buttons inside the layers panel (the US / Europe group toggles) were huge.
- Live map: **Full screen** did nothing on a computer. It now works, and is hidden on browsers that
  can't do it.
- Live map: the **Settings** button now lights up while its panel is open.
- Live map: the **List** button's label was mirrored when the list was closed.

## v3.0.15-26 (2026-11-18)

**Changed**
- Live map: a new button layout.
  - Top bar: Feeder (back to the feeder), Home, Labels, Details, Tracks, Military, Replay.
  - Right column: List, Settings, Track labels, Dim, Isolate, Follow, and **More** for In view,
    Multi, Persist, Random, Full screen and Wide list.
  - Every button shows its keyboard shortcut, like "Labels (L)", and a plain-English tooltip on
    hover (press and hold on a phone). Buttons that are on are clearly highlighted.
  - Phones: icons only, the column keeps List, Settings and More, and the map opens without the
    aircraft list covering it.
- Live map: one search box finds an aircraft (callsign, hex, registration, type) or jumps to an
  airport code or a latitude, longitude.
- Live map: a route the route service couldn't confirm (shown with "??", often another leg of a
  reused flight number) is replaced by the route SkyStats looked up when it fits where the aircraft
  is; otherwise it shows "route unverified" and is looked up again a few minutes later.
- SkyStats Search: an aircraft's details open right under its row in the list (click the row again
  to close them).
- SkyStats Signal vs Distance: the notes explain why aircraft passing nearly overhead read weaker.

**Privacy**
- The feeder no longer checks in with adsb.im. Stock adsb.im sent the image name, board, version and
  the list of sites you feed to adsb.im every day and on page loads, only to learn the newest stock
  release, which this build doesn't use. Lookups you start yourself (nearest airport, ACARS
  frequencies) are unchanged.

**Fixed**
- The update no longer logs an error on Pi OS versions without `/etc/dhcp/dhclient.conf`.

## v3.0.15-25 (2026-11-17)

**New**
- SkyStats: aircraft the feeder's own aircraft database marks as military now count as Military
  even when the plane-alert list doesn't have them (for example an E-6B seen as AEEFBB). Ones
  already seen are marked once after the update. Discord alerts from Planefence don't change.

**Changed**
- Home: tap (or click) any tile to read its advice; tooltips don't show on phones. Under the
  aircraft tiles, "Updated ... ago" turns amber when the numbers are more than a minute old, so
  frozen numbers never look current.
- SkyStats Search: before you search, it shows Military, Government, Police and Civilian shortcuts
  and the ten most recently seen interesting aircraft. On phones the results table fits the screen
  (operator under the registration, type code only). Aircraft without a photo show a plane or
  helicopter outline with the type, and Military aircraft tagged from the feeder's database say so.
- SkyStats: each interesting group has its own colour (Military olive, Government blue, Police red,
  Civilian purple) on badges, shortcuts and card icons, and SkyStats uses the same blue as the
  feeder's pages.
- SkyStats Interesting Aircraft cards list each aircraft once and show the registered owner when
  the plane-alert list has no operator.
- SkyStats Signal vs Distance shows each aircraft's signal at its closest approach, so the band
  now slopes down with distance and shows how well the gain and antenna do. Before, it showed the
  signal when an aircraft was first heard, which is nearly always the weakest the receiver can
  decode, so it looked like a flat line. New readings start after the update; until there are
  enough for the chosen period, the chart shows the old readings with a note saying so.
- SkyStats Range by Direction has a "How to read this chart" section, and the Aircraft Seen and
  Aircraft Type charts have a one-line note explaining what they count.
- Menu: the Live map icon is a level plane (the old one looked like it had crash-landed).
- SkyStats: clicking the SkyStats-K4NZA title goes back to the dashboard (Activity tab, top of
  the page).
- SkyStats Search: the aircraft you open shows right under the search box, above the list, instead
  of below a long list. The list shows the first 10 aircraft; **See more** shows the rest.
- Home: the Updates line is gone (the Updates page shows the same, with more detail). Home still
  starts the once-a-day Pi OS update check in the background.

**Fixed**
- SkyStats stopped looking up registrations (owner, model, country, photo) as soon as it met a
  TIS-B target (a code starting with "~"), so aircraft seen after that had none. Those codes are
  now skipped, and the missed lookups catch up on their own after the update.
- SkyStats database "deadlocks" (about 40 a day): the record-holder job and the live update could
  block each other, and each time a round of position updates was thrown away. They now take turns.
- SkyStats Interesting Aircraft cards could fail to load once a feeder-tagged military aircraft
  without an operator was recorded (caught before release).

## v3.0.15-24 (2026-11-16)

**New**
- SkyStats Search: click a group heading in Interesting Aircraft (Military, Government, Police,
  Civilian) to list every aircraft of that group ever seen, not just the recent ones on the card.
- SkyStats Search: click a column heading (Registration, Operator, Type, Visits, Last seen) to sort
  the results; click again to reverse.
- SkyStats Activity → Signal vs Distance: a "How to read this chart" section explains what a
  healthy chart looks like and what too much or too little gain, range limits and gaps look like.

**Changed**
- Container logs are kept in memory again instead of being written to the SD card (as in stock
  adsb.im). The update switches Docker back and recreates the containers once, so all of them
  restart during this update. Logs from before a reboot are no longer kept.
- WiFi power saving is off. It caused delay spikes on the Pi's WiFi, which slowed the map and
  anything reached over WiFi.
- Home: the four aircraft tiles refresh every 5 seconds (was 15).
- Home: the Updates line moved below "Your feeds on other sites".
- Home checks for Pi OS updates at most once a day (each check rewrites the package lists on the SD
  card). The Updates page still checks every 6 hours.
- Pi OS updates now include new kernels (before, they were held back forever). Packages
  nothing needs any more, such as old kernels, are removed, and so are the downloaded package
  files. After a kernel update the Updates page offers **Restart now**.
- The SkyStats container copy kept for "Go back" is stored compressed only: about a third of the
  space and far fewer SD card writes per update.
- The live map container only opens the network ports something uses: the map (8080), SBS output
  for tools like Planefence (30003), Beast in (30004, 30104) and out (30005, 30006), and MLAT
  results for a stage 2 feeder (31005). The readsb API (30152, no password) and the other unused
  ports are closed.

**Fixed**
- NAS backup: a backup is only written once the NAS share is really connected, never into the
  Pi's memory.

## v3.0.15-23 (2026-11-14)

**Fixed**
- Backup → Network backup: turning on "Back up to the NAS every night" wasn't saved, and the page
  always said "Nightly NAS backup is off", so the nightly backup never ran (Back up now did work).
  The setting is now a switch and is saved. After updating, turn it on and click Save once more.

## v3.0.15-22 (2026-11-14)

**New**
- Nightly backup to a NAS (System → Backup → Network backup). Enter the NAS address, shared folder,
  username and password, and the feeder saves your settings, graphs and SkyStats database to the
  NAS every night at the time you choose, keeping as many backups as you ask for. **Test connection**
  and **Back up now** buttons check it straight away, and the page shows whether the last backup
  worked. If the NAS is off, the feeder carries on normally and tries again an hour later. Off unless
  you turn it on.
- SkyStats: click a registration in Interesting Aircraft or Record Holders to open the Search tab
  with every visit of that aircraft in your history.

**Changed**
- SkyStats is now called SkyStats-K4NZA, and its footer and Settings → About link to its own public
  repository ([ordoleonum/skystats-k4nza](https://github.com/ordoleonum/skystats-k4nza)). About still
  credits Tom Carman's original SkyStats.
- SkyStats Activity tab: the range-by-direction and signal-vs-distance charts come first, above
  Aircraft Seen and Top types.

**Fixed**
- SkyStats header on phones: the light/dark switch no longer covers the title.

## v3.0.15-21 (2026-11-13)

**Changed**
- Home: the Pi health readings (CPU temperature, power supply, disk space and SkyStats history)
  moved from the top bar to a row of tiles under the receiver tiles. Each tile's edge turns green,
  amber or red, with advice in its tooltip. The top bar keeps the message-rate indicator.
- Home: the six shortcut buttons are gone (the same links are always in the menu), and the aircraft
  search box moved up in their place.
- The aircraft search box on Home stays in place after a search, ready for the next one.
- SkyStats search shows a photo of the aircraft from planespotters.net, credited to the photographer.
- SkyStats search links to FlightAware instead of the live map, so aircraft that are out of range
  can still be looked up.
- The top bar shows the installed K4NZA version next to the station name.
- The page footer links to this repository instead of adsb.im.

**Fixed**
- "Your feeds on other sites" on Home showed only a heading for sites without a card of their own
  (adsb.fi, for example). Every site you feed now gets a card with its map and feed status page,
  and the section stays hidden when there is nothing to show.
- The day numbers under the aircraft-per-day chart on Home could repeat a day around a
  daylight-saving change.

## v3.0.15-20 (2026-11-13)

The start of the public change log: from this release on, every change is its own commit
in this repository and every release tag is kept.

**New**
- **Aircraft search** in SkyStats (*Search* tab, or the search box on the feeder's Home page):
  find an aircraft by registration, hex code, callsign, type (for example `B739` or `C17`) or
  operator, and see every visit: when, callsign, route, closest distance, highest altitude
  and time in view. The visits can be downloaded as a CSV file.
- SkyStats now records how close each aircraft came (closest distance). It is in the search
  results and in the Flights export (`closest_km`, `closest_mi`, `closest_nm`).
- **Pi health in the top bar**: free SD card space, size of the SkyStats history (with its
  growth per month) and the power supply, next to the CPU temperature. A reading turns amber
  or red with advice when something needs attention; click it for the System page.
- **Go back a version**: after updating, the Updates page offers to reinstall the version the
  feeder ran before. The first time this is possible is after updating from this release
  to the next one.
- The Updates page shows **what's new** in the newest release.
- The footer also shows the feeder's IP address, for devices where `adsb-feeder.local`
  doesn't work.

**Improved**
- "Aircraft today" and the aircraft-per-day chart on Home count from midnight in the feeder's
  time zone (set in Basic setup) instead of midnight UTC.
- SkyStats all-time numbers (total aircraft and flights, all-time top types and the all-time
  range outline) are kept in small summary tables, so they stay correct when *Keep history*
  removes old flights, and stay fast however long the history grows. The first start after
  updating builds the summaries in the background (a few minutes for a year of history).
- Faster SkyStats reception charts on large histories.
- SkyStats keeps flight routes for up to 18 hours before looking them up again, so it asks
  the route service far less often (from wiedehopf's SkyStats).
- Updates download only the release being installed, without its history, and old releases
  no longer pile up on the SD card.
- The SkyStats container downloaded by an update is checked against a checksum before it is
  installed.

**Security**
- SkyStats refuses settings changes that come from other websites (it used to allow any site).

**Behind the scenes**
- Automatic tests for SkyStats, including tests against a real database on every build.
- Old release pages are removed automatically when a new release is published; tags are kept.
