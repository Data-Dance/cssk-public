# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: The Slovak chart mapped onto the denník columns, as
#: ``(code prefixes, category for money OUT, category for money IN)``.
#:
#: Read off the official chart shipped by ``l10n_sk``
#: (``account.account-sk.csv``, opatrenie MF/23054/2002-92), so the prefixes are
#: the účtové triedy an accountant recognises rather than a guess.
#:
#: **A pair means the account genuinely moves both ways.** 343 pays the VAT over
#: and receives the nadmerný odpočet back; 461/479/231 receive a loan and repay
#: instalments; 491 takes the owner's deposit and pays the owner's withdrawal.
#: Mapped one way, those net two columns of the book into one.
#:
#: **Deliberately not mapped:**
#:
#: * 311 / 321 — receivables and payables are the leg the engine arrives
#:   through, and it follows them to the document behind them.
#: * 314 / 324 — advances. A received advance is taxable income when the money
#:   arrives, but its column depends on what the advance is *for*, so an
#:   unmatched one is flagged for the accountant instead of guessed. An advance
#:   invoice posted to the account of the final supply needs no mapping here.
#: * 611–614, 621–624, 505, 541, 546, 553 — internal or valuation entries that
#:   never stand behind a movement of money.
SK_CHART_MAP = [
    # --- príjmy ---------------------------------------------------------
    (("601", "602", "606", "607"), "cat_p_vyrobky", None),
    (("604",), "cat_p_tovar", None),
    (("641", "642", "644", "645", "646", "648", "661", "663", "665", "666",
      "667", "668"), "cat_p_ostatne", None),
    # Interest on a business account is taxed at source for a natural person,
    # so it does not enter the § 6 base.
    (("662",), "cat_pn_ostatne", None),
    # --- daňové výdavky -------------------------------------------------
    (("501", "504", "507", "11", "13"), "cat_v_zasoby", None),
    (("502", "503", "511", "512", "518"), "cat_v_sluzby", None),
    (("521", "522", "523"), "cat_v_mzdy", None),
    # § 19 ods. 3 písm. i) — the owner's own insurance IS deductible in
    # Slovakia. The Czech module maps the same account to a non-deductible
    # category, and a test in each asserts the disagreement.
    (("526",), "cat_v_poistne_podnikatel", None),
    (("524", "525"), "cat_v_poistne_zamestnavatel", None),
    (("527",), "cat_v_socfond", None),
    (("528", "531", "532", "538", "544", "548", "562", "563", "568", "569"),
     "cat_v_ostatne", None),
    # --- výdavky neovplyvňujúce základ dane -----------------------------
    # § 21: reprezentácia, dary and non-contractual penalties are not tax
    # expenses. Manká a škody are deductible only in limited cases, so they
    # start on the safe side and the accountant moves what qualifies.
    (("513", "543", "545", "549"), "cat_vn_ostatne", None),
    # Paying for an asset buys a thing; the odpis is the expense (Z1).
    (("01", "02", "03", "04"), "cat_vn_majetok", None),
    (("591", "595"), "cat_vn_dan_z_prijmov", None),
    # --- nepeňažné ------------------------------------------------------
    (("551",), "cat_z_odpisy", None),
    # --- dva smery ------------------------------------------------------
    (("343",), "cat_vn_dph", "cat_pn_dph"),
    (("341",), "cat_vn_dan_z_prijmov", "cat_pn_ostatne"),
    (("231", "461", "479"), "cat_vn_uver", "cat_pn_uver"),
    (("491",), "cat_vn_osobna_spotreba", "cat_pn_vklad"),
    (("331",), "cat_v_mzdy", "cat_pn_ostatne"),
    (("336",), "cat_v_poistne_zamestnavatel", "cat_pn_ostatne"),
    # --- priebežné položky ----------------------------------------------
    (("261",), "cat_c_priebezne", None),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cssk_chart_category_map(self):
        """The Slovak mapping, for a Slovak company."""
        self.ensure_one()
        if self.country_id.code != "SK":
            return super()._cssk_chart_category_map()
        return [
            (prefixes, "l10n_sk_cash_journal.%s" % out_ref,
             "l10n_sk_cash_journal.%s" % in_ref if in_ref else None)
            for prefixes, out_ref, in_ref in SK_CHART_MAP
        ]
