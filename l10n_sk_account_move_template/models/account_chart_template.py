# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, models

from odoo.addons.account.models.chart_template import template

# Slovak starter predkontácie.
#
# Each entry is {xmlid: (name, [(label, account_xmlid, 'dr'|'cr'), ...])}. The
# FIRST line is the user-entered amount ("input"); every further line is computed
# as the same amount ("L1"), which is what makes these one-amount postings.
# Extend per the customer's vnútorná smernica — see the scope note in the manifest.
#
# Names are Slovak, not English-with-a-name@sk-translation as the l10n_sk chart
# CSVs are. Two reasons, both structural: `account.move.template.name` is not a
# translatable field, and the chart loader's `@lang` translation mechanism only
# covers models in `TEMPLATE_MODELS` (it also strips `@` keys at the top level
# only, so one inside a nested Command.create payload would reach create() as an
# unknown field and raise).
SK_MOVE_TEMPLATES = {
    "sk_amt_pokladnica_na_cestu": (
        "Výber z pokladnice (na peniaze na ceste)",
        [
            ("Peniaze na ceste", "chart_sk_261000", "dr"),
            ("Pokladnica", "chart_sk_211000", "cr"),
        ],
    ),
    "sk_amt_cesta_na_banku": (
        "Príjem na bankový účet (z peňazí na ceste)",
        [
            ("Bankové účty", "chart_sk_221000", "dr"),
            ("Peniaze na ceste", "chart_sk_261000", "cr"),
        ],
    ),
    "sk_amt_banka_na_cestu": (
        "Výber z bankového účtu (na peniaze na ceste)",
        [
            ("Peniaze na ceste", "chart_sk_261000", "dr"),
            ("Bankové účty", "chart_sk_221000", "cr"),
        ],
    ),
    "sk_amt_cesta_na_pokladnicu": (
        "Vklad do pokladnice (z peňazí na ceste)",
        [
            ("Pokladnica", "chart_sk_211000", "dr"),
            ("Peniaze na ceste", "chart_sk_261000", "cr"),
        ],
    ),
    "sk_amt_vh_zisk": (
        "Preúčtovanie schváleného zisku (431 na 428)",
        [
            ("Výsledok hospodárenia v schvaľovaní", "chart_sk_431000", "dr"),
            ("Nerozdelený zisk minulých rokov", "chart_sk_428000", "cr"),
        ],
    ),
    "sk_amt_vh_strata": (
        "Preúčtovanie schválenej straty (431 na 429)",
        [
            ("Neuhradená strata minulých rokov", "chart_sk_429000", "dr"),
            ("Výsledok hospodárenia v schvaľovaní", "chart_sk_431000", "cr"),
        ],
    ),
}


def _template_line_vals(index, label, account, direction):
    """One account.move.template.line payload.

    Line 1 is the amount the accountant types; the rest mirror it via the
    engine's ``L<sequence>`` formula, so a two-legged predkontácia asks for a
    single number.
    """
    vals = {
        "sequence": index,
        "name": label,
        "account_id": account,
        "move_line_type": direction,
    }
    if index == 1:
        vals["type"] = "input"
    else:
        vals["type"] = "computed"
        vals["python_code"] = "L1"
    return vals


def sk_move_template_data():
    """{xmlid: values} for account.move.template on the Slovak chart."""
    return {
        xmlid: {
            "name": name,
            "journal_id": "general",
            "line_ids": [
                Command.create(_template_line_vals(i, *line))
                for i, line in enumerate(lines, start=1)
            ],
        }
        for xmlid, (name, lines) in SK_MOVE_TEMPLATES.items()
    }


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.move.template")
    def _get_sk_account_move_template(self):
        # Loaded with the SK chart, so account_id/journal_id xmlids resolve to
        # the loading company's own records and company_id comes from the
        # chart-load context.
        return sk_move_template_data()
