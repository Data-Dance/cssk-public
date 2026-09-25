import re

from odoo import fields, models

# § 69 ods. 12 zákona o DPH — the domestic reverse-charge goods for which
# oddiel A.2 carries more than the base. Read off the vzor's own schema
# (KodScsType, DruhTovaruType): písm. f) and g) are identified by the 4-digit
# code of the Spoločný colný sadzobník, písm. h) and i) by a druh (MT / IO);
# all four state a quantity in kg, t, m or ks.
RC_GOODS = [
    ("f", "§ 69 ods. 12 písm. f) — obilniny a technické plodiny"),
    ("g", "§ 69 ods. 12 písm. g) — kovy"),
    ("h", "§ 69 ods. 12 písm. h) — mobilné telefóny"),
    ("i", "§ 69 ods. 12 písm. i) — integrované obvody"),
]
RC_GOODS_WITH_CODE = ("f", "g")
RC_GOODS_KIND = {"h": "MT", "i": "IO"}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_sk_kv_rc_goods = fields.Selection(
        RC_GOODS,
        string="Tovar podľa § 69 ods. 12 (KV DPH A.2)",
        help="Set on goods whose domestic supply is reverse-charged under "
        "§ 69 ods. 12 písm. f) to i). Oddiel A.2 of the kontrolný výkaz then "
        "reports, per invoice, the commodity code (f, g) or the kind of goods "
        "(h, i), and the quantity with its unit. Leave empty for everything "
        "else, including the other § 69 ods. 12 supplies (scrap, construction "
        "work), for which A.2 carries only the base.",
    )
    l10n_sk_kv_cn_code = fields.Char(
        string="Číselný kód tovaru (KV DPH)",
        size=4,
        help="First four digits of the Spoločný colný sadzobník code, reported "
        "in A.2 for § 69 ods. 12 písm. f) and g). Leave empty to take it from "
        "the product's intrastat / HS code when one is installed.",
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _l10n_sk_kv_cn_code(self):
        """The 4-digit SCS code A.2 files, or ``""``.

        The explicit field wins. Otherwise whichever customs code this
        database carries — the OCA ``product_harmonized_system`` code
        (recursive through the category), Enterprise ``account_intrastat``, or
        the CE ``hs_code`` of ``stock_delivery`` — because a company filing
        Intrastat has already recorded it once and should not have to twice.
        """
        self.ensure_one()
        code = self.l10n_sk_kv_cn_code
        if not code and hasattr(self, "get_hs_code_recursively"):
            code = self.get_hs_code_recursively().local_code
        if not code and "intrastat_code_id" in self._fields:
            code = self.intrastat_code_id.code
        if not code and "hs_code" in self._fields:
            code = self.hs_code
        digits = re.sub(r"\D", "", code or "")
        return digits[:4] if len(digits) >= 4 else ""
