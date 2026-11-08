# partner_autocomplete_orsf_sk: developer notes

Not user documentation: this file is not rendered into a page.

## Authentication — and what is never asked for

Everything this module does works **anonymously**. Two optional tokens exist,
and neither is an account password:

`orsf_sk.api_token`
    A **Bearer token** from an ORSF account. Raises the request quota and
    unlocks the full address of a sole trader.

`orsf_sk.session_token`
    The value of the `__Secure-orsf.session_token` cookie from an
    administrator's own signed-in browser session — a *better-auth* session
    token that expires by itself. Only the gated person and graph endpoints
    need it, and nothing in **this** module calls those;
    `partner_autocomplete_orsf_sk_related_parties` does.

An ORSF account password is never asked for, stored or transmitted.

## Where the fields come from

Three places, and the third is optional:

**Odoo core** — `name`, `street`, `city`, `zip`, `country_id`,
`vat` (`base_vat`), `company_registry` (which `l10n_sk` labels IČO) and
`company_type`.

**The dispatcher** — `partner_gid` and `partner_autocomplete_provider`,
from `partner_autocomplete_dispatcher`, this module's only dependency.

**The SK sibling modules, detected at runtime rather than depended on** — the
same move `partner_autocomplete` itself makes for `base_address_extended`:

`l10n_sk_base`
    `l10n_sk_dic` — DIČ.
`l10n_sk_trade_registry`
    Register coordinates, status, dissolution date, and the predmety
    podnikania / účtovné závierky / previous-names lists.
`l10n_sk_vat_registration`
    § 4 / § 7 / § 7a category and *platiteľ DPH od*.

Feature detection is what keeps this a Tools module with no accounting or
localisation weight: it installs and works on its own. **The consequence is
that without those siblings, the values they own are simply not stored** —
they are no longer offered as mappings, because a mapping into an arbitrary
field would give you a copy that nothing else in the stack understands. Install
the sibling that owns the data you want.
