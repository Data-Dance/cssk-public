# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The DIČ backfill writes one field and leaves everything else alone."""

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

PROVIDER = "odoo.addons.partner_autocomplete_orsf_sk.models" \
           ".partner_autocomplete_provider.PartnerAutocompleteProviderOrsfSk"


@tagged("post_install", "-at_install")
class TestOrsfDicBackfill(TransactionCase):

    def setUp(self):
        super().setUp()
        if "l10n_sk_dic" not in self.env["res.partner"]._fields:
            self.skipTest("l10n_sk_base not installed")
        self.sk = self.env.ref("base.sk")

    def _partner(self, **vals):
        return self.env["res.partner"].create(
            {"name": "Test s.r.o.", "country_id": self.sk.id, **vals})

    def test_it_fills_an_empty_dic_and_touches_nothing_else(self):
        partner = self._partner(
            name="Pôvodný názov s.r.o.", company_registry="00681300",
            street="Stará 1")
        record = {
            "ico": "00681300", "dic": "2020318256", "icDph": "SK2020318256",
            "name": "Odvoz a likvidácia odpadu a.s.", "status": "aktívna",
            "address": {"street": "Ivanská cesta 22", "city": "Bratislava"},
        }
        with patch(f"{PROVIDER}._orsf_lookup_batch",
                   return_value={"00681300": record}):
            partner.action_orsf_fill_missing_dic()
        self.assertEqual(partner.l10n_sk_dic, "2020318256")
        # the point of the separate action: identity is NOT rewritten
        self.assertEqual(partner.name, "Pôvodný názov s.r.o.")
        self.assertEqual(partner.street, "Stará 1")
        self.assertFalse(partner.vat)

    def test_a_hand_entered_dic_is_never_overruled(self):
        partner = self._partner(
            company_registry="00681300", l10n_sk_dic="9999999999")
        with patch(f"{PROVIDER}._orsf_lookup_batch") as batch:
            partner.action_orsf_fill_missing_dic()
            batch.assert_not_called()  # nothing to ask about
        self.assertEqual(partner.l10n_sk_dic, "9999999999")

    def test_the_not_found_shape_is_not_mistaken_for_a_record(self):
        """{"ico": ..., "found": false} is how absence is reported. Reading it
        as a record is what produced a wrong commit (b85340c)."""
        partner = self._partner(company_registry="36197514")
        with patch(f"{PROVIDER}._orsf_lookup_batch",
                   return_value={"36197514": {"ico": "36197514",
                                              "found": False}}):
            partner.action_orsf_fill_missing_dic()
        self.assertFalse(partner.l10n_sk_dic)

    def test_a_partner_with_no_ico_is_skipped_not_crashed(self):
        partner = self._partner(company_registry=False)
        with patch(f"{PROVIDER}._orsf_lookup_batch") as batch:
            partner.action_orsf_fill_missing_dic()
            batch.assert_not_called()
        self.assertFalse(partner.l10n_sk_dic)

    def test_two_partners_sharing_an_ico_both_get_it(self):
        a = self._partner(name="A s.r.o.", company_registry="00681300")
        b = self._partner(name="A s.r.o. (duplikát)",
                          company_registry="00681300")
        with patch(f"{PROVIDER}._orsf_lookup_batch",
                   return_value={"00681300": {"ico": "00681300",
                                              "name": "A s.r.o.",
                                              "dic": "2020318256"}}):
            (a | b).action_orsf_fill_missing_dic()
        self.assertEqual(a.l10n_sk_dic, "2020318256")
        self.assertEqual(b.l10n_sk_dic, "2020318256")
