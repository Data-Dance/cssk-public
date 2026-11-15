# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import Command, models

_logger = logging.getLogger(__name__)

# Czech starter předkontace.
#
# Each entry is {xmlid: (name, [(label, account, 'dr'|'cr'), ...])}, where
# account is a chart xmlid or one of the ROLES below. The FIRST line is the
# user-entered amount ("input"); every further line is computed as the same
# amount ("L1"), which is what makes these one-amount postings.
# Extend per the customer's vnitřní směrnice — see the scope note in the manifest.
#
# Names are Czech, not English-with-a-name@cs-translation as the l10n_cz chart
# CSVs are. Two reasons, both structural: `account.move.template.name` is not a
# translatable field, and the chart loader's `@lang` translation mechanism only
# covers models in `TEMPLATE_MODELS` (it also strips `@` keys at the top level
# only, so one inside a nested Command.create payload would reach create() as an
# unknown field and raise).
# Accounts that are not one chart account but depend on how the company's
# books are set up. Odoo gives every bank and cash journal its own account
# (221001, 211001, ...), so 221000 / 211000 are accounts no journal posts to
# and that the bank reconciliation never sees. And 261000, which the CZ chart
# names Peníze na cestě, is the company's *bank suspense account*
# (account_journal_suspense_account_id), where unreconciled statement lines
# wait; money in transit belongs on the Liquidity Transfer account (261xxx,
# transfer_account_id), Odoo's own account for transfers between liquidity
# journals, which is reconcilable.
TRANSIT, CASH, BANK = "role:transit", "role:cash", "role:bank"
ROLES = (TRANSIT, CASH, BANK)
# Without a journal of that type, the summary account of the chart.
ROLE_FALLBACKS = {CASH: "chart_cz_211000", BANK: "chart_cz_221000"}

CZ_MOVE_TEMPLATES = {
    "cz_amt_pokladna_na_cestu": (
        "Výběr z pokladny (na peníze na cestě)",
        [
            ("Peníze na cestě", TRANSIT, "dr"),
            ("Pokladna", CASH, "cr"),
        ],
    ),
    "cz_amt_cesta_na_banku": (
        "Příjem na bankovní účet (z peněz na cestě)",
        [
            ("Bankovní účty", BANK, "dr"),
            ("Peníze na cestě", TRANSIT, "cr"),
        ],
    ),
    "cz_amt_banka_na_cestu": (
        "Výběr z bankovního účtu (na peníze na cestě)",
        [
            ("Peníze na cestě", TRANSIT, "dr"),
            ("Bankovní účty", BANK, "cr"),
        ],
    ),
    "cz_amt_cesta_na_pokladnu": (
        "Vklad do pokladny (z peněz na cestě)",
        [
            ("Pokladna", CASH, "dr"),
            ("Peníze na cestě", TRANSIT, "cr"),
        ],
    ),
    "cz_amt_vh_zisk": (
        "Přeúčtování schváleného zisku (431 na 428)",
        [
            ("Výsledek hospodaření ve schvalovacím řízení", "chart_cz_431000", "dr"),
            ("Nerozdělený zisk minulých let", "chart_cz_428000", "cr"),
        ],
    ),
    "cz_amt_vh_ztrata": (
        "Přeúčtování schválené ztráty (431 na 429)",
        [
            ("Neuhrazená ztráta minulých let", "chart_cz_429000", "dr"),
            ("Výsledek hospodaření ve schvalovacím řízení", "chart_cz_431000", "cr"),
        ],
    ),
}


def _template_line_vals(index, label, account, direction):
    """One account.move.template.line payload.

    Line 1 is the amount the accountant types; the rest mirror it via the
    engine's ``L<sequence>`` formula, so a two-legged předkontace asks for a
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


def cz_move_template_data(roles=None):
    """{xmlid: values} for account.move.template on the Czech chart.

    ``roles`` maps each role to an account id; a template using a role it
    does not resolve is left out.
    """
    roles = roles or {}
    data = {}
    for xmlid, (name, lines) in CZ_MOVE_TEMPLATES.items():
        resolved = [
            (label, roles.get(account) if account in ROLES else account, direction)
            for label, account, direction in lines
        ]
        if not all(account for _label, account, _direction in resolved):
            continue
        data[xmlid] = {
            "name": name,
            "journal_id": "general",
            "line_ids": [
                Command.create(_template_line_vals(i, *line))
                for i, line in enumerate(resolved, start=1)
            ],
        }
    return data


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _l10n_cz_move_template_roles(self, company):
        """{role: account id} for this company's books.

        Bank and cash: the account of the company's first journal of that
        type (the chart's own Bank journal first). Transit: the Liquidity
        Transfer account, or nothing (see ROLE_FALLBACKS for the others).
        """
        loader = self.with_company(company)
        Journal = self.env["account.journal"].sudo()
        roles = {}
        for role, journal_type, xmlid in ((BANK, "bank", "bank"), (CASH, "cash", "cash")):
            journal = loader.ref(xmlid, raise_if_not_found=False)
            if not journal or journal.type != journal_type or not journal.default_account_id:
                journal = Journal.search([
                    ("company_id", "=", company.id),
                    ("type", "=", journal_type),
                    ("default_account_id", "!=", False),
                ], order="sequence, id", limit=1)
            account = journal.default_account_id or loader.ref(
                ROLE_FALLBACKS[role], raise_if_not_found=False
            )
            roles[role] = account.id if account else False
        roles[TRANSIT] = company.transfer_account_id.id
        return roles

    def _l10n_cz_load_move_templates(self, company):
        """Create the starter předkontace this company does not have yet.

        Only missing templates are loaded. ``_load_data`` calls
        ``_load_records`` without ``update=True``, and ``noupdate`` only
        bites on a module *upgrade* — so an existing record is always
        rewritten, and the ``Command.create`` line payloads would append a
        second copy of every line. Skipping what exists keeps it idempotent
        and never reverts an edit the accountant made to a shipped
        předkontace.

        Returns the number of templates created.
        """
        loader = self.sudo().with_company(company)
        if not loader.ref("general", raise_if_not_found=False):
            _logger.warning(
                "No general journal for company %s — CZ předkontace skipped",
                company.name,
            )
            return 0
        roles = loader._l10n_cz_move_template_roles(company)
        if not roles[TRANSIT]:
            _logger.warning(
                "Company %s has no Liquidity Transfer account — the money in "
                "transit předkontace are skipped", company.name,
            )
        missing = {
            xmlid: vals
            for xmlid, vals in cz_move_template_data(roles).items()
            if not loader.ref(xmlid, raise_if_not_found=False)
        }
        if missing:
            loader._load_data({"account.move.template": missing})
        return len(missing)

    def _post_load_data(self, template_code, company, template_data):
        # Not @template data: the journals' own accounts and the Liquidity
        # Transfer account exist only once the chart has been loaded
        # (_post_load_data is where Odoo creates the latter).
        super()._post_load_data(template_code, company, template_data)
        if template_code == "cz":
            self._l10n_cz_load_move_templates(company)
