# Security

This feeder image, like the adsb.im image it is based on, is designed for use on a trusted
home network. Its web interface has no login by default and can change the whole system,
so **don't make it reachable from the internet** and don't share access with people you
don't trust.

From v3.0.15-35 the K4NZA build also refuses changes that another website tries to make
through your browser: a settings change is accepted only when it comes from a feeder page
opened at the same address. This works for any address you use (IP, `.local` name,
Tailscale, ZeroTier, NetBird) without configuration.

**Updates:** the Updates page installs the newest `k4nza-v*` release tag of
[ordoleonum/adsb-feeder-k4nza-public](https://github.com/ordoleonum/adsb-feeder-k4nza-public)
over HTTPS, and the SkyStats container is checked against the checksum published with that
release. Releases are not signed, so feeders trust whoever can push tags to that repository.

If you find a problem specific to the K4NZA build, please contact the maintainer through
GitHub (ordoleonum) rather than the adsb.im project. Issues that also affect the stock
adsb.im image are best reported to that project as described in its own
[SECURITY.md](https://github.com/dirkhh/adsb-feeder-image/blob/main/SECURITY.md).
