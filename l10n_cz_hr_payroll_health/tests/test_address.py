# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..models.l10n_cz_health_common import health_employer_identification


@tagged("post_install", "-at_install")
class TestHealthEmployerAddress(TransactionCase):
    """The employer's address in PPPZ and HOZ, read the way every CZ/SK
    export reads it (l10n_cssk_core.split_street)."""

    def _address(self, street, street2=""):
        company = self.env["res.company"].create({
            "name": "CZ Address Co %s %s" % (street, street2),
            "street": street, "street2": street2,
            "city": "Praha", "zip": "110 00"})
        values = health_employer_identification(company)
        return (values["adresaPlatceUlice"],
                values["adresaPlatceCisloPopisneOrientacni"])

    def test_street2_is_not_the_house_number(self):
        # Street 2 used to win outright: a floor went out as the číslo.
        self.assertEqual(self._address("Vinohradská 1511/230", "3. patro"),
                         ("Vinohradská", "1511/230"))

    def test_street2_that_is_only_a_number_still_counts(self):
        self.assertEqual(self._address("Dlouhá", "5"), ("Dlouhá", "5"))

    def test_a_village_without_streets(self):
        # No street name: the obec stands in for ulice (required element).
        self.assertEqual(self._address("č. p. 45"), ("Praha", "45"))
        self.assertEqual(self._address("Dlouhá"), ("Dlouhá", "0"))
