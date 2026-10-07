import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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

# What § 69 ods. 12 bounds the SCS code to. The statute names CHAPTERS (and for
# písm. g) three headings), not codes, so this is checked at chapter level: a
# list of codes would refuse a heading the Spoločný colný sadzobník adds until
# the next release. The schema cannot catch a wrong one either — KodScsType is
# \d{4} with no enumeration.
RC_GOODS_CHAPTERS = {"f": ("10", "12"), "g": ("72",)}
RC_GOODS_HEADINGS = {"g": ("7301", "7308", "7314")}


def kv_cn_code_in_scope(goods, code):
    """Does a 4-digit SCS code fall where § 69 ods. 12 písm. ``goods`` puts it?"""
    if goods not in RC_GOODS_WITH_CODE or not code:
        return True
    return (code[:2] in RC_GOODS_CHAPTERS.get(goods, ())
            or code in RC_GOODS_HEADINGS.get(goods, ()))


def kv_cn_code_scope_label(goods):
    """The statute's own bound, for messages: "kapitoly 10, 12" etc."""
    parts = ["kapitola %s" % c for c in RC_GOODS_CHAPTERS.get(goods, ())]
    parts += RC_GOODS_HEADINGS.get(goods, ())
    return ", ".join(parts)


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
        "in A.2 for § 69 ods. 12 písm. f) and g). The statute bounds it: "
        "písm. f) to chapters 10 and 12, písm. g) to chapter 72 and headings "
        "7301, 7308 and 7314. Leave empty to reuse the product's customs "
        "classification (HS / intrastat code) — that code is checked against "
        "the same chapters when the kontrolný výkaz is exported.",
    )

    @api.constrains("l10n_sk_kv_rc_goods", "l10n_sk_kv_cn_code")
    def _check_l10n_sk_kv_cn_code(self):
        for product in self:
            code = product.l10n_sk_kv_cn_code
            if not code:
                continue
            if not (len(code) == 4 and code.isdigit()):
                raise ValidationError(_(
                    "%(product)s: the KV DPH commodity code must be four "
                    "digits, not \"%(code)s\".",
                    product=product.display_name, code=code))
            goods = product.l10n_sk_kv_rc_goods
            if not kv_cn_code_in_scope(goods, code):
                raise ValidationError(_(
                    "%(product)s: commodity code %(code)s is outside § 69 "
                    "ods. 12 písm. %(goods)s) (%(scope)s).",
                    product=product.display_name, code=code, goods=goods,
                    scope=kv_cn_code_scope_label(goods)))


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
