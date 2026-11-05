# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Name the existing advance product in the installed languages.

It was created lazily with the English name, so in most languages it still says
"Advance" on documents. Only a language whose name is still the English one is
renamed; a name somebody changed by hand is kept.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    product = env.ref(
        "sale_order_advance_invoice.product_advance_invoice", raise_if_not_found=False)
    if not product:
        return
    cr.execute("SELECT name FROM product_template WHERE id = %s", [product.id])
    names = cr.fetchone()[0] or {}
    english = names.get("en_US")
    langs = [
        code for code, _name in env["res.lang"].get_installed()
        if code != "en_US" and names.get(code, english) == english
    ]
    product._advance_load_name_translations(langs)
