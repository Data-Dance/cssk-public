# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_sk_intrastat.models.intrastat_product_declaration import (
    _SU_CODE_BY_XMLID,
)


@tagged("post_install", "-at_install")
class TestSkIntrastat(TransactionCase):

    def test_supplementary_units_file_the_eurostat_code(self):
        """OCA's unit NAME is not always the code: "items" is p/st."""
        decl = self.env["intrastat.product.declaration"]
        for xmlid, code in _SU_CODE_BY_XMLID.items():
            self.assertEqual(decl._sk_su_code(self.env.ref(xmlid)), code, xmlid)
        # the rest are named by their code already
        self.assertEqual(
            decl._sk_su_code(self.env.ref("intrastat_product.intrastat_unit_m2")), "m2")
        self.assertEqual(decl._sk_su_code(self.env["intrastat.unit"]), "")

    def test_every_mapped_unit_exists(self):
        """A renamed or dropped OCA xmlid would silently fall back to the name."""
        for xmlid in _SU_CODE_BY_XMLID:
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False), xmlid)
