{
    "name": "CZ/SK VIES — direct EU check + proof of consultation",
    "summary": "Validate EU VAT numbers directly against the European "
               "Commission VIES service (no Odoo IAP) and store the official "
               "consultation number as proof of check.",
    "description": """
CZ/SK VIES — direct check & proof of consultation
=================================================

Odoo 19 core ``base_vat`` validates EU VAT numbers through **Odoo IAP**
(``vies.api.odoo.com``) and stores only a ``vies_valid`` boolean. A self-hosted
instance without IAP gets no VIES check at all, and there is no record of *when*
a number was confirmed or the official **consultation number** that is the legal
proof of an intra-Community exemption check.

This module adds, on top of core:

* **Direct EU VIES** — calls the European Commission VIES REST service directly
  (per-company opt-in, ``Use direct EU VIES``). No IAP, no Odoo account needed.
* **Proof of check** — stores the VIES **consultation number** (``requestIdentifier``),
  the check timestamp, the VIES request date, and the registered trader name +
  name-match result on the partner.
* A manual **Check VIES (direct)** action and a daily cron that refreshes stale
  checks for companies in direct mode.

Transient VIES faults (member-state system down, rate limit) are reported as a
fault — never silently flipping a partner to *invalid*.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["base_vat", "l10n_cssk_core"],
    "data": [
        "data/ir_cron.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_cssk_vies/static/src/scss/*.scss",
            "l10n_cssk_vies/static/src/js/*.js",
            "l10n_cssk_vies/static/src/xml/*.xml",
        ],
    },
    "installable": True,
}
