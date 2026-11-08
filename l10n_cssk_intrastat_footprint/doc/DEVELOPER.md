# l10n_cssk_intrastat_footprint: developer notes

Not user documentation: this file is not rendered into a page.

## Design

It does not decide whether a line is Intrastat-reportable. That question is
answered by the declaration's own generation, with the company's thresholds,
exclusions and transaction codes in hand; this reads the link the declaration
already stored. Re-deriving eligibility would be a second reader of that
question, and every contributor to this footprint that parsed rather than read
has drifted from the forward direction at least once.

`l10n_cssk_intrastat_base` — the INSTAT renderer — depends on `base` alone,
deliberately, so the Community (OCA) and Enterprise adapters can share it. And
neither country adapter depends on `l10n_cssk_core`, where the footprint hook
lives. The glue therefore belongs in neither and installs itself when both
sides are present.
