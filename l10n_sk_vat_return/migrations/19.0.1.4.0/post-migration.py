# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""r24 must collect the received side of the § 25 base correction as well.

`l10n_sk` splits the BASE of a § 25 correction into two tags — `24` on the
ordinary domestic sale rates and `24_PR` on the EU and reverse-charge taxes —
while the TAX side is a single tag `25` carried by both. That asymmetry is the
whole argument: if `24_PR` belonged to some other form line, there would be a
`25_PR` for that line's tax, and there is not. So `24_PR` is the received-side
component of line 24, and a formula of `-24` alone reports the tax of a
self-assessed § 25 correction on r25 while omitting its base from r24.

Which is the base-short/tax-correct signature seen four times on the MRP agenda
tonight, and it was filed: document 324057, 2024-12-30, −190.80 on r24 in a real
return, its base line carrying `24_PR`.

Targeted rather than a re-application of the version files: only one field on
one line definition changes, so there is nothing to delete and no risk of a
doubled grid. `noupdate="1"` means the data pass will not do it.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE cssk_vat_return_line_def d
           SET tag_formula = '-24|24_PR'
          FROM cssk_vat_return_version v
         WHERE d.version_id = v.id
           AND d.code = 'r24'
           AND d.tag_formula = '-24'
           AND v.country_id = (SELECT id FROM res_country WHERE code = 'SK')
        """
    )
    if cr.rowcount:
        _logger.info(
            "l10n_sk_vat_return: r24 on %s version(s) now collects 24_PR too — "
            "the received side of a § 25 base correction reached no line",
            cr.rowcount,
        )
