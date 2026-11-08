# l10n_sk_dppo_fs: developer notes

Not user documentation: this file is not rendered into a page.

## Packaging and checks

`l10n_sk_fs` and `l10n_sk_dppo` are **settings toggles** of the Slovak
bundle, not dependencies of it: both are delivered to subscribers rather than
published, and a hard dependency would make `l10n_sk_datadance`
uninstallable from the public repository. Glue that `_inherit`s
`cssk.income.tax.return` therefore cannot live in the umbrella — the model is
not in the graph unless the DPPO toggle was ticked. It lives here instead.

- *Porovnať s účtovnou závierkou* on the DPPO form: finds the UZPODv14 závierka
  covering the return's period (an exact period match wins over an overlap),
  compares VZS r56 against DPPO r100 and posts the comparison to the chatter.
* `VZSDPPO_RECON` — an **error**-severity kontrola when the two disagree
  beyond the reconciliation tolerance, typically a manual r100 override or a
  závierka built for a different obdobie.
* `reconcile_vzs_dppo` / `check_kontroly_vzs_dppo` on
  `l10n.sk.dph.reconciliation`, alongside the KV ↔ priznanie, súhrnný výkaz ↔
  priznanie and priznanie ↔ účtovníctvo reconciliations.
