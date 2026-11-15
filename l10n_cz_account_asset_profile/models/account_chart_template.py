# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Starter asset profiles for a Czech company.

An ``account.asset.profile`` is the ACCOUNTING side of depreciation: which
accounts a depreciation posts to, and over how long the entity expects to use
the thing. Czech law puts that squarely on the účetní jednotka — § 28 odst. 6
zákona č. 563/1991 Sb. has it draw up its own odpisový plán and depreciate
over the time the asset is used — so these are **defaults to adjust, not
statutory data**, in the same sense as the taxes and journals a chart
already ships.

The statutory half is elsewhere and is not guessed here: daňové odpisy live in
the odpisové skupiny (§ 26–33 zákona č. 586/1992 Sb.), shipped as
``account.asset.tax.class`` by ``l10n_cz_account_asset_tax``.

**No profile carries a default tax class, deliberately.** The account does not
determine the odpisová skupina — a stavba is group 4, 5 or 6 depending on what
it is, a movable thing 1, 2 or 3 — so a default would be wrong often,
silently, and in a field that posts real numbers. An empty tax class asks a
question; a wrong one answers it badly.

Four accounts of účtová třída 0 that look like candidates get no profile,
because § 56 odst. 11 vyhlášky č. 500/2002 Sb. says nothing on them is
depreciated: **031 Pozemky**, **032 Umělecká díla a sbírky**, **016 Povolenky
na emise** and **017 Preferenční limity**. A profile for them would assert a
useful life that none has.

**027 Oceňovací rozdíl k nabytému majetku** is left out for a different
reason: it is depreciated (180 months, § 7 odst. 10 of the vyhláška), but it
arises only on the acquisition of an obchodní závod, has its own expense
account (557, not 551) and is not something a starter set should offer next
to machines and software.
"""

from odoo import models
from odoo.addons.account.models.chart_template import template

#: ``(asset account, accumulated depreciation account, years, name)``.
#:
#: The durations are a starting point for the odpisový plán, not a rule. For
#: tangible assets they are the lives of the tax groups the account most
#: often holds (5 years for movable things, 30 for buildings). For goodwill
#: and výsledky vývoje, 5 years is the floor of the 60–120 month range § 56
#: odst. 2 of the vyhláška sets where the useful life cannot be estimated,
#: and the ceiling § 6 odst. 3 písm. c) sets for goodwill. The account
#: pairing, by contrast, is not a matter of taste — each oprávky account
#: names the asset account it belongs to, and that is what decides the pairs.
CZ_ASSET_PROFILES = (
    ("012000", "072000", 5, "Nehmotné výsledky vývoje"),
    ("013000", "073000", 3, "Software"),
    ("014000", "074000", 6, "Ostatní ocenitelná práva"),
    ("015000", "075000", 5, "Goodwill"),
    ("019000", "079000", 5, "Ostatní dlouhodobý nehmotný majetek"),
    ("021000", "081000", 30, "Stavby"),
    ("022000", "082000", 5, "Hmotné movité věci a jejich soubory"),
    ("025000", "085000", 10, "Pěstitelské celky trvalých porostů"),
    ("026000", "086000", 5, "Dospělá zvířata a jejich skupiny"),
    ("029000", "089000", 5, "Jiný dlouhodobý hmotný majetek"),
)

#: Where every Czech depreciation of these profiles lands.
CZ_DEPRECIATION_EXPENSE = "551000"


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "account.asset.profile")
    def _get_cz_account_asset_profile(self):
        """Merged into the CZ chart when it is loaded."""
        return {
            "l10n_cz_asset_profile_%s" % code: {
                "name": name,
                "account_asset_id": "chart_cz_%s" % code,
                "account_depreciation_id": "chart_cz_%s" % depreciation,
                "account_expense_depreciation_id": (
                    "chart_cz_%s" % CZ_DEPRECIATION_EXPENSE
                ),
                "journal_id": "general",
                "method": "linear",
                "method_time": "year",
                "method_number": years,
                # Monthly, from the depreciation start date (OCA's Prorata
                # Temporis takes the first year's share by days): an asset put
                # into use in November does not take a whole year's
                # depreciation in its first year. § 28 odst. 6 zákona
                # č. 563/1991 Sb. has the asset depreciated "v průběhu jeho
                # používání" — and for an intangible acquired from 2021 the
                # accounting depreciation is also the tax expense (zákon
                # č. 609/2020 Sb. repealed § 32a zákona č. 586/1992 Sb.), so
                # a full first year there would be a deduction for months the
                # asset did not exist.
                "method_period": "month",
                "prorata": True,
                # Left empty on purpose — see the module docstring.
                "tax_depreciation_enabled": False,
            }
            for code, depreciation, years, name in CZ_ASSET_PROFILES
        }
