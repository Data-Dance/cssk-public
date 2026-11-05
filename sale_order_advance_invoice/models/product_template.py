# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.translate import TranslationImporter, get_po_paths

ADVANCE_PRODUCT_XMLID = "sale_order_advance_invoice.product_advance_invoice"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _advance_load_name_translations(self, langs=None):
        """Name the advance product from this module's catalogues.

        The product is created lazily, after the module was installed, so the
        catalogue entry for its xmlid was never applied: it kept the English
        name in every language except, by accident, the language of whoever
        created it (a Slovak company showed "Advance" on its documents).

        ``langs`` defaults to every active language but English. The record is
        noupdate, so the import has to force the overwrite; callers only pass
        languages that still hold the English default.
        """
        self.ensure_one()
        if langs is None:
            langs = [code for code, _name in self.env["res.lang"].get_installed()
                     if code != "en_US"]
        if not langs:
            return
        importer = TranslationImporter(self.env.cr, verbose=False)
        for lang in langs:
            for path in get_po_paths("sale_order_advance_invoice", lang):
                importer.load_file(path, lang, xmlids=[ADVANCE_PRODUCT_XMLID])
        importer.save(overwrite=True, force_overwrite=True)
        self.invalidate_recordset(["name"])
