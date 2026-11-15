# Changelog

What changed in each K4NZA ADS-B Feeder release. The newest release is at the top.
The feeder's **Updates** page shows the newest entry as "What's new".

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
