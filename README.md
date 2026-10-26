# standards-watch

A watch tower for quiet standards: **iiRDS · VDI 2770 · AAS submodels**,
the Digital Product Passport work around them, and the funding calls that
keep their tooling alive.

These ecosystems move slowly and announce quietly — a new IDTA submodel
template lands as a directory, a spec edition as a release, a funding call
opens for eight weeks on one page. The people affected are exactly the
people who do not refresh eight pages daily. So a cron does it:

- **[WATCH.md](WATCH.md)** — what moved, newest first (auto-updated daily)
- **[feed.xml](feed.xml)** — the same as RSS; point any reader at the raw file
- `state.json` — the tower's memory; its git history is the complete log

Watched today: iiRDS specification & models (releases *and* issue
activity) and iirds.org news; the VDI 2770 reference implementation
(releases and issues), the guideline's programme page and its XML schema,
and the Digital Data Chain Consortium's news; IDTA's submodel templates
(the published directory and its issue activity), BaSyx Python SDK and the
official AAS test engines; Digital Product Passport pages at Eclipse,
Fraunhofer IPK and GEFEG's BatteryPass Ready; and NLnet's open-calls page.
Every source, with when it was last checked, is a row of the
[Watched sources](WATCH.md#watched-sources) table the cron writes; adding
one is a row in [sources.json](sources.json), not a patch.

Built with the standard library only, on purpose: a watcher that needs a
dependency update is a watcher that eventually stops watching.

## Related

The offline judges for the same three standards:
[iirds-validate](https://github.com/dev365code/iirds-validate) for iiRDS
packages — it also carries the read/write API that lived in
[iirds](https://github.com/dev365code/iirds), now archived —
[vdi2770-validate](https://github.com/dev365code/vdi2770-validate) for VDI
2770 documentation containers and
[aas-submodel-validate](https://github.com/dev365code/aas-submodel-validate)
for AAS submodels against IDTA templates. Unofficial, not affiliated with the
iiRDS Consortium, tekom, VDI, IDTA, NLnet or any other organisation whose
pages it watches; names are used descriptively.

Apache-2.0 © 2026 Wooyong Lee. Contributions take a `Signed-off-by` line (DCO).
