# standards-watch

A watch tower for quiet standards: **iiRDS · VDI 2770 · AAS submodels**,
plus the funding calls that keep their tooling alive.

These ecosystems move slowly and announce quietly — a new IDTA submodel
template lands as a directory, a spec edition as a release, a funding call
opens for eight weeks on one page. The people affected are exactly the
people who do not refresh eight pages daily. So a cron does it:

- **[WATCH.md](WATCH.md)** — what moved, newest first (auto-updated daily)
- **[feed.xml](feed.xml)** — the same as RSS; point any reader at the raw file
- `state.json` — the tower's memory; its git history is the complete log

Watched today: iiRDS specification & models (releases *and* issue
activity), the VDI 2770 reference implementation, IDTA's published
submodel templates, BaSyx Python SDK, the official AAS test engines,
NLnet's open-calls page, and iirds.org news. Adding a source is a row in
[sources.json](sources.json), not a patch.

Built with the standard library only, on purpose: a watcher that needs a
dependency update is a watcher that eventually stops watching.

## Related

[iirds-validate](https://github.com/dev365code/iirds-validate) — 185-rule
offline conformance validator · [iirds](https://github.com/dev365code/iirds)
— read/write SDK. Unofficial, not affiliated with the iiRDS Consortium,
tekom, VDI, IDTA or NLnet; names are used descriptively.

Apache-2.0 © 2026 Wooyong Lee. Contributions take a `Signed-off-by` line (DCO).
