# Changelog

What changed in each K4NZA ADS-B Feeder release. The newest release is at the top.
The feeder's **Updates** page shows the newest entry as "What's new".

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
