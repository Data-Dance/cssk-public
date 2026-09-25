"""Which UBL builder a Peppol document is exported with.

Regression cover for a bug that was invisible statically and shipped a
subtly wrong invoice: ``_peppol_builder`` fell back with
``partner._get_edi_builder(fmt) or ubl_bis3``, but a builder is an
``AbstractModel`` whose recordset is **falsy**, so every national BIS3
subclass was silently discarded in favour of the generic one. For Slovakia
that dropped the *variabilný symbol* from ``cbc:PaymentID`` (BT-83) on every
invoice put on the network.
"""

from odoo.tests.common import TransactionCase


class TestPeppolBuilder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.env["account.journal"].search(
            [
                *cls.env["account.journal"]._check_company_domain(cls.env.company),
                ("type", "=", "sale"),
            ],
            limit=1,
        )

    def _move(self, partner):
        if not self.journal:
            self.skipTest("no sale journal in this company (no chart of accounts)")
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal.id,
            }
        )

    def test_a_falsy_abstract_builder_is_still_used(self):
        """The heart of the bug: an AbstractModel recordset is falsy.

        'nlcius' is a core Peppol format whose builder (``account.edi.xml.
        ubl_nl``) is an AbstractModel, so it reproduces the trap without
        needing a national module installed. If the resolution ever goes back
        to ``or``-style fallback, this returns ``ubl_bis3`` and fails.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Peppol Builder Test",
                "country_id": self.env.ref("base.nl").id,
                "peppol_eas": "0106",
                "peppol_endpoint": "12345678",
                "invoice_edi_format": "nlcius",
            }
        )
        builder = partner._get_edi_builder("nlcius")
        # Guard the premise — if core ever makes builders truthy, this test
        # stops proving anything and should be revisited.
        self.assertFalse(
            bool(builder),
            "premise broken: builder recordsets are no longer falsy",
        )
        self.assertEqual(
            self._move(partner)._peppol_builder()._name, builder._name
        )

    def test_unknown_format_falls_back_to_generic_bis3(self):
        """A partner with no usable Peppol format still exports as BIS3."""
        partner = self.env["res.partner"].create(
            {
                "name": "No Format Test",
                "country_id": self.env.ref("base.sk").id,
                "peppol_eas": "0245",
                "peppol_endpoint": "9999999999",
            }
        )
        builder = self._move(partner)._peppol_builder()
        self.assertTrue(builder._name.startswith("account.edi.xml.ubl"))

    def test_non_peppol_format_is_not_sent_over_peppol(self):
        """A partner set to Factur-X must not have that document handed to a
        Peppol transport — the format is constrained to on_peppol ones."""
        partner = self.env["res.partner"].create(
            {
                "name": "Facturx Test",
                "country_id": self.env.ref("base.fr").id,
                "peppol_eas": "0009",
                "peppol_endpoint": "73282932000074",  # core's own example: passes the SIRET checksum
                "invoice_edi_format": "facturx",
            }
        )
        builder = self._move(partner)._peppol_builder()
        self.assertNotEqual(builder._name, "account.edi.xml.cii")
        self.assertIn(
            "ubl", builder._name, "a Peppol transport must carry a UBL document"
        )
