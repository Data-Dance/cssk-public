# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Starter asset profiles for a Slovak company.

An ``account.asset.profile`` is the ACCOUNTING side of depreciation: which
accounts a depreciation posts to, and over how long the entity expects to use
the thing. Slovak law puts that squarely on the účtovná jednotka — § 28 zákona
431/2002 has it set its own odpisový plán from the expected useful life — so
these are **defaults to adjust, not statutory data**, in the same sense as the
taxes and journals a chart already ships.

The statutory half is elsewhere and is not guessed here: daňové odpisy live in
the odpisové skupiny (§ 22–29 zákona 595/2003), shipped as
``account.asset.tax.class`` by ``l10n_sk_account_asset_tax``.

**No profile carries a default tax class, deliberately.** The account does not
determine the odpisová skupina — a building is group 5 or 6 depending on what
it is, a machine 1, 2 or 3 — so a default would be wrong often, silently, and
in a field that posts real numbers. An empty tax class asks a question; a wrong
one answers it badly.

Two accounts get no profile at all, because nothing on them is depreciated:
**031 Pozemky** and **032 Umelecké diela a zbierky**. A profile for them would
assert a useful life that neither has.
"""

from odoo import models
from odoo.addons.account.models.chart_template import template

#: ``(asset account, accumulated depreciation account, years, name)``.
#:
#: The durations are ordinary Slovak practice for accounting depreciation and
#: happen to line up with the tax groups in the common case; they are a
#: starting point, not a rule. The account pairing, by contrast, is not a
#: matter of taste — each oprávky account names the asset account it belongs
#: to, and that is what decides the pairs below.
SK_ASSET_PROFILES = (
    ("012000", "072000", 5, "Aktivované náklady na vývoj"),
    ("013000", "073000", 4, "Softvér"),
    ("014000", "074000", 5, "Oceniteľné práva"),
    ("015000", "075000", 5, "Goodwill"),
    ("019000", "079000", 5, "Ostatný dlhodobý nehmotný majetok"),
    ("021000", "081000", 40, "Stavby"),
    ("022000", "082000", 6, "Samostatné hnuteľné veci a súbory hnuteľných vecí"),
    ("025000", "085000", 12, "Pestovateľské celky trvalých porastov"),
    ("026000", "086000", 4, "Základné stádo a ťažné zvieratá"),
    ("029000", "089000", 6, "Ostatný dlhodobý hmotný majetok"),
)

#: Where every Slovak depreciation lands.
SK_DEPRECIATION_EXPENSE = "551000"


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.asset.profile")
    def _get_sk_account_asset_profile(self):
        """Merged into the SK chart when it is loaded.

        **The pairing here deliberately differs from core l10n_sk's own
        ``account.asset-sk.csv``, which is wrong in 19.0 for two rows.** That
        file gives ``sk_asset_basic_herd_and_draft_animals`` the asset account
        029000 (Ostatný dlhodobý hmotný majetok) and
        ``sk_asset_other_tangible_fixes_assets`` the account 031000
        (**Pozemky**) — the asset-account column has slipped by one row, while
        the names and the oprávky accounts stayed put. Core's own
        ``account.account-sk.csv`` contradicts it: there, 026000 carries the
        herd model and 029000 the other-tangible one, which is right.

        Copying it would have set land to depreciate over six years, silently.
        So the pairs come from what the oprávky accounts actually say, and this
        note is here so nobody later "fixes" them to match upstream.
        """
        return {
            "l10n_sk_asset_profile_%s" % code: {
                "name": name,
                "account_asset_id": "chart_sk_%s" % code,
                "account_depreciation_id": "chart_sk_%s" % depreciation,
                "account_expense_depreciation_id": (
                    "chart_sk_%s" % SK_DEPRECIATION_EXPENSE
                ),
                "journal_id": "general",
                "method": "linear",
                "method_time": "year",
                "method_number": years,
                "method_period": "year",
                # Left empty on purpose — see the module docstring.
                "tax_depreciation_enabled": False,
            }
            for code, depreciation, years, name in SK_ASSET_PROFILES
        }
