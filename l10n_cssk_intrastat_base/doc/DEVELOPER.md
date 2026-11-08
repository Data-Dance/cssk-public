# l10n_cssk_intrastat_base: developer notes

Not user documentation: this file is not rendered into a page.

## API

- `cssk.instat.builder` (AbstractModel) with two entry points:

- `build_instat_xml(header, lines)` — one declaration / one flow (Community
    adapter).
  * `build_instat_envelope(env_header, decl_groups)` — one envelope with
    several declarations, e.g. arrivals + dispatches (Enterprise adapter).

- Both validate the rendered XML against the vendored `instat62.xsd` and raise
  on failure.
* Integer coercion of `netMass` / `quantityInSU` / `invoicedAmount` per
  the schema, and normalized Party / Address rendering for the envelope sender
  and each declaration's PSI.
