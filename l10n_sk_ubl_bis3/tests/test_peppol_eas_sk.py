# -*- coding: utf-8 -*-
"""The Slovak Peppol participant identifier is 0245 + DIČ, not 9950 + IČ DPH."""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSlovakPeppolEas(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk = cls.env.ref('base.sk')

    def _partner(self, **vals):
        return self.env['res.partner'].create(
            {'name': "SK Subjekt s.r.o.", 'country_id': self.sk.id, **vals})

    def test_the_default_scheme_is_0245_not_9950(self):
        """Core lists 9950 first for SK, so a VAT payer was identified by its
        IČ DPH. An access point rejects that as an unknown participant."""
        partner = self._partner(vat="SK2020317068", l10n_sk_dic="2020317068")
        self.assertEqual(partner.peppol_eas, '0245')
        self.assertEqual(partner.peppol_endpoint, "2020317068")

    def test_the_endpoint_is_the_dic_not_the_ico(self):
        """Core mapped 0245 to company_registry — the 8-digit IČO — under a
        code whose own label says DIČ."""
        partner = self._partner(
            company_registry="31333532", l10n_sk_dic="2020317068")
        self.assertEqual(partner.peppol_eas, '0245')
        self.assertEqual(partner.peppol_endpoint, "2020317068")
        self.assertNotEqual(partner.peppol_endpoint, "31333532")

    def test_a_non_vat_payer_still_gets_an_endpoint(self):
        """Registered for income tax, not for VAT: no IČ DPH exists, and the
        DIČ field is the only source. This is the case the field exists for."""
        partner = self._partner(l10n_sk_dic="2020317068")
        self.assertFalse(partner.vat)
        self.assertEqual(partner.peppol_eas, '0245')
        self.assertEqual(partner.peppol_endpoint, "2020317068")

    def test_the_dic_is_never_derived_from_the_vat_number(self):
        """The inverse of what this module first did.

        Deriving the DIČ as the VAT number minus its SK prefix assumed the two
        always agree. The ePošťák sandbox firms disprove it — a synthetic IČ DPH
        stands in for a DIČ that fails base_vat's checksum, so deriving gives
        4536197523 where the participant is 4536197514 — and whether real
        subjects diverge (VAT groups, § 5 registrations) is an open question.
        A wrong participant identifier is worse than none, so there is no
        fallback: no stored DIČ, no 0245 endpoint.
        """
        partner = self._partner(vat="SK2020317068")
        self.assertFalse(partner.l10n_sk_dic)
        self.assertEqual(partner._l10n_sk_get_dic(), "")
        self.assertNotEqual(
            partner.peppol_endpoint, "2020317068",
            "the DIČ must not be invented from the VAT number")

    def test_the_sandbox_case_that_withdrew_the_derivation(self):
        """The concrete number that made this a defect rather than a theory:
        a synthetic IČ DPH whose digits are not the firm's DIČ."""
        partner = self._partner(l10n_sk_dic="4536197514")
        partner.with_context(no_vat_validation=True).vat = "SK4536197523"
        self.assertEqual(partner.peppol_eas, '0245')
        self.assertEqual(
            partner.peppol_endpoint, "4536197514",
            "the recorded DIČ wins; the VAT digits are not the DIČ")

    def test_the_endpoint_follows_the_dic(self):
        """_peppol_eas_endpoint_depends must name l10n_sk_dic, or correcting a
        DIČ leaves a stale participant id behind."""
        partner = self._partner(l10n_sk_dic="2020317068")
        partner.l10n_sk_dic = "1111111111"
        self.assertEqual(partner.peppol_endpoint, "1111111111")

    def test_an_explicit_scheme_is_not_overridden(self):
        """Reordering the mapping changes the DEFAULT. A partner deliberately
        published under 9950 must stay there."""
        partner = self._partner(vat="SK2020317068", l10n_sk_dic="2020317068")
        partner.peppol_eas = '9950'
        partner.l10n_sk_dic = "1111111111"
        self.assertEqual(partner.peppol_eas, '9950')

    def test_the_core_mapping_is_left_alone(self):
        """EAS_MAPPING is a module-global, imported once per PROCESS. Editing
        it would reach every database the worker serves, including ones without
        this module — whose registries carry none of these overrides. The fix
        is registry-scoped, so the shared dict must be untouched, and 9950 must
        still map to 'vat' for the import side that scans for that entry to
        recover a supplier's VAT from an inbound PartyIdentification."""
        from odoo.addons.account_edi_ubl_cii.models.account_edi_common import (
            EAS_MAPPING,
        )
        self.assertEqual(EAS_MAPPING['SK'], {'9950': 'vat', '0245': 'company_registry'})

    def test_a_malformed_vat_derives_nothing(self):
        """'SK123' must not become the participant id '123'. A wrong
        identifier registers the company as somebody who is not them.

        ``no_vat_validation`` because base_vat refuses to store a malformed VAT
        (base_vat/models/res_partner.py:146), and the case worth covering is
        precisely a database that already holds one -- imported, or entered
        before the constraint existed.
        """
        partner = self.env['res.partner'].with_context(
            no_vat_validation=True,
        ).create({
            'name': "Zlý VAT s.r.o.", 'country_id': self.sk.id, 'vat': "SK123",
        })
        self.assertEqual(partner.vat, "SK123")
        self.assertEqual(partner._l10n_sk_get_dic(), "")
        self.assertNotEqual(partner.peppol_endpoint, "123")

    def test_the_scheme_does_not_flip_without_a_number(self):
        """_compute_peppol_endpoint keeps the previous endpoint when the new
        one is empty, so flipping to 0245 with no DIČ would leave an IČ DPH
        sitting there labelled as a DIČ."""
        partner = self._partner(company_registry="31333532")
        self.assertFalse(partner._l10n_sk_get_dic())
        self.assertNotEqual(partner.peppol_endpoint, "31333532")

    def test_the_sk_builder_outranks_the_generic_one(self):
        """Once SK joins PEPPOL_DEFAULT_COUNTRIES (PR #275798) both formats
        offer SK, and min() by sequence decides. Equal sequences would fall
        back to dict order and drop the VS -> BT-83 mapping."""
        info = self.env['res.partner']._get_ubl_cii_formats_info()
        self.assertLess(
            info['ubl_bis3_sk']['sequence'], info['ubl_bis3']['sequence'])

    def test_export_refuses_a_slovak_party_without_a_dic(self):
        """With no derivation, a missing DIČ must fail at export with a message
        naming the partner -- not at the access point, where an unknown
        participant reads as a malformed request."""
        partner = self._partner(l10n_sk_dic="2020317068")
        self.assertEqual(partner.peppol_eas, '0245')
        partner.l10n_sk_dic = False
        builder = self.env['account.edi.xml.ubl_sk']
        invoice = self.env['account.move'].new({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'company_id': self.env.company.id,
        })
        constraints = builder._l10n_sk_peppol_constraints(invoice, {})
        self.assertIn('l10n_sk_ubl_bis3_customer_dic_required', constraints)
        self.assertIn(
            "DIČ", constraints['l10n_sk_ubl_bis3_customer_dic_required'])
