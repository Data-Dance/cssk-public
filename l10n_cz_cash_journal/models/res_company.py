# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: The Czech chart mapped onto the deník columns, as
#: ``(code prefixes, category for money OUT, category for money IN)``.
#:
#: Read off the official chart shipped by ``l10n_cz`` (``account.account-cz.csv``,
#: vyhláška č. 500/2002 Sb.). Same shape as the Slovak table, and deliberately
#: NOT a copy of it — see 526 below.
#:
#: **Deliberately not mapped**: 311 / 321 (the leg the engine arrives through),
#: 314 / 324 (advances, whose column depends on what the advance is for), and
#: the valuation accounts that never stand behind a movement of money.
CZ_CHART_MAP = [
    # --- příjmy ---------------------------------------------------------
    (("601", "602", "606", "607"), "cat_p_vyrobky", None),
    (("604",), "cat_p_zbozi", None),
    (("641", "642", "644", "645", "646", "648", "661", "663", "665", "666",
      "667", "668"), "cat_p_ostatni", None),
    (("662",), "cat_pn_ostatni", None),
    # --- daňové výdaje --------------------------------------------------
    (("501", "112"), "cat_v_material", None),
    (("504", "132"), "cat_v_zbozi", None),
    (("502", "503", "511", "512", "518"), "cat_v_rezie", None),
    (("521", "522", "523"), "cat_v_mzdy", None),
    (("524", "525"), "cat_v_odvody", None),
    # § 25 odst. 1 písm. g) — the owner's own insurance is NOT deductible in
    # the Czech Republic, where § 19 ods. 3 písm. i) allows it in Slovakia.
    # The two catalogues differ here on purpose and tests assert it.
    (("526",), "cat_vn_pojistne_podnikatele", None),
    (("527", "528", "531", "532", "538", "544", "548", "562", "563", "568",
      "569"), "cat_v_ostatni", None),
    # --- nedaňové výdaje ------------------------------------------------
    (("513", "543", "545", "549"), "cat_vn_ostatni", None),
    (("01", "02", "03", "04"), "cat_vn_majetek", None),
    (("591", "595"), "cat_vn_dan_z_prijmu", None),
    # --- nepeněžní ------------------------------------------------------
    (("551",), "cat_z_odpisy", None),
    # --- dva směry ------------------------------------------------------
    (("343",), "cat_vn_dph", "cat_pn_dph"),
    (("341",), "cat_vn_dan_z_prijmu", "cat_pn_ostatni"),
    (("231", "461", "479"), "cat_vn_uver", "cat_pn_uver"),
    (("491",), "cat_vn_osobni_spotreba", "cat_pn_vklad"),
    (("331",), "cat_v_mzdy", "cat_pn_ostatni"),
    (("336",), "cat_v_odvody", "cat_pn_ostatni"),
    # --- průběžné položky -----------------------------------------------
    (("261",), "cat_c_prubezne", None),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cssk_chart_category_map(self):
        """The Czech mapping, for a Czech company."""
        self.ensure_one()
        if self.country_id.code != "CZ":
            return super()._cssk_chart_category_map()
        return [
            (prefixes, "l10n_cz_cash_journal.%s" % out_ref,
             "l10n_cz_cash_journal.%s" % in_ref if in_ref else None)
            for prefixes, out_ref, in_ref in CZ_CHART_MAP
        ]
