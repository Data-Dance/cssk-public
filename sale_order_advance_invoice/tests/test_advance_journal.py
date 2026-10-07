"""The advance journal is adopted, never inserted twice."""

from odoo.tests import TransactionCase, tagged

XMLID = "sale_order_advance_invoice.advance_invoice_journal"


@tagged("post_install", "-at_install")
class TestAdvanceJournal(TransactionCase):

    def _tdadv(self, company):
        return self.env["account.journal"].search(
            [("company_id", "=", company.id), ("code", "=", "TDADV")])

    def _drop_xmlid(self):
        self.env["ir.model.data"].search([
            ("module", "=", "sale_order_advance_invoice"),
            ("name", "=", "advance_invoice_journal")]).unlink()

    def test_a_journal_without_the_xmlid_is_adopted(self):
        """A customer database: TDADV exists (a localization helper made it), no xmlid."""
        company = self.env.company
        journal = self._tdadv(company) or self.env["account.journal"].create({
            "name": "Daňové doklady", "code": "TDADV", "type": "general",
            "company_id": company.id})
        self._drop_xmlid()
        self.env["res.company"]._advance_invoice_journal_ensure_xmlid()
        self.assertEqual(self._tdadv(company), journal, "no second TDADV journal")
        self.assertEqual(self.env.ref(XMLID), journal)

    def test_a_live_xmlid_is_left_alone(self):
        before = self.env.ref(XMLID)
        self.env["res.company"]._advance_invoice_journal_ensure_xmlid()
        self.assertEqual(self.env.ref(XMLID), before)

    def test_a_company_without_one_gets_it(self):
        company = self.env["res.company"].create({"name": "Nová s.r.o."})
        self._drop_xmlid()
        self.env["res.company"].with_company(company)._advance_invoice_journal_ensure_xmlid()
        journal = self._tdadv(company)
        self.assertEqual(len(journal), 1)
        self.assertEqual(self.env.ref(XMLID), journal)
