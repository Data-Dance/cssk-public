# l10n_sk_base: developer notes

Not user documentation: this file is not rendered into a page.

## Field history

This is not a hypothetical. The field previously lived in `l10n_cssk_core`,
the shared CZ/SK base, and `l10n_cz_invoice` printed a second DIČ line from
it — the same identifier twice, disguised only by the second copy lacking its
country prefix. That line is gone.

Installing this module carries existing `l10n_cssk_dic` values over
automatically. The carry-over runs in `post_init_hook` rather than as a
migration script, because a migration in a brand-new module never fires;
removing a field does not drop its column, so the old values are still there on
arrival. Only rows where the new field is empty are filled, so a value entered
after the upgrade wins. The old column is left untouched.

Consumers repointed at the same time: `l10n_sk_invoice`, `l10n_sk_dppo`
(both DPPO XML templates), `partner_autocomplete_orsf_sk`, and
`l10n_cssk_income_tax_base` — that last one through `getattr`, since it is
the shared CZ/SK base and a Czech-only deployment installs it with no Slovak
module.
