# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""r24's two halves are stored with OPPOSITE signs, so they need opposite terms.

19.0.1.4.0 made r24 collect `24_PR` as well as `24`, which put the right
magnitude on the line and the wrong sign: a filed −190.80 computed as +190.80.

The grid's convention is what decides it, and it is uniform: every SUPPLIED
base line is negative (r01 '-01', r03 '-03', r13 '-13') and every RECEIVED one
is positive (r09 '09', r11 '11', r18 '18|18a'), because a revenue base is a
credit and an expense base a debit while the form wants both the same way
round. A line collecting BOTH sides therefore cannot carry one sign — and r24
is that line, since `l10n_sk` splits the § 25 base into `24` on the domestic
sale rates and `24_PR` on the reverse-charge ones.

So the formula becomes `-24|+24_PR`: per-term signs, with an unsigned term
still inheriting the formula's, which leaves every other definition unchanged.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE cssk_vat_return_line_def d
           SET tag_formula = '-24|+24_PR'
          FROM cssk_vat_return_version v
         WHERE d.version_id = v.id
           AND d.code = 'r24'
           AND d.tag_formula = '-24|24_PR'
           AND v.country_id = (SELECT id FROM res_country WHERE code = 'SK')
        """
    )
    if cr.rowcount:
        _logger.info(
            "l10n_sk_vat_return: r24 on %s version(s) now signs its two sides "
            "independently — the received half was reported inverted",
            cr.rowcount,
        )
